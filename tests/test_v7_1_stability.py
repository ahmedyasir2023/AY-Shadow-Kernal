"""AY Shadow V7.1 source contracts. Hardware tests are a separate release gate."""
import pathlib
import unittest
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
K = (ROOT / "kernel/ay_deepdoze.c").read_text()
P = (ROOT / "scripts/v7_1_patch.py").read_text()
V = (ROOT / "scripts/v7_1_verify.py").read_text()
B = (ROOT / "build_v7_1.sh").read_text()

def func(name, next_name):
    return K.split(name, 1)[1].split(next_name, 1)[0]

class V71Stability(unittest.TestCase):
    def test_deepdoze_true_transitions_only(self):
        start = func("static void ay_enter_deepdoze(struct work_struct *work)", "static void ay_set_screen")
        self.assertIn("atomic_cmpxchg(&ay_deep, 0, 1) != 0", start)
        self.assertLess(start.index("atomic_cmpxchg(&ay_deep, 0, 1)"), start.index("atomic_inc(&ay_deep_entries)"))
        self.assertEqual(start.count("atomic_inc(&ay_deep_entries)"), 1)
        schedule = func("static void ay_schedule_doze(void)", "static int ay_pm_event")
        self.assertIn("if (atomic_read(&ay_deep))", schedule)
        self.assertIn("atomic_inc(&ay_doze_rearm_skips)", schedule)
        self.assertIn("system_freezable_wq", schedule)
        self.assertIn("AY_DEFAULT_DELAY 600U", K)
        self.assertIn("AY_DEFAULT_CAP 0U", K)

    def test_touch_repeated_events_not_forcing_policy_refresh(self):
        t = func("static void ay_touch_event(", "static int ay_touch_connect(")
        self.assertIn("atomic_cmpxchg(&ay_touch_active, 0, 1)", t)
        self.assertIn("atomic_cmpxchg(&ay_turbo_active, 0, 1)", t)
        self.assertIn("if (touch_started || turbo_started)", t)
        self.assertIn("atomic_inc(&ay_touch_refresh_skips)", t)
        self.assertIn("mod_delayed_work(system_wq, &ay_touch_work", t)
        self.assertIn("mod_delayed_work(system_wq, &ay_turbo_work", t)
        self.assertIn("AY_TURBO_TEMP_DECI_C 375", K)
        self.assertIn("AY_BATTERY_LIMIT_DECI_C 400", K)

    def test_thermal_refresh_only_on_state_change(self):
        t = func("static void ay_thermal_sample(", "static void ay_enter_deepdoze(")
        self.assertIn("was_safe = atomic_xchg(&ay_thermal_safe, now_safe)", t)
        self.assertIn("if (was_safe != now_safe || turbo_stopped)", t)
        self.assertIn("power_supply_get_property", t)
        self.assertIn("power_supply_put", t)

    def test_telemetry_is_read_only_and_bounded(self):
        for token in ('doze_rearm_skips=%d', 'touch_refresh_skips=%d',
                      'policy_refreshes=%d', '__ATTR_RO(telemetry)',
                      '__ATTR_RO(deep_entries)', '__ATTR_RO(post_suspend_count)',
                      '__ATTR(touch_turbo, 0600', 'atomic_inc(&ay_policy_refreshes)'):
            self.assertIn(token, K)
        for unsafe in ('pm_stay_awake(', 'pm_wakeup_event(',
                       'disable_irq_nosync(', 'setenforce', 'thermal_zone_device_unregister',
                       'cpufreq_driver_target(', 'alarmtimer_suspend('):
            self.assertNotIn(unsafe, K)
        self.assertIn('cpufreq_verify_within_limits', K)
        self.assertIn('ay_shadow_panel_event(bool screen_on)', K)

    def test_kernel_info_log_has_valid_c_call(self):
        # This regression previously compiled as '"pr_info("AY Shadow...'.
        self.assertNotIn('"pr_info(', K)
        self.assertIn('pr_info("AY Shadow V7.1 Stability:', K)
        self.assertEqual(K.count('pr_info("AY Shadow V7.1 Stability:'), 1)

    def test_fingerprint_and_root_pin_and_release(self):
        for token in ('scripts/v5_patch.py', 'ay_shadow_panel_event(true)',
                      'ay_shadow_panel_event(false)',
                      'DouTap_enable = 1;', '"-AY-Shadow-V7.1-Stability"'):
            self.assertIn(token, P)
        for token in ('CONFIG_KSU', 'CONFIG_KSU_SUSFS',
                      'CONFIG_OPPO_FINGERPRINT', 'CONFIG_TOUCHPANEL_NOVA',
                      'AY_DEFAULT_DELAY 600U', 'V7.1 stability gate'):
            self.assertIn(token, V)
        for token in ('PIN=', 'v7_1_patch.py', 'v7_1_verify.py',
                      'Image.gz-dtb', 'sha256sum', 'SOURCE BUILD only'):
            self.assertIn(token, B)
        self.assertIn('7306b28fccd87db72f25b314105747b1ce6f653c', B)

if __name__ == '__main__':
    unittest.main()
