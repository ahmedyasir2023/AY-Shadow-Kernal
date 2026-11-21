#!/usr/bin/env python3
"""Apply the reviewed Lightning McQueen RMX2170 source changes."""
from pathlib import Path
import argparse
import sys

REPLACEMENTS = [
    (
        "arch/arm64/configs/atoll_defconfig",
        "CONFIG_SCHEDUTIL_UP_RATE_LIMIT=500\n",
        "CONFIG_SCHEDUTIL_UP_RATE_LIMIT=500\nCONFIG_SCHEDUTIL_DOWN_RATE_LIMIT=5000\n",
        "Keep the observed 500/5000 us schedutil policy explicit.",
    ),
    (
        "arch/arm64/configs/atoll_defconfig",
        "# KSU\nCONFIG_KSU_SUSFS=y",
        "# KSU\n"
        "CONFIG_KSU=y\n"
        "CONFIG_KSU_SUSFS=y\n"
        "# CONFIG_KSU_DEBUG is not set\n"
        "# CONFIG_KSU_SUSFS_ENABLE_LOG is not set",
        "Keep the in-tree KernelSU/SUSFS integration and disable release logging.",
    ),
    (
        "kernel/sched/cpufreq_schedutil.c",
        "#define NL_RATIO 75\n#define DEFAULT_HISPEED_LOAD 90\n",
        "#define NL_RATIO 75\n"
        "#define DEFAULT_HISPEED_LOAD 85\n"
        "#define DEFAULT_HISPEED_FREQ_PERCENT 70\n",
        "Set the RMX2170 WALT hispeed defaults.",
    ),
    (
        "kernel/sched/cpufreq_schedutil.c",
        "tunables->down_rate_limit_us =\n"
        "\t\t\t\tCONFIG_SCHEDUTIL_DOWN_RATE_LIMIT;\n"
        "#ifdef CONFIG_SCHED_KAIR_GLUE\n",
        "tunables->down_rate_limit_us =\n"
        "\t\t\t\tCONFIG_SCHEDUTIL_DOWN_RATE_LIMIT;\n"
        "\t/* Lightning McQueen RMX2170: moderate WALT high-load floor. */\n"
        "\ttunables->hispeed_load = DEFAULT_HISPEED_LOAD;\n"
        "\ttunables->hispeed_freq = mult_frac(policy->cpuinfo.max_freq,\n"
        "\t\t\t\t\t   DEFAULT_HISPEED_FREQ_PERCENT, 100);\n"
        "#ifdef CONFIG_SCHED_KAIR_GLUE\n",
        "Use 70% of each cpufreq policy maximum after WALT load reaches 85%.",
    ),
    (
        "build.sh",
        'VERSION_NUMBER="v1.0.1"',
        'VERSION_NUMBER="v1.1.0"',
        "Label the AnyKernel package v1.1.0.",
    ),
]

def apply_one(root: Path, rel: str, old: str, new: str, description: str) -> str:
    path = root / rel
    if not path.is_file():
        raise RuntimeError(f"Required source file is missing: {rel}")
    data = path.read_text(encoding="utf-8")
    if new in data:
        return f"ALREADY APPLIED: {rel} — {description}"
    count = data.count(old)
    if count != 1:
        raise RuntimeError(
            f"Refusing to patch {rel}: expected exactly one anchor, found {count}. "
            "The source tree may not match the approved 16.0 branch."
        )
    path.write_text(data.replace(old, new, 1), encoding="utf-8")
    return f"APPLIED: {rel} — {description}"

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Kernel source root")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    makefile = root / "Makefile"
    defconfig = root / "arch/arm64/configs/atoll_defconfig"

    if not makefile.is_file() or not defconfig.is_file():
        print("ERROR: not a kernel source root with atoll_defconfig.", file=sys.stderr)
        return 2

    mk = makefile.read_text(encoding="utf-8", errors="replace")
    if "VERSION = 4\nPATCHLEVEL = 14\nSUBLEVEL = 356\n" not in mk:
        print("ERROR: expected Linux 4.14.356 source; refusing to patch.", file=sys.stderr)
        return 2

    cfg = defconfig.read_text(encoding="utf-8", errors="replace")
    if 'CONFIG_LOCALVERSION="-Lightning-McQueen-"' not in cfg:
        print("ERROR: Lightning McQueen localversion not found.", file=sys.stderr)
        return 2

    try:
        for rel, old, new, description in REPLACEMENTS:
            print(apply_one(root, rel, old, new, description))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    print("\nPatch application complete.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
