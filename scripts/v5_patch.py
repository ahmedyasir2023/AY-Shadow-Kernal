#!/usr/bin/env python3
"""V5 RC2 source configuration: extend V4-safe kernel without changing device policy."""
from pathlib import Path
import re
import subprocess
import sys

if len(sys.argv) != 2:
    sys.exit("usage: v5_patch.py SOURCE_DIR")
src = Path(sys.argv[1]).resolve()
subprocess.run([sys.executable, str(Path(__file__).with_name("compat_patch.py")), str(src)], check=True)
cfgpath = src / "arch/arm64/configs/atoll_defconfig"
config = cfgpath.read_text()

def set_cfg(key, value):
    global config
    pat = re.compile(rf"^(?:CONFIG_{key}=.*|# CONFIG_{key} is not set)$", re.M)
    if len(pat.findall(config)) > 1:
        sys.exit(f"Duplicate config key {key}")
    value = f"CONFIG_{key}={value}"
    config = pat.sub(value, config, count=1) if pat.search(config) else config.rstrip() + "\n" + value + "\n"

for path, symbol in (("net/sched/Kconfig", "NET_SCH_FQ_CODEL"), ("net/ipv4/Kconfig", "TCP_CONG_WESTWOOD")):
    if not re.search(rf"^config {symbol}$", (src / path).read_text(), re.M):
        sys.exit(f"Required optional networking feature missing: {symbol}")

set_cfg("LOCALVERSION", '"-AY-Shadow-V5-RC2"')
set_cfg("SECCOMP", "y")
set_cfg("SECCOMP_FILTER", "y")
# New optional algorithms built into the actual kernel, not made Android defaults.
set_cfg("NET_SCH_FQ_CODEL", "y")
set_cfg("TCP_CONG_WESTWOOD", "y")
cfgpath.write_text(config)
print("Applied RC2: new built-in FQ-CoDel + TCP Westwood; V4 fingerprint base preserved.")
