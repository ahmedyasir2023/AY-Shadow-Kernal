#!/usr/bin/env python3
"""Apply the reviewed Lightning McQueen RMX2170 source changes atomically."""
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
        "Enable the in-tree KernelSU/SUSFS integration without release debug logging.",
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
        "\tif (tunables) {\n"
        "\t\tgov_attr_set_init(&tunables->attr_set, &sg_policy->tunables_hook);\n",
        "\tif (tunables) {\n"
        "\t\t/*\n"
        "\t\t * Apply defaults only to fresh tunables. The restore path in\n"
        "\t\t * sugov_init() retains cached Power HAL/user values on restart.\n"
        "\t\t */\n"
        "\t\ttunables->hispeed_load = DEFAULT_HISPEED_LOAD;\n"
        "\t\ttunables->hispeed_freq = mult_frac(\n"
        "\t\t\tsg_policy->policy->cpuinfo.max_freq,\n"
        "\t\t\tDEFAULT_HISPEED_FREQ_PERCENT, 100);\n"
        "\t\tgov_attr_set_init(&tunables->attr_set, &sg_policy->tunables_hook);\n",
        "Initialize a 70%-of-policy-max floor for fresh tunables only.",
    ),
    (
        "build.sh",
        "#!/bin/bash\n",
        "#!/bin/bash\nset -euo pipefail\n",
        "Fail immediately on missing toolchains and build/packaging errors.",
    ),
    (
        "build.sh",
        "  2>&1 | tee out/build.log | grep --line-buffered -E \"warning:|error:\" | sed \\\n"
        "  -e 's/warning:/\\x1b[1;33mwarning:\\x1b[0m/g' \\\n"
        "  -e 's/error:/\\x1b[1;31merror:\\x1b[0m/g'\n",
        "  2>&1 | tee out/build.log\n",
        "Preserve the real compiler exit status while retaining the full build log.",
    ),
    (
        "build.sh",
        'VERSION_NUMBER="v1.0.1"',
        'VERSION_NUMBER="v1.1.0"',
        "Label the AnyKernel package v1.1.0.",
    ),
]


def stage_changes(root: Path):
    staged = {}
    changed = set()
    messages = []

    for rel, old, new, description in REPLACEMENTS:
        path = root / rel
        if not path.is_file():
            raise RuntimeError(f"Required source file is missing: {rel}")

        data = staged.get(rel)
        if data is None:
            data = path.read_text(encoding="utf-8")

        if new in data:
            messages.append(f"ALREADY APPLIED: {rel} — {description}")
            staged[rel] = data
            continue

        count = data.count(old)
        if count != 1:
            raise RuntimeError(
                f"Refusing to patch {rel}: expected exactly one anchor, found {count}. "
                "The source tree may not match the pinned RMX2170 baseline."
            )

        staged[rel] = data.replace(old, new, 1)
        changed.add(rel)
        messages.append(f"READY TO APPLY: {rel} — {description}")

    return staged, changed, messages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Kernel source root")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate every source anchor without modifying files",
    )
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
        staged, changed, messages = stage_changes(root)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3

    for message in messages:
        print(message)

    if args.check:
        print("\nPreflight passed; no files were modified.")
        return 0

    for rel in sorted(changed):
        (root / rel).write_text(staged[rel], encoding="utf-8")

    print("\nPatch application complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
