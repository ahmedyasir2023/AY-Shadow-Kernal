#!/usr/bin/env python3
"""Apply minimal auditable source changes to a pinned Linux 4.14.357 tree."""
from pathlib import Path
import re
import sys
import difflib

if len(sys.argv) != 2:
    sys.exit("usage: apply.py SOURCE_DIRECTORY")
root = Path(sys.argv[1])
makefile = (root / "Makefile").read_text()
for key, value in (("VERSION", "4"), ("PATCHLEVEL", "14"), ("SUBLEVEL", "357")):
    if not re.search(r"^" + key + r"\s*=\s*" + value + r"\s*$", makefile, re.M):
        sys.exit("Wrong upstream kernel: expected Linux 4.14.357")
for filename, marker in (("drivers/kernelsu/Kconfig", "config KSU_SUSFS"),
                         ("fs/Makefile", "CONFIG_KSU_SUSFS")):
    if marker not in (root / filename).read_text():
        sys.exit("Missing KernelSU Next/SUSFS source integration: " + filename)

def set_cfg(s, key, value):
    pat = re.compile(r"^(?:CONFIG_" + re.escape(key) + r"=.*|# CONFIG_" +
                     re.escape(key) + r" is not set)$", re.M)
    lines = pat.findall(s)
    if len(lines) > 1:
        sys.exit("Duplicate Kconfig value: " + key)
    replacement = "CONFIG_" + key + "=" + value
    if lines:
        return pat.sub(replacement, s, count=1)
    return s.rstrip("\n") + "\n" + replacement + "\n"

changes = {
    "LOCALVERSION": '"-AY-Shadow-Kernal"',
    # Source Makefile defaults to -O3 when CONFIG_CC_OPTIMIZE_FOR_SIZE is not y.
    "TCP_CONG_ADVANCED": "y",
    "TCP_CONG_BBR": "y",
    "NET_SCH_FQ": "y",
    "KSU": "y",
    "KSU_MANUAL_HOOK": "y",
    "KSU_SUSFS": "y",
}
reportdir = Path("reports")
reportdir.mkdir(exist_ok=True)
for path in (root / "arch/arm64/configs/atoll_defconfig",
             root / "arch/arm64/configs/vendor/atoll_defconfig",
             root / "arch/arm64/configs/vendor/atoll-perf_defconfig"):
    name = path.name
    old = path.read_text()
    new = old
    for key, value in changes.items():
        new = set_cfg(new, key, value)
    new = re.sub(r"^CONFIG_CC_OPTIMIZE_FOR_SIZE=y$", "# CONFIG_CC_OPTIMIZE_FOR_SIZE is not set", new, flags=re.M)
    (reportdir / ((("primary-" if path.parent.name == "configs" else "vendor-") + name) + ".diff")).write_text("".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile="upstream/"+name, tofile="AY-Shadow/"+name)))
    path.write_text(new)
    print("Patched", path)
