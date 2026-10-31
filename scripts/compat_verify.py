#!/usr/bin/env python3
"""Verify fingerprint-compat build config and actual baked-in root stack."""
from pathlib import Path
import sys
if len(sys.argv)!=3:
    sys.exit("usage: compat_verify.py source_dir out/.config")
src=Path(sys.argv[1]); path=Path(sys.argv[2])
rows=path.read_text().splitlines()
cfg=dict(s.split("=",1) for s in rows if s.startswith("CONFIG_") and "=" in s)
required={
 "CONFIG_LOCALVERSION": '"-AY-Shadow-FP-Compat"',
 "CONFIG_KSU":"y","CONFIG_KSU_SUSFS":"y",
 "CONFIG_OPPO_FINGERPRINT":"y",
 "CONFIG_OPPO_FINGERPRINT_FPC":"y",
 "CONFIG_OPPO_FINGERPRINT_QCOM":"y",
 "CONFIG_OPPO_FINGERPRINT_GOODIX_OPTICAL":"y",
 "CONFIG_OPPO_FINGERPRINT_JIIOV_OPTICAL":"y",
 "CONFIG_CPU_BOOST":"y",
 "CONFIG_IRQ_SBALANCE":"y",
 "CONFIG_QTI_THERMAL_LIMITS_DCVS":"y",
 "CONFIG_HZ":"300","CONFIG_HZ_300":"y",
 "CONFIG_SECURITY_SELINUX":"y",
}
errors=[f"{k}: expected {v}, actual {cfg.get(k)}" for k,v in required.items() if cfg.get(k)!=v]
if errors:
    sys.exit("Compatibility Kconfig verification failed:\n"+"\n".join(errors))
if "KSU_VERSION := 33355" not in (src/"drivers/kernelsu/Makefile").read_text():
    sys.exit("KernelSU Next version is not v3.4.2 legacy")
if 'SUSFS_VERSION "v2.3.0"' not in (src/"include/linux/susfs.h").read_text():
    sys.exit("SUSFS version mismatch")
print("Verified original fingerprint drivers/config present and newer root stack.")
