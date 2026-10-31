#!/usr/bin/env python3
"""V5 RC1: patch the known-working v4 configuration, without changing fingerprint sources.
This introduces a CONFIG_SECCOMP_FILTER experiment.  It is NOT an automatic SELinux fix.
"""
from pathlib import Path
import re
import subprocess
import sys

if len(sys.argv)!=2:
    sys.exit("usage: v5_patch.py SOURCE_DIR")
src=Path(sys.argv[1]).resolve()
subprocess.run([sys.executable,str(Path(__file__).with_name("compat_patch.py")),str(src)],check=True)
path=src/"arch/arm64/configs/atoll_defconfig"
s=path.read_text()
def set_cfg(k,v):
    global s
    pat=re.compile(rf"^(?:CONFIG_{k}=.*|# CONFIG_{k} is not set)$",re.M)
    if len(pat.findall(s))>1:
        sys.exit(f"Duplicate Kconfig key: {k}")
    value=f"CONFIG_{k}={v}"
    s=pat.sub(value,s,count=1) if pat.search(s) else s.rstrip()+"\n"+value+"\n"
# Keep original governor/clock/thermal/fingerprint settings from the user's working v4.
set_cfg("LOCALVERSION",'"-AY-Shadow-V5-RC1"')
set_cfg("SECCOMP","y")
set_cfg("SECCOMP_FILTER","y")
# Do not touch SELinux runtime mode or system policy; gather device logs before changing.
path.write_text(s)
print("Applied V5 RC1 seccomp-filter option and kernel branding to v4-compatible config.")
