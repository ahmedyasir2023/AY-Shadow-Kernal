# AY Shadow Kernal v3.0 — RMX2170 / MelloDerp Android 14
**State:** Experimental image successfully built; not yet boot-tested on an actual device.

## What was verified
- GitHub Actions run **41143706259** successfully compiled Linux 4.14.357, `Image.gz-dtb` from pinned ShadowBladeX mcqueen-ksu source.
- `CONFIG_LOCALVERSION="-AY-Shadow-Kernal"`, KernelSU Next, SUSFS, BBR and FQ enabled in the resolved kernel configuration.
- Original MelloDerp ROM boot.img is Android boot header **v2**, page size **4096**, separate DTB section, with **four device trees**.
- The compiled DTB set overlaps with the ROM by **three exactly matching DTB blobs**; the fourth atoll device tree differs in bytes. For a conservative first test, packaging uses the **original ROM DTB** rather than the compiled DTB blob.
- ZIP reuses the known-working v2.1 OrangeFox AnyKernel3 installer, preserving RMX2170, Android 14, and A-only safety checks. It flashes boot only. It attempts to save a copy of the currently installed boot image, but this may fail if recovery storage is inaccessible.
- Archive and installer syntax checks completed.

## Packaging
Run `python3 scripts/package_recovery.py --image <compiled Image.gz-dtb> --rom-boot <original MelloDerp boot.img> --base-flashable <v2.1 OrangeFox ZIP> --output AY-Shadow-v3-EXPERIMENTAL.zip`.

The MelloDerp ROM boot image and a known-working flashable installer must be **provided separately**. They are not bundled in the source repository.

**Not proven:** reliable boot on RMX2170, kernel module ABI, touchscreen, fingerprint, camera, radio/Wi-Fi, encryption, deep sleep, thermals, or KernelSU root behavior on a live device. A successful build/ZIP CRC check is NOT a hardware compatibility test.

**Before any first flash**, back up **your current** boot partition from OrangeFox to reliable storage and confirm you can restore it. Do not use the original ROM boot image as a replacement for a backup of your already-rooted kernel.

Sources: https://github.com/theshaenix/ShadowBladeX, https://github.com/theshaenix/AnyKernel3, https://github.com/mello-kernel/kernel_realme_sm7125.
