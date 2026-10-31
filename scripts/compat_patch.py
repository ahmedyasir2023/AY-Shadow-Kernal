#!/usr/bin/env python3
"""Apply narrowly scoped fingerprint-compat patches to pinned ShadowBladeX Astra source.
Do not modify fingerprint drivers, board DTBs, thermal protections or selinux behavior.
"""
from pathlib import Path
import re
import sys

if len(sys.argv) != 2:
    sys.exit("usage: compat_patch.py kernel_source")
source = Path(sys.argv[1])
mk = (source / "Makefile").read_text()
for k, v in [("VERSION","4"),("PATCHLEVEL","14"),("SUBLEVEL","357")]:
    if not re.search(rf"^{k}\s*=\s*{v}\s*$", mk, re.M):
        sys.exit(f"Unexpected upstream kernel {k}")
files = ["drivers/kernelsu/Makefile", "include/linux/susfs.h",
         "drivers/input/oppo_fp_drivers/Makefile"]
for name in files:
    if not (source/name).is_file():
        sys.exit("Missing expected source: " + name)
ksu = (source/files[0]).read_text()
susfs = (source/files[1]).read_text()
if "KSU_VERSION := 33355" not in ksu or 'SUSFS_VERSION "v2.3.0"' not in susfs:
    sys.exit("Unexpected KernelSU Next / SUSFS versions. Re-review source pin.")
cfgpath = source / "arch/arm64/configs/atoll_defconfig"
config = cfgpath.read_text()
def config_set(key,value):
    global config
    pat = re.compile(rf"^(?:CONFIG_{key}=.*|# CONFIG_{key} is not set)$", re.M)
    matches = pat.findall(config)
    if len(matches)>1:
        sys.exit(f"Duplicate config key: {key}")
    replacement = f"CONFIG_{key}={value}"
    config = pat.sub(replacement,config,count=1) if matches else config.rstrip()+"\n"+replacement+"\n"

# Fingerprint support and scheduling align with the previously working kernel.
# Preserve upstream thermal guards, source drivers and SELinux policy.
options={
    "LOCALVERSION":'"-AY-Shadow-FP-Compat"',
    "KSU":"y",
    "KSU_SUSFS":"y",
    "OPPO_FINGERPRINT":"y",
    "OPPO_FINGERPRINT_FPC":"y",
    "OPPO_FINGERPRINT_QCOM":"y",
    "OPPO_FINGERPRINT_GOODIX_OPTICAL":"y",
    "OPPO_FINGERPRINT_JIIOV_OPTICAL":"y",
    "CPU_BOOST":"y",
    "IRQ_SBALANCE":"y",
    "QTI_THERMAL_LIMITS_DCVS":"y",
    "HZ_300":"y",
    "HZ":"300",
}
for k,v in options.items():
    config_set(k,v)
# A different Hz option may otherwise override the intended timer frequency.
for k in ("HZ_100","HZ_250","HZ_1000"):
    pat = re.compile(rf"^CONFIG_{k}=y$",re.M)
    config=pat.sub(f"# CONFIG_{k} is not set",config)
cfgpath.write_text(config)
print("Fingerprint-compatible source variant configured.")
