// SPDX-License-Identifier: GPL-2.0
/*
 * AY Shadow V6 Alpha 4 — Eng. Ahmed Yasir / RMX2170.
 * Opt-in, screen-driven policy cap. No thermal/FP/wakelock bypass.
 */
#include <linux/module.h>
#include <linux/init.h>
#include <linux/atomic.h>
#include <linux/cpu.h>
#include <linux/cpufreq.h>
#include <linux/fb.h>
#include <linux/jiffies.h>
#include <linux/kernel.h>
#include <linux/kobject.h>
#include <linux/mutex.h>
#include <linux/notifier.h>
#include <linux/power_supply.h>
#include <linux/sysfs.h>
#include <linux/suspend.h>
#include <linux/timekeeping.h>
#include <linux/workqueue.h>

#define AY_DEFAULT_DELAY 600U
#define AY_DEFAULT_CAP 0U /* Ultra: hardware minimum unless an existing policy floor is higher */
#define AY_WAKE_MS 250U
#define AY_WAKE_FLOOR 20U
#define AY_GAME_FLOOR 25U
#define AY_BATTERY_LIMIT_DECI_C 400
#define AY_BATTERY_SAMPLE_MS 5000U

static struct kobject *ay_kobj;
static DEFINE_MUTEX(ay_control_lock);
static struct delayed_work ay_doze_work;
static struct delayed_work ay_wake_work;
static struct delayed_work ay_thermal_work;
static struct work_struct ay_policy_work;
static atomic_t ay_deep = ATOMIC_INIT(0);
static atomic_t ay_fb_events = ATOMIC_INIT(0);
static atomic_t ay_wake_events = ATOMIC_INIT(0);
static atomic_t ay_wake_active = ATOMIC_INIT(0);
static atomic_t ay_thermal_safe = ATOMIC_INIT(0);
static atomic_t ay_battery_temp = ATOMIC_INIT(-1);
static atomic_t ay_game_samples = ATOMIC_INIT(0);
static atomic_t ay_deep_entries = ATOMIC_INIT(0);
static atomic_t ay_game_denials = ATOMIC_INIT(0);
static atomic_t ay_restore_pending = ATOMIC_INIT(0);
static atomic_t ay_restore_ms = ATOMIC_INIT(-1);
/* Explicit future Android-exception hook: calls, music, navigation. */
static unsigned long ay_wake_started;
static unsigned long ay_last_sample;
static bool ay_wake_enabled; /* user opt-in, off until hardware validation */
static bool ay_game_enabled; /* user opt-in, off until hardware validation */
static unsigned int ay_wake_ms = AY_WAKE_MS;
static unsigned int ay_game_floor = AY_GAME_FLOOR;
static bool ay_enabled; /* deliberately OFF by default until hardware validation */
static bool ay_screen_on = true;
static unsigned int ay_delay = AY_DEFAULT_DELAY;
static unsigned int ay_cap = AY_DEFAULT_CAP;
static u64 ay_screen_off_boottime_ms;
static atomic_t ay_post_suspend_count = ATOMIC_INIT(0);
static atomic_t ay_cap_applied = ATOMIC_INIT(0);

/* BOOTTIME includes elapsed suspend. jiffies do not. */
static u64 ay_now_ms(void)
{
	return (u64)ktime_to_ms(ktime_get_boottime());
}
static unsigned int ay_remaining_ms(void)
{
	u64 now = ay_now_ms();
	u64 since = READ_ONCE(ay_screen_off_boottime_ms);
	u64 elapsed = now >= since ? now - since : 0;
	u64 target = (u64)READ_ONCE(ay_delay) * 1000ULL;

	return elapsed >= target ? 0U : (unsigned int)(target - elapsed);
}
static void ay_schedule_doze(void)
{
	if (!READ_ONCE(ay_enabled) || READ_ONCE(ay_screen_on))
		return;
	mod_delayed_work(system_freezable_wq, &ay_doze_work,
			 msecs_to_jiffies(ay_remaining_ms()));
}
/* A suspend that overlaps the deadline cannot postpone UltraDoze indefinitely. */
static int ay_pm_event(struct notifier_block *nb,
		       unsigned long event, void *data)
{
	if (event == PM_POST_SUSPEND) {
		atomic_inc(&ay_post_suspend_count);
		ay_schedule_doze();
	}
	return NOTIFY_OK;
}
static struct notifier_block ay_pm_nb = { .notifier_call = ay_pm_event };

