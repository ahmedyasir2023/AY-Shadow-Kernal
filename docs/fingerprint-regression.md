# Fingerprint regression on AY Shadow v3 (RMX2170)
Status: **open; cause not yet isolated**. Reported after successful boot of v3.0 on MelloDerp Android 14.

- Previous tested boot/kernel: ShadowBladeX 4.14.356 `-ShadowBladeX-TheNoah77-`.
- Current test boot/kernel: AY Shadow 4.14.357-openela `-AY-Shadow-Kernal`.
- Direct Git tree comparison: `drivers/input/oppo_fp_drivers` and `drivers/input/oppo_secure_common` source tree SHAs are IDENTICAL between `mello-kernel/kernel_realme_sm7125:roms` and `theshaenix/ShadowBladeX:mcqueen-ksu`. Fingerprint drivers did not disappear.
- Extracted `IKCONFIG` from both the known-working kernel zip and experimental v3 showed `CONFIG_OPPO_FINGERPRINT=y`, `CONFIG_OPPO_FINGERPRINT_GOODIX_OPTICAL=y`, `CONFIG_OPPO_FINGERPRINT_FPC=y`, `CONFIG_OPPO_FINGERPRINT_JIIOV_OPTICAL=y` in both.
- Real differences across configs include sched 300Hz vs 250Hz, CPU_BOOST, MEMCG, and kernel security/KernelSU hook integration. The precise cause remains **unproven**; these settings are not known to be the fingerprint failure.
- v3 used ShadowBladeX `mcqueen-ksu` source with different policy/config compared with the older shipping ShadowBladeX 4.14.356. Other kernel branches may be closer to the shipped kernel; do not blindly substitute drivers.
- The recovery package uses MelloDerp's original four DTB blobs.

**Recommended triage (safe order):**
1. Reboot once and check whether enrollment fails vs only unlocking.
2. Temporarily disable KernelSU modules and reboot; assess whether a module is interfering.
3. Restore a **known-working pre-v3 Boot backup** from OrangeFox, or reflash previous successful v2.1 kernel; no format data. Check whether fingerprint returns. If it fails on both kernels, investigate ROM/vendor/HAL and calibration, not only v3.
4. If returning to v3 for diagnosis, collect `dumpsys fingerprint`, filtered `logcat`, filtered `dmesg` via script; redact identifiers before sharing.
5. Only after confirming a v3-only regression, isolate config/commit changes, rebuild candidate and perform on-device validation. Do not call an untested patch a fix.

Do not disable SELinux or flash persist/vendor partitions as a speculative fingerprint repair.
