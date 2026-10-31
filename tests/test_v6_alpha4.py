"""V6 TITAN Alpha4 UltraDoze safety contracts."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "kernel/ay_deepdoze.c").read_text()
CFG = (ROOT / "scripts/v6_patch.py").read_text()
VER = (ROOT / "scripts/v6_verify.py").read_text()
DOC = (ROOT / "docs/V6-ALPHA4.md").read_text()
DIAG = (ROOT / "scripts/v6_diagnostics.sh").read_text()


class UltraDozeContract(unittest.TestCase):
    def test_no_application_inhibitor_or_allowlist(self):
        for forbidden in ("ay_inhibit", "__ATTR(inhibit", "app_whitelist",
                          "UID_WHITELIST", "phone_call_exception",
                          "audio_exception", "navigation_exception"):
            self.assertNotIn(forbidden, SRC)

    def test_minimum_cpu_cap_and_wall_time(self):
        self.assertIn("AY_DEFAULT_DELAY 600U", SRC)
        self.assertIn("AY_DEFAULT_CAP 0U", SRC)
        self.assertIn("value > 95", SRC)
        self.assertIn("cpufreq_verify_within_limits(policy, policy->min, limit)", SRC)

    def test_suspend_time_is_counted_without_forcing_wakeup(self):
        for required in ("ktime_get_boottime()", "ay_remaining_ms()",
                         "PM_POST_SUSPEND", "register_pm_notifier",
                         "unregister_pm_notifier", "system_freezable_wq",
                         "ay_schedule_doze()"):
            self.assertIn(required, SRC)
        self.assertNotIn("alarm_start(", SRC)
        self.assertNotIn("pm_wakeup_event(", SRC)

    def test_wake_clear_and_thermal_protection(self):
        self.assertIn("FB_EARLY_EVENT_BLANK", SRC)
        self.assertIn("atomic_set(&ay_deep, 0)", SRC)
        self.assertIn("cancel_delayed_work(&ay_doze_work)", SRC)
        for forbidden in ("setenforce", "thermal_zone_device_unregister",
                          "disable_irq_nosync", "cpufreq_driver_target"):
            self.assertNotIn(forbidden, SRC)

    def test_closed_by_default_without_on_device_check(self):
        for required in ("static bool ay_enabled;", "static bool ay_wake_enabled;",
                         "static bool ay_game_enabled;"):
            self.assertIn(required, SRC)
        self.assertIn('"-AY-Shadow-V6-A5"', CFG)
        self.assertIn("AY_DEFAULT_CAP 0U", VER)
        self.assertIn("fingerprint", DOC.lower())

    def test_native_double_tap_wake_path_is_required(self):
        for required in ("CONFIG_TOUCHPANEL_NOVA", "CONFIG_TOUCHPANEL_NOVA_NT36672C_NOFLASH",
                         "CONFIG_TOUCHPANEL_NEW_SET_IRQ_WAKE", "black_gesture_support;",
                         "new_set_irq_wake_support;", "DTAP_DETECT",
                         "KEY_DOUBLE_TAP", "enable_irq_wake(ts->irq)"):
            self.assertIn(required, VER)
        for required in ("double_tap_enable", "gesture_enable", "wakeup_sources"):
            self.assertIn(required, DIAG)
        self.assertIn("Double-Tap-to-Wake", DOC)
        self.assertIn("/proc/touchpanel/double_tap_enable", DOC)
        self.assertNotIn("disable_irq_wake", SRC)

    def test_wall_time_and_policy_counters_are_visible(self):
        for required in ("__ATTR_RO(screen_off_seconds)",
                         "__ATTR_RO(post_suspend_count)",
                         "__ATTR_RO(cap_applied)", "post_suspend=%d",
                         "cap_applied=%d"):
            self.assertIn(required, SRC)


if __name__ == "__main__":
    unittest.main()
