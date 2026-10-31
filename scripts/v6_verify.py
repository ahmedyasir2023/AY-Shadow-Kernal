#!/usr/bin/env python3
"""Verify V6 configuration after resolving defconfig and root/fingerprint preservation."""
from pathlib import Path
import sys

if len(sys.argv) != 3:
    sys.exit("usage: v6_verify.py SOURCE_DIR OUT/.config")
src, path = Path(sys.argv[1]), Path(sys.argv[2])
config = dict(line.split("=", 1) for line in path.read_text().splitlines()
              if line.startswith("CONFIG_") and "=" in line)
required = {
    "CONFIG_LOCALVERSION": '"-AY-Shadow-V6-A3"',
    "CONFIG_AY_SHADOW_DEEPDOZE": "y", "CONFIG_FB_NOTIFY": "y",
    "CONFIG_POWER_SUPPLY": "y",
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
              "static bool ay_enabled;", "fb_unregister_client",
              "AY_WAKE_MS 250U", "AY_GAME_FLOOR 25U",
              "AY_BATTERY_LIMIT_DECI_C 400", "power_supply_get_by_name",
              "power_supply_put", "AY_BATTERY_SAMPLE_MS 5000U",
              "static bool ay_wake_enabled;", "static bool ay_game_enabled;",
              "static bool ay_inhibit;", "__ATTR(inhibit, 0600",
              "atomic_read(&ay_restore_ms)", "AY_BATTERY_SAMPLE_MS",
              "time_before(jiffies, READ_ONCE(ay_last_sample)"):
    if guard not in source:
        errors.append("Missing driver safety gate: " + guard)
if "KSU_VERSION := 33355" not in (src / "drivers/kernelsu/Makefile").read_text():
    errors.append("KernelSU source version changed unexpectedly")
if 'SUSFS_VERSION "v2.3.0"' not in (src / "include/linux/susfs.h").read_text():
    errors.append("SUSFS version changed unexpectedly")
if errors:
    sys.exit("V6 verification FAILED:\n" + "\n".join(errors))
print("V6 Alpha3 config PASS: DeepDoze, InstantWake, temperature-gated GameBoost, root, FP.")
print("Hardware behavior not validated: do not flash unreviewed raw kernel.")
