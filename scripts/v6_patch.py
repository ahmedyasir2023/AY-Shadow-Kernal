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
for name, value in (("LOCALVERSION", '"-AY-Shadow-V6-A5-AUTO"'),
                    ("AY_SHADOW_DEEPDOZE", "y"),
                    ("POWER_SUPPLY", "y")):
    pat = re.compile(rf"^(?:CONFIG_{name}=.*|# CONFIG_{name} is not set)$", re.M)
    if len(pat.findall(s)) > 1:
        sys.exit(f"Duplicate config key {name}")
    repl = f"CONFIG_{name}={value}"
    s = pat.sub(repl, s, count=1) if pat.search(s) else s.rstrip() + "\n" + repl + "\n"
cfgpath.write_text(s)
print("V6 Alpha5 AUTO kernel source patched: DeepDoze + InstantWake + thermal-gated GameBoost. DeepDoze, wake boost and touch boost start automatically at boot.")