/*
 * Priority: screen-off Doze ceiling, then optional short wake boost, then
 * temperature-gated game floor. The existing policy max and all hardware/thermal
 * restrictions remain authoritative; never force driver clocks directly.
 */
static int ay_cpufreq_adjust(struct notifier_block *nb,
			     unsigned long event, void *data)
{
	struct cpufreq_policy *policy = data;
	unsigned int min, max, limit, floor;

	if (event != CPUFREQ_ADJUST || !policy)
		return NOTIFY_OK;

	min = policy->cpuinfo.min_freq;
	max = policy->cpuinfo.max_freq;
	if (max <= min)
		return NOTIFY_OK;

	if (READ_ONCE(ay_enabled) && atomic_read(&ay_deep)) {
		limit = min + (unsigned int)(((u64)(max - min) *
					  READ_ONCE(ay_cap)) / 100U);
		if (limit < policy->min)
			limit = policy->min;
		if (limit < policy->max) {
			cpufreq_verify_within_limits(policy, policy->min, limit);
			atomic_inc(&ay_cap_applied);
		}
		return NOTIFY_OK;
	}

	if (!READ_ONCE(ay_screen_on))
		return NOTIFY_OK;

	floor = 0;
	if (READ_ONCE(ay_wake_enabled) && atomic_read(&ay_wake_active))
		floor = min + (unsigned int)(((u64)(max - min) *
					   AY_WAKE_FLOOR) / 100U);
	if (READ_ONCE(ay_game_enabled) && atomic_read(&ay_thermal_safe) &&
	    time_before(jiffies, READ_ONCE(ay_last_sample) +
			msecs_to_jiffies(2 * AY_BATTERY_SAMPLE_MS))) {
		limit = min + (unsigned int)(((u64)(max - min) *
					 READ_ONCE(ay_game_floor)) / 100U);
		if (limit > floor)
			floor = limit;
	}

	/* A governor, thermal or voltage policy can impose a lower maximum. */
	if (floor && floor > policy->min) {
		if (floor > policy->max)
			floor = policy->max;
		cpufreq_verify_within_limits(policy, floor, policy->max);
	}
	return NOTIFY_OK;
}

static struct notifier_block ay_cpufreq_nb = {
	.notifier_call = ay_cpufreq_adjust,
};

static void ay_refresh_policies(struct work_struct *work)
{
	unsigned int cpu;
	struct cpufreq_policy *policy;
	for_each_online_cpu(cpu) {
		policy = cpufreq_cpu_get(cpu);
		if (!policy)
			continue;
		if (policy->cpu == cpu) {
			cpufreq_cpu_put(policy);
			cpufreq_update_policy(cpu);
		} else {
			cpufreq_cpu_put(policy);
		}
	}
	/* Policy refresh duration, NOT full unlock or display-on latency. */
	if (READ_ONCE(ay_screen_on) &&
	    atomic_xchg(&ay_restore_pending, 0))
		atomic_set(&ay_restore_ms, jiffies_to_msecs(jiffies -
				READ_ONCE(ay_wake_started)));
}
static void ay_end_wakeboost(struct work_struct *work)
{
	atomic_set(&ay_wake_active, 0);
	schedule_work(&ay_policy_work);
}

/*
 * Read battery temperature OUTSIDE the cpufreq policy notifier. Fail closed:
 * if battery driver/temperature is unavailable, the game floor is disabled.
 * 400 = 40.0 C, battery temperatures are expressed in tenths of degree C.
 */
