# AY Shadow FP-Compat v4 — Experimental fingerprint-first kernel

**STATUS: ON-DEVICE TEST NOT PERFORMED.** Do not confuse a successful GitHub Actions build with a fingerprint fix.

## Known facts
- The original ShadowBladeX 4.14.356 kernel works with fingerprint and existing KernelSU Next 12802.
- AY Shadow v3 (Linux 4.14.357, built from `mcqueen-ksu`) boots, but fingerprint fails on RMX2170.
- DTB-only v3.1 comparison did not establish a fix. Changing the user data or persist partition is NOT an appropriate diagnostic method.
- A difference between v2.1 and v3 is not proof of causation by any single kernel option.

## New strategy
- Build from the pinned official ShadowBladeX **`astra-ksu`** branch, commit `7306b28fccd87db72f25b314105747b1ce6f653c`, NOT the earlier `mcqueen-ksu` branch.
- This upstream branch already contains **KernelSU Next v3.4.2 legacy (kernel code 33355)** and **SUSFS v2.3.0**. These are real source-code upgrades relative to the 12802/v1.5.9 kernel used in v2.1.
- The updated source has the same fingerprint driver tree objects as the known MelloDerp kernel source.
- Compile with optical/FPC fingerprint, 300Hz scheduling, CPU_BOOST, IRQ balancing, thermal limits, and SELinux support. No disabling of SELinux, device encryption, or thermal safety.
- Avoid cherry-picking wholesale config changes from the broken v3 branch. Other Astra code/config differences remain and hardware validation is still required.
- When packaging, use the precise four DTB blobs in the original working ShadowBladeX ZIP, preserving order. Do not flash a generic upstream AnyKernel installer that changes `fstab` or vendor partitions.

## Before first experiment
- Have OrangeFox, the known working v2.1 ZIP, and an **independently verified, current boot partition backup** from the phone. Copy the backup off-device.
- Experimental build may still fail to boot or break fingerprint.
- After boot, check: fingerprint unlock + enrolling a test template (without deleting existing templates), camera, Wi-Fi, mobile calls, display brightness, charging, SELinux, and KernelSU root.
- If ANY of these fail, restore the personally backed-up pre-flash Boot image. No Wipe Data.
- Use a normal **KernelSU Next v3.4.2 (33355)** manager APK only after successful boot / root detection and verification.

This branch intentionally does not publish a stable release or claim fingerprint repair before real-device validation.

## Verified compiler outcome — 2026-10-31
- GitHub Actions experimental branch build **41220748902** completed successfully.
- Source commit pinned to `7306b28fccd87db72f25b314105747b1ce6f653c`.
- Resolved kernel config contains `CONFIG_KSU=y`, `CONFIG_KSU_SUSFS=y`, optical/FPC fingerprint drivers, `CONFIG_HZ=300`, CPU boost, IRQ balancing, SELinux, thermal support.
- Build log explicitly reports KernelSU Next kernel code **33355** and SUSFS **v2.3.0**; no compiler errors.
- The separate OrangeFox test ZIP assembled outside GitHub uses original **working ShadowBladeX 4.14.356** DTBs in their exact original order (not generic upstream device trees).
- Test archive SHA256: `6d40e25c59b2f3cedd402156af285d6459d10737040b7e975414c67582b978fd`
- Test ZIP CRC and installation script syntax verified; neither guarantees the fingerprint will work or the phone will boot.
- The ZIP was provided in the ChatGPT conversation; GitHub Actions Artifact contains the raw kernel image/config/log, **NOT** a recovery flashable ZIP.
- **Actual phone fingerprint and boot tests remain pending. Never treat this as a validated fix until the user reports the results.**

GitHub Actions build link: https://github.com/ahmedyasir2023/AY-Shadow-Kernal/actions/runs/41220748902


## User hardware validation — October 31, 2026

**Tested on Realme 7 Pro / RMX2170 running MelloDerp Android 14**, based on user-reported result and screenshots:

| Check | Observed result |
|---|---|
| System boots | PASS (screenshots taken after boot) |
| Fingerprint | PASS — user explicitly confirms it works again |
| KernelSU root | PASS — user explicitly confirms root works; Manager shows Working, built-in (legacy) kernel v3.4.2 (33355) |
| SUSFS | Detected, supported v2.3.0 (NON-GKI) |
| Zygisk Next | Enabled, 1.5.2 |
| OverlayFS MetaModule | Detected, 1.3.1 |
| Kernel version shown | `4.14.357-g57525715` |
| KernelSU manager installed | v3.2.0 (33129), older than running kernel; recommend matching v3.4.2 manager |
| SELinux | Permissive — existing security concern, source unknown |
| CPU-Z 'Root Access' | No (not necessarily contradictory; CPU-Z may not have root authorization) |

**Scope of result:** This validates boot, reported fingerprint operation and reported root operation only. It does **not** demonstrate long-term stability, enforcing SELinux, battery or GPU gains, CTS/Play Integrity or compatibility with every module. No claim is made that root hiding defeats security checks.

**Release policy:** Keep this branch as a device-validated candidate, not a production-stable kernel until charging, camera, Wi-Fi, cellular, deep sleep, encryption and module tests are documented. Preserve the known-working Boot backup and previous kernel recovery ZIP.
