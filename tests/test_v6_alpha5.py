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
    def test_bounded_thermal_guarded_touch_launch_boost(self):
        kernel=(R/"kernel/ay_deepdoze.c").read_text()
        for token in ("AY_TOUCH_MS 900U", "AY_TOUCH_FLOOR 45U",
                      "static bool ay_touch_enabled = true;", "input_register_handler",
                      "input_unregister_handler", "code != BTN_TOUCH",
                      "READ_ONCE(ay_screen_on)", "atomic_read(&ay_thermal_safe)",
                      "time_before(jiffies, READ_ONCE(ay_last_sample)",
                      "cancel_delayed_work_sync(&ay_touch_work)",
                      "__ATTR(touchboost, 0600", "__ATTR_RO(touch_events)"):
            self.assertIn(token,kernel)
        for forbidden in ("pm_stay_awake(", "pm_wakeup_event(",
                          "thermal_zone_device_unregister",
                          "cpufreq_driver_target", "__ATTR(inhibit"):
            self.assertNotIn(forbidden,kernel)

    def test_auto_boot_profile_has_no_manual_startup_requirement(self):
        kernel=(R/"kernel/ay_deepdoze.c").read_text()
        for token in ("static bool ay_enabled = true;",
                      "static bool ay_wake_enabled = true;",
                      "static bool ay_touch_enabled = true;",
                      "ay_touch_registered = true;",
                      "input_register_handler(&ay_touch_handler)",
                      "static bool ay_game_enabled;",
                      "AY_DEFAULT_DELAY 600U",
                      "FB_EARLY_EVENT_BLANK"):
            self.assertIn(token,kernel)
        self.assertNotIn("pm_stay_awake(",kernel)

    def test_app_compilation_is_opt_in(self):
        launcher=(R/"scripts/v6_app_launch.sh").read_text()
        for token in ("speed-profile", "-m speed", "pm compile --reset",
                      "pm list packages -3", "case", "battery/temp"):
            self.assertIn(token,launcher)
        self.assertNotIn("-a",launcher)

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
