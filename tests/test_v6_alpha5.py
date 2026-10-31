"""Alpha5 contract: native first-boot DT2W and reversible Android Rocket UI."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
P=(R/"scripts/v6_patch.py").read_text()
V=(R/"scripts/v6_verify.py").read_text()
S=(R/"scripts/v6_rocket_ui.sh").read_text()
class Alpha5(unittest.TestCase):
    def test_first_boot_native_dt2w(self):
        for token in ('old_dt2w = "uint8_t DouTap_enable = 0;"',
                      'new_dt2w = "uint8_t DouTap_enable = 1;"',
                      'tp_source.count(old_dt2w) != 1', 'ts->gesture_enable = 1;'):
            self.assertIn(token,P)
        self.assertIn('"uint8_t DouTap_enable = 1;"',V)
    def test_reversible_animation_controls(self):
        for token in ("window_animation_scale", "transition_animation_scale",
                      "animator_duration_scale", "settings get global",
                      "settings put global", "settings delete global",
                      "wakeboost", "on)", "off)", "status)"):
            self.assertIn(token,S)
        for forbidden in ("setenforce", "disable_irq", "thermal_zone_device_unregister",
                          "cpuinfo_max_freq", "chmod 777"):
            self.assertNotIn(forbidden,S)
if __name__=="__main__":
    unittest.main()
