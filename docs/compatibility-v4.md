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
