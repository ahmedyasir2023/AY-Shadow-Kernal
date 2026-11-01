"""Alpha5.2 Rocket bounded boost regression tests."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
K = (ROOT / "kernel/ay_deepdoze.c").read_text()
UI = (ROOT / "scripts/v6_rocket_ui.sh").read_text()
class Rocket(unittest.TestCase):
    def test_performance_window(self):
        for token in ("AY_WAKE_MS 350U", "AY_WAKE_FLOOR 30U",
                      "AY_TOUCH_MS 900U", "AY_TOUCH_FLOOR 45U",
                      "value < 10 || value > 50",
                      "wake_floor_adjustments=%d touch_floor_adjustments=%d"):
            self.assertIn(token, K)
    def test_deep_sleep_and_safety(self):
        for token in ("AY_DEFAULT_DELAY 600U", "AY_DEFAULT_CAP 0U",
                      "AY_BATTERY_LIMIT_DECI_C 400", "if (!READ_ONCE(ay_screen_on))",
                      "atomic_set(&ay_touch_active, 0)",
                      "atomic_set(&ay_wake_active, 0)",
                      "cpufreq_verify_within_limits(policy, floor, policy->max)"):
            self.assertIn(token, K)
        for forbidden in ("pm_stay_awake(", "thermal_zone_device_unregister",
                          "cpufreq_driver_target", "disable_irq_nosync"):
            self.assertNotIn(forbidden, K)
    def test_visual_changes_are_reversible(self):
        self.assertIn('settings put global "$key" 0.5', UI)
        self.assertIn('settings delete global "$key"', UI)
if __name__ == "__main__":
    unittest.main()
