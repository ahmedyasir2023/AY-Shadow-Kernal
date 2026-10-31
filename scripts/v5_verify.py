#!/usr/bin/env python3
"""Build gates for V5; confirms security config and v4 device integration are retained."""
from pathlib import Path
import sys
if len(sys.argv)!=3:
    sys.exit("usage: v5_verify.py SOURCE_DIR OUT/.config")
src=Path(sys.argv[1]); lines=Path(sys.argv[2]).read_text().splitlines()
cfg={k:v for k,v in (line.split("=",1) for line in lines if line.startswith("CONFIG_") and "=" in line)}
required={
  "CONFIG_LOCALVERSION":'"-AY-Shadow-V5-RC1"',
  "CONFIG_SECCOMP":"y",
  "CONFIG_SECCOMP_FILTER":"y",
  "CONFIG_KSU":"y",
  "CONFIG_KSU_SUSFS":"y",
  "CONFIG_SECURITY_SELINUX":"y",
  "CONFIG_OPPO_FINGERPRINT":"y",
  "CONFIG_OPPO_FINGERPRINT_FPC":"y",
  "CONFIG_OPPO_FINGERPRINT_GOODIX_OPTICAL":"y",
  "CONFIG_OPPO_FINGERPRINT_JIIOV_OPTICAL":"y",
  "CONFIG_CPU_BOOST":"y",
  "CONFIG_IRQ_SBALANCE":"y",
  "CONFIG_QTI_THERMAL_LIMITS_DCVS":"y",
  "CONFIG_HZ":"300",
  "CONFIG_HZ_300":"y",
  "CONFIG_TUN":"y",
  "CONFIG_NETFILTER":"y",
}
errors=[f"{k}: expected {v}, got {cfg.get(k)!r}" for k,v in required.items() if cfg.get(k)!=v]
if "KSU_VERSION := 33355" not in (src/"drivers/kernelsu/Makefile").read_text():
    errors.append("Expected pinned KernelSU Next 33355")
if 'SUSFS_VERSION "v2.3.0"' not in (src/"include/linux/susfs.h").read_text():
    errors.append("Expected pinned SUSFS 2.3.0")
if errors:
    sys.exit("V5 build verification FAILED:\n"+"\n".join(errors))
print("V5 RC1 Kconfig gates PASS: fingerprint and root retained; seccomp filter built-in.")
print("WARNING: does not validate runtime SELinux, per-process Seccomp, app compatibility or actual device fingerprint.")
