#!/usr/bin/env python3
"""Require actual resolved Kconfig features and pinned, working NON-GKI root code."""
from pathlib import Path
import sys
if len(sys.argv) != 3:
    sys.exit("usage: v5_verify.py SOURCE_DIR OUT/.config")
src = Path(sys.argv[1])
cfg = {}
for line in Path(sys.argv[2]).read_text().splitlines():
    if line.startswith("CONFIG_") and "=" in line:
        k, v = line.split("=", 1)
        if k in cfg:
            sys.exit(f"Duplicate resolved config key: {k}")
        cfg[k] = v
required = {
    "CONFIG_LOCALVERSION": '"-AY-Shadow-V5-RC2"',
    "CONFIG_SECCOMP": "y", "CONFIG_SECCOMP_FILTER": "y",
    "CONFIG_KSU": "y", "CONFIG_KSU_SUSFS": "y",
    "CONFIG_SECURITY_SELINUX": "y",
    "CONFIG_OPPO_FINGERPRINT": "y", "CONFIG_OPPO_FINGERPRINT_FPC": "y",
    "CONFIG_OPPO_FINGERPRINT_GOODIX_OPTICAL": "y",
    "CONFIG_OPPO_FINGERPRINT_JIIOV_OPTICAL": "y",
    "CONFIG_CPU_BOOST": "y", "CONFIG_IRQ_SBALANCE": "y",
    "CONFIG_QTI_THERMAL_LIMITS_DCVS": "y",
    "CONFIG_HZ": "300", "CONFIG_HZ_300": "y",
    "CONFIG_TUN": "y", "CONFIG_NETFILTER": "y",
    "CONFIG_TCP_CONG_CUBIC": "y", "CONFIG_TCP_CONG_BBR": "y",
    "CONFIG_NET_SCH_FQ": "y",
    "CONFIG_TCP_CONG_WESTWOOD": "y", "CONFIG_NET_SCH_FQ_CODEL": "y",
    "CONFIG_ZRAM": "y", "CONFIG_ZRAM_MULTI_COMP": "y",
    "CONFIG_CRYPTO_LZ4": "y", "CONFIG_PSI": "y",
}
errors = [f"{k}: expected {v}, got {cfg.get(k)!r}" for k, v in required.items() if cfg.get(k) != v]
if "KSU_VERSION := 33355" not in (src / "drivers/kernelsu/Makefile").read_text():
    errors.append("KernelSU Next source is not vetted v3.4.2 / code 33355")
if 'SUSFS_VERSION "v2.3.0"' not in (src / "include/linux/susfs.h").read_text():
    errors.append("SUSFS source is not pinned v2.3.0 NON-GKI")
if errors:
    sys.exit("V5 RC2 Kconfig gate failed:\n" + "\n".join(errors))
print("V5 RC2 source gates PASS: root 33355, SUSFS 2.3.0, fingerprint, thermals, ZRAM,")
print("seccomp, FQ-CoDel and TCP Westwood. Runtime hardware compatibility NOT tested.")