static void ay_thermal_sample(struct work_struct *work)
{
	struct power_supply *battery;
	union power_supply_propval prop;
	int ret = -ENODEV, temperature = -1;

	if (!READ_ONCE(ay_game_enabled) || !READ_ONCE(ay_screen_on)) {
		atomic_set(&ay_thermal_safe, 0);
		schedule_work(&ay_policy_work);
		return;
	}
	battery = power_supply_get_by_name("battery");
	if (battery) {
		ret = power_supply_get_property(battery, POWER_SUPPLY_PROP_TEMP,
						&prop);
		if (!ret)
			temperature = prop.intval;
		power_supply_put(battery);
	}
	atomic_set(&ay_battery_temp, temperature);
	atomic_set(&ay_thermal_safe, !ret && temperature >= 0 &&
			temperature < AY_BATTERY_LIMIT_DECI_C &&
			READ_ONCE(ay_game_enabled) && READ_ONCE(ay_screen_on));
	if (ret || temperature < 0 ||
	    temperature >= AY_BATTERY_LIMIT_DECI_C)
		atomic_inc(&ay_game_denials);
	WRITE_ONCE(ay_last_sample, jiffies);
	atomic_inc(&ay_game_samples);
	schedule_work(&ay_policy_work);
	if (READ_ONCE(ay_game_enabled) && READ_ONCE(ay_screen_on))
		mod_delayed_work(system_freezable_wq, &ay_thermal_work,
				 msecs_to_jiffies(AY_BATTERY_SAMPLE_MS));
}

static void ay_enter_deepdoze(struct work_struct *work)
{
	if (!READ_ONCE(ay_enabled) || READ_ONCE(ay_screen_on))
		return;
	/* Suspended time counts. Do NOT wake the phone just to set this cap. */
	if (ay_remaining_ms()) {
		ay_schedule_doze();
		return;
	}
	atomic_set(&ay_deep, 1);
	atomic_inc(&ay_deep_entries);
	schedule_work(&ay_policy_work);
}
static void ay_set_screen(bool screen_on)
{
	if (READ_ONCE(ay_screen_on) == screen_on)
		return;
	WRITE_ONCE(ay_screen_on, screen_on);
	if (screen_on) {
		/* Clear cap on EARLY UNBLANK, before policy worker runs. */
		atomic_inc(&ay_wake_events);
		WRITE_ONCE(ay_wake_started, jiffies);
		atomic_set(&ay_restore_pending, 1);
		atomic_set(&ay_deep, 0);
		cancel_delayed_work(&ay_doze_work);
		if (READ_ONCE(ay_wake_enabled)) {
			atomic_set(&ay_wake_active, 1);
			mod_delayed_work(system_wq, &ay_wake_work,
				msecs_to_jiffies(READ_ONCE(ay_wake_ms)));
		}
		if (READ_ONCE(ay_game_enabled))
			mod_delayed_work(system_freezable_wq, &ay_thermal_work, 0);
		schedule_work(&ay_policy_work);
	} else {
		atomic_set(&ay_wake_active, 0);
		atomic_set(&ay_thermal_safe, 0);
		cancel_delayed_work(&ay_wake_work);
		cancel_delayed_work(&ay_thermal_work);
		schedule_work(&ay_policy_work);
		WRITE_ONCE(ay_screen_off_boottime_ms, ay_now_ms());
		ay_schedule_doze();
	}
}
static int ay_fb_event(struct notifier_block *nb,
			unsigned long event, void *data)
{
	struct fb_event *notification = data;
	int blank;
	if (event != FB_EARLY_EVENT_BLANK && event != FB_EVENT_BLANK)
		return NOTIFY_DONE;
	if (!notification || !notification->data)
		return NOTIFY_DONE;
	blank = *(int *)notification->data;
	if (blank == FB_BLANK_UNBLANK) {
		atomic_inc(&ay_fb_events);
		ay_set_screen(true);
	} else if (blank == FB_BLANK_POWERDOWN) {
		atomic_inc(&ay_fb_events);
		ay_set_screen(false);
	}
	return NOTIFY_OK;
}
static struct notifier_block ay_fb_nb = {.notifier_call = ay_fb_event};

