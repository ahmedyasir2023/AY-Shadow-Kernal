# AY Shadow Kernal v3.0 — RMX2170 (Android 14)

**Status: experimental source build, NOT validated for flashing.**

This repository provides a reproducible build pipeline for a **genuinely recompiled** Realme 7 Pro kernel, based on the [ShadowBladeX `mcqueen-ksu` branch](https://github.com/theshaenix/ShadowBladeX/tree/mcqueen-ksu), pinned to commit `3f464b55a3c34dc06efa04dbe58a48b349623098` (Linux 4.14.357).

Target ROM: `MelloDerp-14-Chapter4-uWu-RMX2170-20240302-0833`.

Changes planned in the compiled kernel:
- `CONFIG_LOCALVERSION="-AY-Shadow-Kernal"` so **uname** and KernelSU display the new name.
- Performance-oriented build option, instead of size optimization, using upstream settings.
- Compile TCP BBR and FQ as *optional* options (leave the Android default congestion controller intact).
- Retain existing KernelSU Next and SUSFS integration; retain SELinux, storage encryption, AVB and thermal drivers.

The stock Realme [Android Q source](https://github.com/realme-kernel-opensource/realme7pro_AndroidQ-kernel-source) is 4.14.117 and is not a direct substitute for this Android 14 ROM. The vendor device-tree, panel and dtb compatibility of newer ShadowBladeX with RMX2170 has **not** been confirmed by a successful boot test.

## How to build

Open [GitHub Actions](https://github.com/ahmedyasir2023/AY-Shadow-Kernal/actions) and inspect the workflow. A push to the main branch is configured to trigger its build; an explicit workflow dispatch is also available.

Output, on success: `Image.gz-dtb`, a generated Kconfig, build log and an **EXPERIMENTAL-UNTESTED** recovery package (never a production release).

**Do not flash this experimental package on your phone without reviewing DTB/boot compatibility and keeping a tested recovery method and a current copy of your existing boot image.** A successful GitHub Actions build does not verify hardware boot, camera, radio, fingerprint, root or charging.

Credits: Realme open-source kernel, MelloDerp project, ShadowBladeX, KernelSU Next, SUSFS, AnyKernel3 and their respective contributors. Keep their original licenses and notices when redistributing.
