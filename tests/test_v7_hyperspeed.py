"""V7 real-feature safety contracts; no claims about actual app startup latency."""
import unittest
from pathlib import Path
R = Path(__file__).resolve().parents[1]
K = (R/"kernel/ay_deepdoze.c").read_text()
P = (R/"scripts/v7_patch.py").read_text()
V = (R/"scripts/v7_verify.py").read_text()
B = (R/"build_v7.sh").read_text()

class V7HyperSpeed(unittest.TestCase):
    def test_genuine_short_adaptive_turbo(self):
        for t in ("AY_WAKE_MS 400U", "AY_WAKE_FLOOR 40U",
                  "AY_TOUCH_MS 800U", "AY_TOUCH_FLOOR 55U",
                  "AY_TURBO_MS 450U", "AY_TURBO_FLOOR 70U",
                  "AY_RAPID_WINDOW_MS 350U", "AY_TURBO_TEMP_DECI_C 375",
                  "atomic_set(&ay_turbo_active, 1)",
                  "atomic_set(&ay_turbo_active, 0)",
                  "mod_delayed_work(system_wq, &ay_turbo_work",
                  "cancel_delayed_work_sync(&ay_turbo_work)",
                  "queue_work(system_highpri_wq, &ay_policy_work)"):
            self.assertIn(t, K)

    def test_screen_off_no_wakelock_and_hardware_limits(self):
        for t in ("AY_DEFAULT_DELAY 600U", "AY_DEFAULT_CAP 0U",
                  "ay_shadow_panel_event(bool screen_on)",
                  "CPUFREQ_ADJUST", "cpufreq_verify_within_limits",
                  "AY_BATTERY_LIMIT_DECI_C 400",
                  "time_before(jiffies, READ_ONCE(ay_last_sample)",
                  "FB_EARLY_EVENT_BLANK", "PM_POST_SUSPEND",
                  "atomic_set(&ay_touch_active, 0)",
                  "atomic_set(&ay_turbo_active, 0)",
                  "atomic_set(&ay_wake_active, 0)"):
            self.assertIn(t, K)
        for t in ("pm_stay_awake(", "pm_wakeup_event(",
                  "thermal_zone_device_unregister", "setenforce",
                  "disable_irq_nosync", "cpufreq_driver_target",
                  "__ATTR(inhibit", "app_whitelist"):
            self.assertNotIn(t, K)

    def test_reversible_controls_and_instrumentation(self):
        for t in ('__ATTR(touch_turbo, 0600',
                  '__ATTR_RO(turbo_events)', 'turbo_active=%d turbo_events=%d',
                  '"panel_events=%d', 'atomic_read(&ay_turbo_events)'):
            self.assertIn(t, K)

    def test_pin_fingerprint_root_screen_verified_by_build(self):
        for t in ("scripts/v5_patch.py", "dsi_panel_enable",
                  "dsi_panel_disable", "ay_shadow_panel_event(true)",
                  "ay_shadow_panel_event(false)",
                  'new_dt2w = "uint8_t DouTap_enable = 1;"',
                  '"-AY-Shadow-V7-HyperSpeed"'):
            self.assertIn(t, P)
        for t in ("CONFIG_KSU", "CONFIG_KSU_SUSFS",
                  "CONFIG_OPPO_FINGERPRINT", "CONFIG_TOUCHPANEL_NOVA",
                  "CONFIG_DRM_MSM_DSI_STAGING",
                  "AY_TURBO_FLOOR 70U", "AY_DEFAULT_DELAY 600U"):
            self.assertIn(t, V)
        for t in ("Image.gz-dtb", "sha256sum", "v7_verify.py",
                  "v7_patch.py", "SOURCE BUILD only", "PIN="):
            self.assertIn(t, B)
    def test_art_opt_in_only(self):
        s=(R/"scripts/v7_art_optimizer.sh").read_text()
        for t in ("profile-one", "full-one", "profile-all",
                  "speed-profile", "cmd package compile",
                  "pm list packages -3", "battery/temp"):
            self.assertIn(t,s)
        self.assertNotIn("setenforce",s)
        self.assertNotIn("pm clear",s)

if __name__ == "__main__":
    unittest.main()