static ssize_t enabled_show(struct kobject *kobj,
				struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n", READ_ONCE(ay_enabled) ? 1 : 0);
}
static ssize_t enabled_store(struct kobject *kobj, struct kobj_attribute *attr,
			      const char *buf, size_t count)
{
	bool new_value;
	int ret = kstrtobool(buf, &new_value);
	if (ret)
		return ret;
	mutex_lock(&ay_control_lock);
	WRITE_ONCE(ay_enabled, new_value);
	if (!new_value) {
		atomic_set(&ay_deep, 0);
		cancel_delayed_work_sync(&ay_doze_work);
		schedule_work(&ay_policy_work);
	} else {
		ay_schedule_doze();
	}
	mutex_unlock(&ay_control_lock);
	return count;
}
static struct kobj_attribute enabled_attr =
	__ATTR(enabled, 0600, enabled_show, enabled_store);

static ssize_t delay_seconds_show(struct kobject *kobj,
				   struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n", READ_ONCE(ay_delay));
}
static ssize_t delay_seconds_store(struct kobject *kobj,
				    struct kobj_attribute *attr,
				    const char *buf, size_t count)
{
	unsigned int value;
	int ret = kstrtouint(buf, 10, &value);
	if (ret)
		return ret;
	if (value < 300 || value > 1800)
		return -ERANGE;
	mutex_lock(&ay_control_lock);
	WRITE_ONCE(ay_delay, value);
	if (READ_ONCE(ay_enabled) && !READ_ONCE(ay_screen_on) &&
	    !atomic_read(&ay_deep))
		ay_schedule_doze();
	mutex_unlock(&ay_control_lock);
	return count;
}
static struct kobj_attribute delay_seconds_attr =
	__ATTR(delay_seconds, 0600, delay_seconds_show, delay_seconds_store);

static ssize_t cap_percent_show(struct kobject *kobj,
				 struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n", READ_ONCE(ay_cap));
}
static ssize_t cap_percent_store(struct kobject *kobj,
				  struct kobj_attribute *attr,
				  const char *buf, size_t count)
{
	unsigned int value;
	int ret = kstrtouint(buf, 10, &value);
	if (ret)
		return ret;
	if (value > 95)
		return -ERANGE;
	WRITE_ONCE(ay_cap, value);
	if (atomic_read(&ay_deep))
		schedule_work(&ay_policy_work);
	return count;
}
static struct kobj_attribute cap_percent_attr =
	__ATTR(cap_percent, 0600, cap_percent_show, cap_percent_store);

static ssize_t state_show(struct kobject *kobj,
			   struct kobj_attribute *attr, char *buf)
{
	const char *state;
	if (!READ_ONCE(ay_enabled))
		state = "disabled";
	else if (READ_ONCE(ay_screen_on))
		state = "performance";
	else if (atomic_read(&ay_deep))
		state = "ultra_deepdoze";
	else
		state = "light_idle";
	return scnprintf(buf, PAGE_SIZE, "%s\n", state);
}
/* Opt-in instant-wake floor; does not change the GPU, thermal limits or ROM. */
static ssize_t wakeboost_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n",
			READ_ONCE(ay_wake_enabled) ? 1 : 0);
}
static ssize_t wakeboost_store(struct kobject *kobj,
		struct kobj_attribute *attr, const char *buf, size_t count)
{
	bool on;
	int ret = kstrtobool(buf, &on);
	if (ret)
		return ret;
	WRITE_ONCE(ay_wake_enabled, on);
	if (!on) {
		atomic_set(&ay_wake_active, 0);
		cancel_delayed_work(&ay_wake_work);
		schedule_work(&ay_policy_work);
	}
	return count;
}
static struct kobj_attribute wakeboost_attr =
	__ATTR(wakeboost, 0600, wakeboost_show, wakeboost_store);

static ssize_t wakeboost_ms_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n", READ_ONCE(ay_wake_ms));
}
static ssize_t wakeboost_ms_store(struct kobject *kobj,
		struct kobj_attribute *attr, const char *buf, size_t count)
{
	unsigned int value;
	int ret = kstrtouint(buf, 10, &value);
	if (ret)
		return ret;
	if (value < 100 || value > 500)
		return -ERANGE;
	WRITE_ONCE(ay_wake_ms, value);
	return count;
}
static struct kobj_attribute wakeboost_ms_attr =
	__ATTR(wakeboost_ms, 0600, wakeboost_ms_show, wakeboost_ms_store);

