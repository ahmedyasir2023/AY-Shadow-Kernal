"""AY Shadow V6 Alpha3 safety contracts, before the full kernel CI compilation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DRIVER = (ROOT / "kernel" / "ay_deepdoze.c").read_text()
PATCH = (ROOT / "scripts" / "v6_patch.py").read_text()
BUILD = (ROOT / "build_v6.sh").read_text()
VERIFY = (ROOT / "scripts" / "v6_verify.py").read_text()

class TitanAlpha3Contracts(unittest.TestCase):
    def test_wakeboost_is_opt_in_and_finite(self):
        self.assertIn("static bool ay_wake_enabled = true;", DRIVER)
        self.assertIn("AY_WAKE_MS 250U", DRIVER)
        self.assertIn("value < 100 || value > 500", DRIVER)
        self.assertIn("atomic_set(&ay_wake_active, 0)", DRIVER)
        self.assertIn("mod_delayed_work(system_wq, &ay_wake_work", DRIVER)
        self.assertIn("cpufreq_verify_within_limits(policy, floor, policy->max)", DRIVER)

    def test_game_boost_fails_closed_without_battery_sensor(self):
        self.assertIn("static bool ay_game_enabled;", DRIVER)
        self.assertIn("AY_BATTERY_LIMIT_DECI_C 400", DRIVER)
        self.assertIn('power_supply_get_by_name("battery")', DRIVER)
        self.assertIn("power_supply_get_property(battery, POWER_SUPPLY_PROP_TEMP", DRIVER)
        self.assertIn("power_supply_put(battery)", DRIVER)
        self.assertIn("atomic_set(&ay_thermal_safe, !ret && temperature >= 0", DRIVER)
        self.assertIn("atomic_read(&ay_thermal_safe)", DRIVER)
        self.assertIn("value < 10 || value > 35", DRIVER)

    def test_no_security_or_thermal_bypass(self):
        for forbidden in ("setenforce", "thermal_zone_device_unregister",
                          "cpufreq_driver_target", "thermal_limit=0"):
            self.assertNotIn(forbidden, DRIVER)
        self.assertIn("if (floor > policy->max)", DRIVER)

    def test_screen_off_clears_short_boosts(self):
        self.assertIn("FB_EARLY_EVENT_BLANK", DRIVER)
        self.assertIn("atomic_set(&ay_wake_active, 0)", DRIVER)
        self.assertIn("atomic_set(&ay_thermal_safe, 0)", DRIVER)
        self.assertIn("cancel_delayed_work(&ay_wake_work)", DRIVER)
        self.assertIn("cancel_delayed_work(&ay_thermal_work)", DRIVER)

    def test_alpha2_full_kernel_build(self):
        self.assertIn('"CONFIG_POWER_SUPPLY": "y"', VERIFY)
        self.assertIn('("POWER_SUPPLY", "y")', PATCH)
        self.assertIn("AY-Shadow-V6-A5-AUTO", BUILD)
        self.assertIn("Image.gz-dtb", BUILD)
        self.assertIn("SOURCE BUILD only", BUILD)

    def test_root_only_control_knobs(self):
        for name in ("__ATTR(wakeboost, 0600", "__ATTR(wakeboost_ms, 0600",
                     "__ATTR(game_mode, 0600", "__ATTR(game_floor_percent, 0600",
                     "__ATTR_RO(battery_temp_decic)", "__ATTR_RO(thermal_guard)"):
            self.assertIn(name, DRIVER)

if __name__ == "__main__":
    unittest.main()
