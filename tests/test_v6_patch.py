"""Static V6 safety checks; CI separately compiles the real kernel C module."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class AlphaContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.driver = (ROOT / "kernel/ay_deepdoze.c").read_text()
        cls.patch = (ROOT / "scripts/v6_patch.py").read_text()

    def test_early_wake_and_freezable_timer(self):
        self.assertIn("FB_EARLY_EVENT_BLANK", self.driver)
        self.assertIn("system_freezable_wq", self.driver)
        self.assertIn("atomic_set(&ay_deep, 0)", self.driver)

    def test_fail_safe_off_at_boot(self):
        self.assertIn("static bool ay_enabled;", self.driver)
        self.assertIn("AY_DEFAULT_DELAY 600U", self.driver)
        self.assertIn("AY_DEFAULT_CAP 0U", self.driver)

    def test_no_thermal_bypass_or_unlimited_boost(self):
        for forbidden in ("setenforce", "cpufreq_driver_target", "thermal_zone_set"):
            self.assertNotIn(forbidden, self.driver)
        self.assertIn("cpufreq_verify_within_limits", self.driver)

    def test_v5_compatibility_inheritance(self):
        self.assertIn("scripts/v5_patch.py", self.patch)
        self.assertIn("CONFIG_AY_SHADOW_DEEPDOZE",
                      (ROOT / "scripts/v6_verify.py").read_text())

    def test_source_only_artifact(self):
        self.assertIn("SOURCE BUILD only", (ROOT / "build_v6.sh").read_text())

if __name__ == "__main__":
    unittest.main()