/* Temperature-gated, optional CPU GameBoost; 0 means V5 behavior. */
static ssize_t game_mode_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n",
			READ_ONCE(ay_game_enabled) ? 1 : 0);
}
static ssize_t game_mode_store(struct kobject *kobj,
		struct kobj_attribute *attr, const char *buf, size_t count)
{
	bool on;
	int ret = kstrtobool(buf, &on);
	if (ret)
		return ret;
	WRITE_ONCE(ay_game_enabled, on);
	atomic_set(&ay_thermal_safe, 0);
	cancel_delayed_work(&ay_thermal_work);
	if (on && READ_ONCE(ay_screen_on))
		mod_delayed_work(system_freezable_wq, &ay_thermal_work, 0);
	schedule_work(&ay_policy_work);
	return count;
}
static struct kobj_attribute game_mode_attr =
	__ATTR(game_mode, 0600, game_mode_show, game_mode_store);

static ssize_t game_floor_percent_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n", READ_ONCE(ay_game_floor));
}
static ssize_t game_floor_percent_store(struct kobject *kobj,
		struct kobj_attribute *attr, const char *buf, size_t count)
{
	unsigned int value;
	int ret = kstrtouint(buf, 10, &value);
	if (ret)
		return ret;
	if (value < 10 || value > 35)
		return -ERANGE;
	WRITE_ONCE(ay_game_floor, value);
	schedule_work(&ay_policy_work);
	return count;
}
static struct kobj_attribute game_floor_percent_attr =
	__ATTR(game_floor_percent, 0600, game_floor_percent_show,
			game_floor_percent_store);

static ssize_t battery_temp_decic_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%d\n",
			 atomic_read(&ay_battery_temp));
}
static struct kobj_attribute battery_temp_decic_attr =
	__ATTR_RO(battery_temp_decic);

static ssize_t thermal_guard_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%u\n",
			 atomic_read(&ay_thermal_safe) ? 1 : 0);
}
static struct kobj_attribute thermal_guard_attr = __ATTR_RO(thermal_guard);

/* Read-only performance counters: instrumentation is deliberately passive. */
static ssize_t restore_ms_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%d\n", atomic_read(&ay_restore_ms));
}
static struct kobj_attribute restore_ms_attr = __ATTR_RO(restore_ms);

static ssize_t deep_entries_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%d\n", atomic_read(&ay_deep_entries));
}
static struct kobj_attribute deep_entries_attr = __ATTR_RO(deep_entries);

static ssize_t game_denials_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%d\n", atomic_read(&ay_game_denials));
}
static struct kobj_attribute game_denials_attr = __ATTR_RO(game_denials);

static struct kobj_attribute state_attr = __ATTR_RO(state);
static ssize_t telemetry_show(struct kobject *kobj,
			       struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE,
		"fb_events=%d wake_events=%d screen_on=%d deepdoze=%d " 
		"wakeboost=%d game=%d thermal_safe=%d temp_decic=%d samples=%d "
		"deep_entries=%d restore_ms=%d game_denials=%d "
		"post_suspend=%d cap_applied=%d\n",
		atomic_read(&ay_fb_events), atomic_read(&ay_wake_events),
		READ_ONCE(ay_screen_on) ? 1 : 0, atomic_read(&ay_deep),
		atomic_read(&ay_wake_active), READ_ONCE(ay_game_enabled) ? 1 : 0,
		atomic_read(&ay_thermal_safe), atomic_read(&ay_battery_temp),
		atomic_read(&ay_game_samples),
		atomic_read(&ay_deep_entries), atomic_read(&ay_restore_ms),
		atomic_read(&ay_game_denials), atomic_read(&ay_post_suspend_count),
		atomic_read(&ay_cap_applied));
}
static struct kobj_attribute telemetry_attr = __ATTR_RO(telemetry);

