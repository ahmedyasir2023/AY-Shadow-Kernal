"""V6 Alpha3 in-kernel hardware safety and read-only instrumentation checks."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = (ROOT / "kernel" / "ay_deepdoze.c").read_text()
BUILD = (ROOT / "build_v6.sh").read_text()
SCRIPT = (ROOT / "scripts" / "v6_diagnostics.sh").read_text()

class V6Alpha3Safety(unittest.TestCase):
    def test_no_application_inhibitor(self):
        self.assertNotIn("ay_inhibit", DRIVER)
        self.assertNotIn("__ATTR(inhibit", DRIVER)
        self.assertIn("cancel_delayed_work_sync(&ay_doze_work)", DRIVER)
        self.assertIn("atomic_set(&ay_deep, 0)", DRIVER)
        self.assertIn("system_freezable_wq", DRIVER)

    def test_wake_policy_restore_is_measured(self):
        self.assertIn("atomic_xchg(&ay_restore_pending, 0)", DRIVER)
        self.assertIn("jiffies_to_msecs(jiffies -", DRIVER)
        self.assertIn("READ_ONCE(ay_wake_started)", DRIVER)
        self.assertIn("__ATTR_RO(restore_ms)", DRIVER)

    def test_thermal_data_must_be_fresh(self):
        self.assertIn("time_before(jiffies, READ_ONCE(ay_last_sample)", DRIVER)
        self.assertIn("AY_BATTERY_SAMPLE_MS 5000U", DRIVER)
        self.assertIn("atomic_inc(&ay_game_denials)", DRIVER)
        self.assertIn("READ_ONCE(ay_screen_on)", DRIVER)

    def test_multiple_device_observables(self):
        for name in ("fb_events=", "wake_events=", "post_suspend=%d",
                     "deep_entries=%d", "restore_ms=%d", "game_denials=%d",
                     "__ATTR_RO(deep_entries)", "__ATTR_RO(game_denials)"):
            self.assertIn(name, DRIVER)

    def test_no_raw_flash_and_immutable_safety_defaults(self):
        self.assertIn("V6-A5-2", BUILD)
        self.assertIn("SOURCE BUILD only", BUILD)
        self.assertIn("static bool ay_enabled = true;", DRIVER)
        self.assertIn("static bool ay_wake_enabled = true;", DRIVER)
        self.assertIn("static bool ay_game_enabled;", DRIVER)
        for prohibited in ("thermal_zone_device_unregister", "setenforce",
                           "cpufreq_driver_target", "disable_irq_nosync"):
            self.assertNotIn(prohibited, DRIVER)

    def test_diagnostics_script_is_read_only(self):
        self.assertIn("v6_diagnostics.sh", SCRIPT)
        self.assertIn("id -u", SCRIPT)
        self.assertIn("/sys/kernel/ay_shadow", SCRIPT)
        self.assertNotIn('echo 1 >', SCRIPT)
        self.assertNotIn("setenforce", SCRIPT)
        self.assertNotIn("chmod 777", SCRIPT)

if __name__ == "__main__":
    unittest.main()
