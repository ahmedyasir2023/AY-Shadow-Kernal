#!/usr/bin/env python3
"""Fail closed if required A16 root/hide or hardware configs were lost."""
from pathlib import Path
import re, sys
cfg=Path(sys.argv[1]).read_text()
wanted=[
 'CONFIG_KSU=y',
 'CONFIG_KSU_SUSFS=y',
 'CONFIG_LOCALVERSION="-Ahmed-Super-Kernal-A16"',
 'CONFIG_KPROBES=y',
 'CONFIG_OPPO_FINGERPRINT=y',
 'CONFIG_OPPO_FINGERPRINT_GOODIX_OPTICAL=y',
 'CONFIG_TOUCHPANEL_NOVA=y',
 'CONFIG_TOUCHPANEL_NOVA_NT36672C_NOFLASH=y',
]
bad=[x for x in wanted if not re.search("^"+re.escape(x)+"$",cfg,re.M)]
if bad:
 raise SystemExit("A16 KCONFIG VERIFICATION FAILED:\n"+"\n".join(bad))
print("Required A16 KSU+SUSFS and untouched hardware config flags verified")