/* Clock includes suspend, unlike CPU timers or jiffies. */
static ssize_t screen_off_seconds_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	u64 now, start;

	if (READ_ONCE(ay_screen_on))
		return scnprintf(buf, PAGE_SIZE, "0\n");
	now = ay_now_ms();
	start = READ_ONCE(ay_screen_off_boottime_ms);
	return scnprintf(buf, PAGE_SIZE, "%llu\n",
		(unsigned long long)((now >= start ? now - start : 0) / 1000ULL));
}
static struct kobj_attribute screen_off_seconds_attr =
	__ATTR_RO(screen_off_seconds);

static ssize_t post_suspend_count_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%d\n",
			 atomic_read(&ay_post_suspend_count));
}
static struct kobj_attribute post_suspend_count_attr =
	__ATTR_RO(post_suspend_count);

static ssize_t cap_applied_show(struct kobject *kobj,
		struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE, "%d\n",
			 atomic_read(&ay_cap_applied));
}
static struct kobj_attribute cap_applied_attr = __ATTR_RO(cap_applied);

static struct attribute *ay_attrs[] = {
	&enabled_attr.attr, &delay_seconds_attr.attr, &cap_percent_attr.attr,
	&state_attr.attr, &telemetry_attr.attr, &wakeboost_attr.attr,
	&wakeboost_ms_attr.attr, &game_mode_attr.attr,
	&game_floor_percent_attr.attr, &battery_temp_decic_attr.attr,
	&thermal_guard_attr.attr, &restore_ms_attr.attr,
	&deep_entries_attr.attr, &game_denials_attr.attr,
	&screen_off_seconds_attr.attr, &post_suspend_count_attr.attr,
	&cap_applied_attr.attr, NULL,
};
static const struct attribute_group ay_attr_group = {.attrs = ay_attrs};
static int __init ay_deepdoze_init(void)
{
	int ret;
	INIT_DELAYED_WORK(&ay_doze_work, ay_enter_deepdoze);
	INIT_DELAYED_WORK(&ay_wake_work, ay_end_wakeboost);
	INIT_DELAYED_WORK(&ay_thermal_work, ay_thermal_sample);
	INIT_WORK(&ay_policy_work, ay_refresh_policies);
	ret = cpufreq_register_notifier(&ay_cpufreq_nb, CPUFREQ_POLICY_NOTIFIER);
	if (ret)
		return ret;
	ret = fb_register_client(&ay_fb_nb);
	if (ret)
		goto err_cpufreq;
	ret = register_pm_notifier(&ay_pm_nb);
	if (ret)
		goto err_fb;
	ay_kobj = kobject_create_and_add("ay_shadow", kernel_kobj);
	if (!ay_kobj) {
		ret = -ENOMEM;
		goto err_pm;
	}
	ret = sysfs_create_group(ay_kobj, &ay_attr_group);
	if (ret)
		goto err_kobj;
	pr_info("AY Shadow V6 DeepDoze initialized (OFF by default, delay=%u s)\n",
		ay_delay);
	return 0;
err_kobj:
	kobject_put(ay_kobj);
err_pm:
	unregister_pm_notifier(&ay_pm_nb);
err_fb:
	fb_unregister_client(&ay_fb_nb);
err_cpufreq:
	cpufreq_unregister_notifier(&ay_cpufreq_nb, CPUFREQ_POLICY_NOTIFIER);
	return ret;
}
static void __exit ay_deepdoze_exit(void)
{
	WRITE_ONCE(ay_enabled, false);
	atomic_set(&ay_deep, 0);
	fb_unregister_client(&ay_fb_nb);
	unregister_pm_notifier(&ay_pm_nb);
	cancel_delayed_work_sync(&ay_doze_work);
	cancel_delayed_work_sync(&ay_wake_work);
	cancel_delayed_work_sync(&ay_thermal_work);
	flush_work(&ay_policy_work);
	cpufreq_unregister_notifier(&ay_cpufreq_nb, CPUFREQ_POLICY_NOTIFIER);
	sysfs_remove_group(ay_kobj, &ay_attr_group);
	kobject_put(ay_kobj);
}
module_init(ay_deepdoze_init);
module_exit(ay_deepdoze_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("AY Shadow V6 Alpha4: no-app-exceptions UltraDoze, BOOTTIME, instant restore");
MODULE_AUTHOR("Eng. Ahmed Yasir");
