# Lightning McQueen v1.1.0 — RMX2170

This directory contains an isolated build configuration for the Realme 7 Pro (RMX2170).

## Fixed build target
- ROM: MelloDerp Android 14
- Kernel source: crdroidandroid/android_kernel_realme_sm7125
- Branch: 16.0
- Linux base: 4.14.356
- Defconfig: arch/arm64/configs/atoll_defconfig
- Kernel localversion: -Lightning-McQueen-

This build is kept separate from the AY Shadow Kernal project and its ShadowBladeX 4.14.357 source.

## Source changes
- Retain the in-tree KernelSU Next v1.1.1 and SUSFS v1.5.12 integration.
- Explicitly enable CONFIG_KSU=y and CONFIG_KSU_SUSFS=y.
- Disable KernelSU debug output and SUSFS kernel logging for release.
- Preserve the observed schedutil rate limits: 500 µs up / 5000 µs down.
- Set WALT hispeed_load to 85%.
- Set hispeed_freq to 70% of each cpufreq policy's maximum. The OSM cpufreq driver supports per-policy tunables, so little and big clusters receive independent thresholds.
- Label the AnyKernel package v1.1.0.

The hispeed threshold is a load-triggered floor, not a permanent frequency lock. The tunables remain writable by the platform power HAL.

## Build
A push to branch lightning-mcqueen-rmx2170-v1.1.0 starts the dedicated GitHub Actions workflow.

The workflow checks out this isolated configuration and the approved kernel source, applies the patch idempotently, uses the source repository's own build script and toolchain versions, verifies the generated config and ZIP, then uploads the AnyKernel package, image, config, logs and SHA-256 manifest.

## Release boundary
A successful CI build confirms compilation and package integrity only. It does not prove physical-device boot or validate camera, modem, Wi-Fi, Bluetooth, fingerprint, charging or thermal behavior. Keep the package experimental until those are established.

No voltage, thermal trip, CPU hotplug, GPU clock, ZRAM-size or SELinux-policy changes are included.
