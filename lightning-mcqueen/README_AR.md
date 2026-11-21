# Lightning McQueen v1.1.0 — RMX2170

## Fixed target

- Device: Realme 7 Pro (RMX2170, Qualcomm SM7125 / atoll)
- ROM target: MelloDerp Android 14
- Kernel base: Linux 4.14.356
- Defconfig: arch/arm64/configs/atoll_defconfig
- Kernel release: 4.14.356-Lightning-McQueen-
- Source: crdroidandroid/android_kernel_realme_sm7125
- Source branch: 16.0
- Pinned source commit: 60f3427322632b19e8bc3e22731ecc7ce0baac25

The source is pinned to a specific commit so repeated builds use the same baseline rather than a moving branch head.

## Kernel configuration

- Retain the in-tree KernelSU Next integration, tag v1.1.1.
- Retain in-tree SUSFS v1.5.12.
- Enable CONFIG_KSU=y and CONFIG_KSU_SUSFS=y.
- Keep KernelSU debug output and SUSFS kernel logging disabled in the release configuration.
- Set schedutil rate limits to 500 µs up / 5000 µs down.
- Set WALT hispeed_load to 85%.
- Set hispeed_freq to 70% of each cpufreq policy's own maximum frequency.
- Initialize WALT defaults only when a fresh per-policy tunables object is allocated. The governor restore path continues to reinstate cached values, including values previously set by the Power HAL or userspace.

The hispeed value is a load-triggered floor, not a fixed CPU clock. It does not pin the processor at 70%, and the tunables remain adjustable by the platform power stack.

The OSM cpufreq driver in the pinned source declares CPUFREQ_HAVE_GOVERNOR_PER_POLICY, so the hispeed frequency default is calculated separately from each policy's maximum frequency.

## Build and package

The workflow is .github/workflows/lightning-mcqueen-rmx2170.yml.

A push to lightning-mcqueen-rmx2170-v1.1.0 runs the isolated GitHub Actions build:

1. Check out this pipeline and the pinned kernel source commit.
2. Verify the kernel version and all patch anchors without changing files.
3. Apply the source changes atomically and check the resulting diff.
4. Use the source repository's Clang r416183b and GCC 9.3 toolchains.
5. Compile Image.gz-dtb and create the AnyKernel3 ZIP.
6. Verify the kernel release, required .config options and ZIP integrity.
7. Upload the image, .config, logs, SHA-256 and AnyKernel ZIP as one workflow artifact.

The AnyKernel3 packaging source is the Realme 6 Pro / Realme 7 Pro variant. Its device check includes RMX2170, uses the A-only boot partition, and declares Android 12–17 support.

## Release boundary

A successful CI run confirms compilation and ZIP integrity, not physical-device boot or full hardware validation. Keep the package experimental until boot and the key device functions are confirmed on the RMX2170.

No voltage tables, thermal trip points, CPU hotplug rules, GPU clocks, ZRAM sizing or SELinux policy changes are included.
