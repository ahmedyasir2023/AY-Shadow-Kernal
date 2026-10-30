#!/usr/bin/env python3
from pathlib import Path
import sys
if len(sys.argv) != 2: sys.exit("usage: verify_config.py .config")
cfg = dict(line.strip().split("=", 1) for line in Path(sys.argv[1]).read_text().splitlines() if line.startswith("CONFIG_") and "=" in line)
required = {
    "CONFIG_LOCALVERSION": '"-AY-Shadow-Kernal"',
    "CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE": "y",
    "CONFIG_TCP_CONG_BBR": "y",
    "CONFIG_NET_SCH_FQ": "y",
    "CONFIG_KSU": "y",
    "CONFIG_KSU_MANUAL_HOOK": "y",
    "CONFIG_KSU_SUSFS": "y",
    "CONFIG_ZRAM": "y",
    "CONFIG_DM_VERITY": "y",
    "CONFIG_SCHED_WALT": "y",
}
errors = [f"{k}: expected {v}, got {cfg.get(k)}" for k,v in required.items() if cfg.get(k) != v]
if errors: sys.exit("Invalid resolved kernel config:\n" + "\n".join(errors))
print("Resolved kernel config check passed (not a hardware compatibility check).")
