# AY Shadow V5 RC2 — Eng. Ahmed Yasir

Target: Realme 7 Pro RMX2170, MelloDerp Android 14. Status: EXPERIMENTAL.

## Concrete differences from V5 RC1
- Linux source Kconfig: optional built-in TCP Westwood and FQ-CoDel scheduling. Default Android congestion control and qdisc are unchanged, so performance uplift is not claimed without measurements.
- Installer: V4 AnyKernel-based recovery packager with ASCII designer banner:
  ~*~ Eng. Ahmed Yasir ~*~
- Packaging guards: independent SHA256 check of working V4 ZIP, ROM boot DTB verification, device/Android 14 installer checks, CRC test. The exact four fingerprint-working V4 DTBs are retained; the ROM boot is used only as a compatibility reference.
- Verified existing KernelSU Next v3.4.2 code 33355 + SUSFS 2.3.0 NON-GKI, the current official stable upstream; no incompatible GKI module or speculative upgrade.
- Build Kconfig tests preserve thermal, fingerprint, SELinux, ZRAM/LZ4 and root support.

## Build and packaging
CI builds a SOURCE-ONLY Image.gz-dtb, NOT a flashable ZIP.
To package locally, after the operator verifies the exact working V4 ZIP checksum and has the matching MelloDerp boot.img:

    python3 scripts/v5_package.py \
      --image dist/v5/AY-Shadow-V5-RC2-EXPERIMENTAL-Image.gz-dtb \
      --rom-boot /path/to/MelloDerp-boot.img \
      --base-v4 /path/to/KNOWN-WORKING-V4.zip \
      --trusted-v4-sha256 <verified_64_hex_sha256> \
      --output /path/to/AY-Shadow-V5-RC2-TEST.zip

Verified user-uploaded original V4 ZIP SHA256: `6d40e25c59b2f3cedd402156af285d6459d10737040b7e975414c67582b978fd`. The supplied ROM boot DTBs differ from V4 in one out of four blobs; using stock ROM DTBs as a replacement is therefore an avoidable fingerprint regression risk.\n\nKeep an off-phone Boot backup, OrangeFox restore and working V4 ZIP.
The ZIP is a test candidate, not stable, and must not be flashed before human review of the exact base installer.
Test boot, fingerprint, KernelSU authorizations, Wi-Fi, radio, camera, charger, encryption, Zygisk, SELinux and thermal throttling.
No persist/vendor modifications, no thermal disabling, no Play Integrity bypass claims.

Root manager (normal Android APK, not recovery):
https://github.com/KernelSU-Next/KernelSU-Next/releases/download/v3.4.2/KernelSU_Next_v3.4.2_33355-release.apk

Technical limitation: BBR, FQ, ZRAM, multi-compression and LZ4 were already present in the pinned upstream. New network options extend choice, not measured speed.
