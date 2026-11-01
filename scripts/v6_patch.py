#!/usr/bin/env python3
"""Compile V6 DeepDoze into pinned, fingerprint-compatible V5 RC2 kernel source."""
from pathlib import Path
import re
import subprocess
import sys

if len(sys.argv) != 2:
    sys.exit("usage: v6_patch.py SOURCE_DIR")
src = Path(sys.argv[1]).resolve()
root = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(root / "scripts/v5_patch.py"), str(src)], check=True)

# Restore native DT2W default immediately after the touchscreen driver initializes.
# Android may subsequently override it according to the user's preference.
tp = src / "drivers/input/touchscreen/oppo_touchscreen/touchpanel_common_driver.c"
tp_source = tp.read_text()
old_dt2w = "uint8_t DouTap_enable = 0;"
new_dt2w = "uint8_t DouTap_enable = 1;"
if tp_source.count(old_dt2w) != 1 or tp_source.count("ts->gesture_enable = 1;") != 1:
    sys.exit("Unexpected touch source: refuse to modify DT2W boot default")
tp.write_text(tp_source.replace(old_dt2w, new_dt2w, 1))


# Physical primary display transition hook for the pinned Qualcomm DSI pipeline.
# CONFIG_MSM_DRM_NOTIFY is absent from the tested atoll .config, so merely
# registering that optional notifier is not a correct fix. We instrument the
# existing compiled panel enable/disable functions (not the touch/fingerprint).
panel = src / "drivers/gpu/drm/msm/dsi-staging/dsi_panel.c"
panel_data = panel.read_text()
include_anchor = '#include "dsi_panel.h"'
enable_anchor = '''	lcd_queue_load_tp_fw();
 /* add begin by zhaifeibao'''
# Guard exact function bodies by their unique end snippets to avoid modifying
# unrelated display paths if upstream changes.
panel_enable_begin = panel_data.index("int dsi_panel_enable(struct dsi_panel *panel)")
panel_post_begin = panel_data.index("int dsi_panel_post_enable(struct dsi_panel *panel)")
panel_disable_begin = panel_data.index("int dsi_panel_disable(struct dsi_panel *panel)")
panel_unprepare_begin = panel_data.index("int dsi_panel_unprepare(struct dsi_panel *panel)")
panel_enable_src = panel_data[panel_enable_begin:panel_post_begin]
panel_disable_src = panel_data[panel_disable_begin:panel_unprepare_begin]
if panel_data.count(include_anchor) != 1 or panel_enable_src.count("lcd_queue_load_tp_fw();") != 1:
    sys.exit("Unexpected DSI panel enable implementation; aborting screen bridge")
if panel_enable_src.count("return rc;") != 1 or panel_disable_src.count("return rc;") != 1:
    sys.exit("Unexpected DSI panel return paths; aborting screen bridge")
# Only notify on a successfully initialized panel and only after its mutex is released.
panel_enable_src = panel_enable_src.replace(
    "lcd_queue_load_tp_fw();",
    "lcd_queue_load_tp_fw();\n\tif (!rc)\n\t\tay_shadow_panel_event(true);", 1)
panel_disable_src = panel_disable_src.replace(
    "\tmutex_unlock(&panel->panel_lock);\n\treturn rc;\n}",
    "\tmutex_unlock(&panel->panel_lock);\n\tif (!rc)\n\t\tay_shadow_panel_event(false);\n\treturn rc;\n}", 1)
if panel_disable_src.count("ay_shadow_panel_event(false)") != 1:
    sys.exit("Unable to place DSI panel disable bridge safely")
panel_data = (panel_data[:panel_disable_begin] + panel_disable_src +
              panel_data[panel_unprepare_begin:])
panel_data = (panel_data[:panel_enable_begin] + panel_enable_src +
              panel_data[panel_post_begin:])
panel_data = panel_data.replace(include_anchor,
                                include_anchor + "\n#include <linux/ay_shadow_panel.h>", 1)
panel.write_text(panel_data)
header = src / "include/linux/ay_shadow_panel.h"
header.write_text('''/* SPDX-License-Identifier: GPL-2.0 */
#ifndef _LINUX_AY_SHADOW_PANEL_H
#define _LINUX_AY_SHADOW_PANEL_H
#include <linux/types.h>
#ifdef CONFIG_AY_SHADOW_DEEPDOZE
void ay_shadow_panel_event(bool screen_on);
#else
static inline void ay_shadow_panel_event(bool screen_on) {}
#endif
#endif
''')

driver = root / "kernel/ay_deepdoze.c"
if not driver.is_file():
    sys.exit("Missing V6 driver source")
(src / "drivers/misc/ay_deepdoze.c").write_bytes(driver.read_bytes())

kconfig = src / "drivers/misc/Kconfig"
s = kconfig.read_text()
entry = (
    "config AY_SHADOW_DEEPDOZE\n"
    "    bool \"AY Shadow DeepDoze experimental CPU policy controller\"\n"
    "    depends on FB_NOTIFY && CPU_FREQ && PM_SLEEP && SYSFS\n"
    "    default n\n"
    "    help\n"
    "      BOOTTIME-aware 10-minute UltraDoze CPU limit with early\n"
    "      framebuffer wake restoration, no app exceptions, thermal preserved.\n"
)
if "config AY_SHADOW_DEEPDOZE" not in s:
    if 'menu "Misc devices"' not in s:
        sys.exit("Unexpected misc Kconfig structure")
    s = s.replace('menu "Misc devices"', 'menu "Misc devices"\n\n' + entry, 1)
kconfig.write_text(s)

makefile = src / "drivers/misc/Makefile"
s = makefile.read_text()
entry = "obj-$(CONFIG_AY_SHADOW_DEEPDOZE) += ay_deepdoze.o\n"
if entry not in s:
    s += "\n" + entry
makefile.write_text(s)

cfgpath = src / "arch/arm64/configs/atoll_defconfig"
s = cfgpath.read_text()
for name, value in (("LOCALVERSION", '"-AY-Shadow-V6-A5-1"'),
                    ("AY_SHADOW_DEEPDOZE", "y"),
                    ("POWER_SUPPLY", "y")):
    pat = re.compile(rf"^(?:CONFIG_{name}=.*|# CONFIG_{name} is not set)$", re.M)
    if len(pat.findall(s)) > 1:
        sys.exit(f"Duplicate config key {name}")
    repl = f"CONFIG_{name}={value}"
    s = pat.sub(repl, s, count=1) if pat.search(s) else s.rstrip() + "\n" + repl + "\n"
cfgpath.write_text(s)
print("V6 Alpha5.1 panel-event kernel source patched: Qualcomm DSI screen bridge + automatic DeepDoze/InstantWake. DeepDoze, wake boost and touch boost start automatically at boot.")
