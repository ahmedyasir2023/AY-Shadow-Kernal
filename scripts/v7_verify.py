#!/usr/bin/env python3
"""Verify V7 configuration after resolving defconfig and root/fingerprint preservation."""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    sys.exit("usage: v6_verify.py SOURCE_DIR OUT/.config")
src, path = Path(sys.argv[1]), Path(sys.argv[2])
config = dict(line.split("=", 1) for line in path.read_text().splitlines()
              if line.startswith("CONFIG_") and "=" in line)
required = {
    "CONFIG_LOCALVERSION": '"-AY-Shadow-V7-HyperSpeed"',
    "CONFIG_AY_SHADOW_DEEPDOZE": "y", "CONFIG_FB_NOTIFY": "y",
    "CONFIG_POWER_SUPPLY": "y",
    "CONFIG_INPUT_TOUCHSCREEN": "y",
    "CONFIG_TOUCHPANEL_OPPO": "y",
    "CONFIG_TOUCHPANEL_NOVA": "y",
    "CONFIG_TOUCHPANEL_NOVA_NT36672C_NOFLASH": "y",
    "CONFIG_TOUCHPANEL_NEW_SET_IRQ_WAKE": "y",
    "CONFIG_CPU_FREQ": "y", "CONFIG_PM_SLEEP": "y",
    "CONFIG_CPU_FREQ_GOV_SCHEDUTIL": "y",
    "CONFIG_KSU": "y", "CONFIG_KSU_SUSFS": "y",
    "CONFIG_SECCOMP_FILTER": "y", "CONFIG_ZRAM": "y",
    "CONFIG_OPPO_FINGERPRINT": "y",
    "CONFIG_OPPO_FINGERPRINT_GOODIX_OPTICAL": "y",
    "CONFIG_OPPO_FINGERPRINT_FPC": "y",
    "CONFIG_QTI_THERMAL_LIMITS_DCVS": "y",
    "CONFIG_NET_SCH_FQ_CODEL": "y", "CONFIG_TCP_CONG_WESTWOOD": "y",
}
errors = [f"{k}: expected {v}, got {config.get(k)!r}"
          for k, v in required.items() if config.get(k) != v]
source = (src / "drivers/misc/ay_deepdoze.c").read_text()
for guard in ("FB_EARLY_EVENT_BLANK", "system_freezable_wq", "CPUFREQ_ADJUST",
              "cpufreq_verify_within_limits", "AY_DEFAULT_DELAY 600U",
              "static bool ay_enabled = true;", "fb_unregister_client",
              "AY_WAKE_MS 400U", "AY_GAME_FLOOR 25U",
              "AY_BATTERY_LIMIT_DECI_C 400", "power_supply_get_by_name",
              "power_supply_put", "AY_BATTERY_SAMPLE_MS 5000U",
              "static bool ay_wake_enabled = true;", "static bool ay_game_enabled;",
              "static bool ay_touch_enabled = true;", "AY_TOUCH_MS 800U",
              "AY_TOUCH_FLOOR 55U", "input_register_handler",
              "input_unregister_handler", "__ATTR(touchboost, 0600",
              "__ATTR_RO(touch_events)",
              "AY_DEFAULT_CAP 0U", "ktime_get_boottime()",
              "ay_shadow_panel_event(bool screen_on)",
              "EXPORT_SYMBOL_GPL(ay_shadow_panel_event)",
              "panel_events=%d",
              "ay_touch_registered = true;",
              "ret = input_register_handler(&ay_touch_handler);",
              "register_pm_notifier", "PM_POST_SUSPEND",
              "__ATTR_RO(screen_off_seconds)", "__ATTR_RO(post_suspend_count)",
              "__ATTR_RO(cap_applied)",
              "atomic_read(&ay_restore_ms)", "AY_BATTERY_SAMPLE_MS",
              "time_before(jiffies, READ_ONCE(ay_last_sample)"):
    if guard not in source:
        errors.append("Missing driver safety gate: " + guard)
# RMX2170 project 19721 native Novatek NT36672C gesture/wake path.
tp_common = (src / "drivers/input/touchscreen/oppo_touchscreen/touchpanel_common_driver.c").read_text()
tp_nvt = (src / "drivers/input/touchscreen/oppo_touchscreen/Novatek/NT36672C_noflash/nvt_drivers_nt36672c_noflash.c").read_text()
tp_dts = (src / "arch/arm64/boot/dts/19721/atoll-idp.dtsi").read_text()
for label, blob, guards in (
    ("touch common", tp_common, (
        "GESTURE_ATTR(double_tap, DouTap_enable);",
        "uint8_t DouTap_enable = 1;",
        "ts->gesture_enable = 1;",
        "key = KEY_DOUBLE_TAP;",
        "enable_irq_wake(ts->irq);",
        "disable_irq_wake(ts->irq);",
        "if (ts->new_set_irq_wake_support)",
    )),
    ("Novatek NT36672C", tp_nvt, (
        "case DTAP_DETECT:",
        "gesture->gesture_type  = DouTap;",
        "nvt_enable_black_gesture",
        "CMD_OPEN_BLACK_GESTURE",
    )),
    ("RMX2170 project 19721 device tree", tp_dts, (
        'compatible = "novatek,nf_nt36672c";',
        "project_id = <19721>;",
        "black_gesture_support;",
        "new_set_irq_wake_support;",
    )),
):
    for guard in guards:
        if guard not in blob:
            errors.append(f"Missing Double-Tap-to-Wake support in {label}: " + guard)

panel_data = (src / "drivers/gpu/drm/msm/dsi-staging/dsi_panel.c").read_text()
panel_header = src / "include/linux/ay_shadow_panel.h"
for required in ('#include <linux/ay_shadow_panel.h>',
                 "ay_shadow_panel_event(true);",
                 "ay_shadow_panel_event(false);"):
    if required not in panel_data:
        errors.append("Missing DSI panel event hook: " + required)
if not panel_header.is_file():
    errors.append("Missing panel bridge header")
if config.get("CONFIG_DRM_MSM_DSI_STAGING") != "y":
    errors.append("Physical DSI panel implementation not compiled")

if "KSU_VERSION := 33355" not in (src / "drivers/kernelsu/Makefile").read_text():
    errors.append("KernelSU source version changed unexpectedly")
if 'SUSFS_VERSION "v2.3.0"' not in (src / "include/linux/susfs.h").read_text():
    errors.append("SUSFS version changed unexpectedly")
for guard in ("AY_TURBO_MS 450U", "AY_TURBO_FLOOR 70U",
              "AY_RAPID_WINDOW_MS 350U", "AY_TURBO_TEMP_DECI_C 375",
              "system_highpri_wq", "__ATTR(touch_turbo, 0600",
              "__ATTR_RO(turbo_events)", "ay_turbo_active",
              "cancel_delayed_work_sync(&ay_turbo_work)"):
    if guard not in source:
        errors.append("Missing V7 adaptive boost gate: " + guard)
if errors:
    sys.exit("V7 verification FAILED:\n" + "\n".join(errors))
print("V7 HyperSpeed config PASS: UltraDoze, native RMX2170 Novatek DT2W/IRQ wake, fingerprint, root, thermal guards.")
print("Hardware behavior not validated: do not flash unreviewed raw kernel.")
