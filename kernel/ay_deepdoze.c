// SPDX-License-Identifier: GPL-2.0
/*
 * AY Shadow V6 Alpha 1 — Eng. Ahmed Yasir / RMX2170.
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
#include <linux/sysfs.h>
#include <linux/workqueue.h>

#define AY_DEFAULT_DELAY 600U
#define AY_DEFAULT_CAP 55U

static struct kobject *ay_kobj;
static DEFINE_MUTEX(ay_control_lock);
static struct delayed_work ay_doze_work;
static struct work_struct ay_policy_work;
static atomic_t ay_deep = ATOMIC_INIT(0);
static atomic_t ay_fb_events = ATOMIC_INIT(0);
static atomic_t ay_wake_events = ATOMIC_INIT(0);
static bool ay_enabled; /* deliberately OFF by default until hardware validation */
static bool ay_screen_on = true;
static unsigned int ay_delay = AY_DEFAULT_DELAY;
static unsigned int ay_cap = AY_DEFAULT_CAP;
static unsigned long ay_screen_off_at;

static int ay_cpufreq_adjust(struct notifier_block *nb,
			     unsigned long event, void *data)
{
	struct cpufreq_policy *policy = data;
	unsigned int min, max, limit;

	if (event != CPUFREQ_ADJUST || !READ_ONCE(ay_enabled) ||
	    !atomic_read(&ay_deep) || !policy)
		return NOTIFY_OK;

	min = policy->cpuinfo.min_freq;
	max = policy->cpuinfo.max_freq;
	if (max <= min)
		return NOTIFY_OK;
	/* Restrict only maximum; never raise current min, max, or thermal limit. */
	limit = min + (unsigned int)(((u64)(max - min) *
					  READ_ONCE(ay_cap)) / 100U);
	if (limit < policy->min)
		limit = policy->min;
	if (limit < policy->max)
		cpufreq_verify_within_limits(policy, policy->min, limit);
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
}
static void ay_enter_deepdoze(struct work_struct *work)
{
	if (!READ_ONCE(ay_enabled) || READ_ONCE(ay_screen_on))
		return;
	atomic_set(&ay_deep, 1);
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
		atomic_set(&ay_deep, 0);
		cancel_delayed_work(&ay_doze_work);
		schedule_work(&ay_policy_work);
	} else {
		WRITE_ONCE(ay_screen_off_at, jiffies);
		if (READ_ONCE(ay_enabled))
			mod_delayed_work(system_freezable_wq, &ay_doze_work,
				msecs_to_jiffies(READ_ONCE(ay_delay) * 1000U));
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
	} else if (!READ_ONCE(ay_screen_on)) {
		unsigned long elapsed = jiffies - READ_ONCE(ay_screen_off_at);
		unsigned long target = msecs_to_jiffies(READ_ONCE(ay_delay) * 1000U);
		mod_delayed_work(system_freezable_wq, &ay_doze_work,
			target > elapsed ? target - elapsed : 0);
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
	    !atomic_read(&ay_deep)) {
		unsigned long elapsed = jiffies - READ_ONCE(ay_screen_off_at);
		unsigned long target = msecs_to_jiffies(value * 1000U);
		mod_delayed_work(system_freezable_wq, &ay_doze_work,
			target > elapsed ? target - elapsed : 0);
	}
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
	if (value < 35 || value > 95)
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
		state = "deepdoze";
	else
		state = "light_idle";
	return scnprintf(buf, PAGE_SIZE, "%s\n", state);
}
static struct kobj_attribute state_attr = __ATTR_RO(state);
static ssize_t telemetry_show(struct kobject *kobj,
			       struct kobj_attribute *attr, char *buf)
{
	return scnprintf(buf, PAGE_SIZE,
		"fb_events=%d wake_events=%d screen_on=%d deepdoze=%d\n",
		atomic_read(&ay_fb_events), atomic_read(&ay_wake_events),
		READ_ONCE(ay_screen_on) ? 1 : 0, atomic_read(&ay_deep));
}
static struct kobj_attribute telemetry_attr = __ATTR_RO(telemetry);

static struct attribute *ay_attrs[] = {
	&enabled_attr.attr, &delay_seconds_attr.attr, &cap_percent_attr.attr,
	&state_attr.attr, &telemetry_attr.attr, NULL,
};
static const struct attribute_group ay_attr_group = {.attrs = ay_attrs};
static int __init ay_deepdoze_init(void)
{
	int ret;
	INIT_DELAYED_WORK(&ay_doze_work, ay_enter_deepdoze);
	INIT_WORK(&ay_policy_work, ay_refresh_policies);
	ret = cpufreq_register_notifier(&ay_cpufreq_nb, CPUFREQ_POLICY_NOTIFIER);
	if (ret)
		return ret;
	ret = fb_register_client(&ay_fb_nb);
	if (ret)
		goto err_cpufreq;
	ay_kobj = kobject_create_and_add("ay_shadow", kernel_kobj);
	if (!ay_kobj) {
		ret = -ENOMEM;
		goto err_fb;
	}
	ret = sysfs_create_group(ay_kobj, &ay_attr_group);
	if (ret)
		goto err_kobj;
	pr_info("AY Shadow V6 DeepDoze initialized (OFF by default, delay=%u s)\n",
		ay_delay);
	return 0;
err_kobj:
	kobject_put(ay_kobj);
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
	cancel_delayed_work_sync(&ay_doze_work);
	flush_work(&ay_policy_work);
	cpufreq_unregister_notifier(&ay_cpufreq_nb, CPUFREQ_POLICY_NOTIFIER);
	sysfs_remove_group(ay_kobj, &ay_attr_group);
	kobject_put(ay_kobj);
}
module_init(ay_deepdoze_init);
module_exit(ay_deepdoze_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("AY Shadow V6 DeepDoze: 10-minute screen-off CPU ceiling and early wake restore");
MODULE_AUTHOR("Eng. Ahmed Yasir");
