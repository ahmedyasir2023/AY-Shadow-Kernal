"""Panel-event bridge regression checks for failed framebuffer screen notifications."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
K=(R/"kernel/ay_deepdoze.c").read_text()
P=(R/"scripts/v6_patch.py").read_text()
V=(R/"scripts/v6_verify.py").read_text()
class PanelEventBridge(unittest.TestCase):
    def test_factual_root_cause(self):
        self.assertIn("CONFIG_MSM_DRM_NOTIFY is absent", P)
        self.assertIn("CONFIG_DRM_MSM_DSI_STAGING", V)
    def test_events_and_counters(self):
        for needle in ('void ay_shadow_panel_event(bool screen_on)',
                       'atomic_inc(&ay_panel_events)',
                       'ay_set_screen(screen_on)',
                       'EXPORT_SYMBOL_GPL(ay_shadow_panel_event)',
                       'panel_events=%d', 'FB_EARLY_EVENT_BLANK'):
            self.assertIn(needle,K)
    def test_guarded_upstream_instrumentation(self):
        for needle in ('dsi_panel.c', 'dsi_panel_enable(', 'dsi_panel_disable(',
                       'ay_shadow_panel_event(true)', 'ay_shadow_panel_event(false)',
                       'Unexpected DSI panel', '#include <linux/ay_shadow_panel.h>'):
            self.assertIn(needle,P)
    def test_safety_retained(self):
        for forbidden in ('disable_irq_nosync', 'setenforce',
                          'thermal_zone_device_unregister', 'pm_stay_awake('):
            self.assertNotIn(forbidden, K)
        self.assertIn("AY_DEFAULT_DELAY 600U",K)
        self.assertIn("static bool ay_enabled = true;",K)

if __name__=="__main__":
    unittest.main()
