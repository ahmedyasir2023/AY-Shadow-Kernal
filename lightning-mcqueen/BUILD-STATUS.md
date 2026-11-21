# Lightning McQueen RMX2170 v1.1.0

- Device: Realme 7 Pro (RMX2170)
- ROM target: MelloDerp Android 14
- Kernel source: crdroidandroid/android_kernel_realme_sm7125
- Source branch: 16.0
- Pinned source commit: 60f3427322632b19e8bc3e22731ecc7ce0baac25
- Linux base: 4.14.356
- KernelSU Next: v1.1.1
- SUSFS: v1.5.12

The CI checkout reference is pinned to the exact source commit. The build workflow performs a non-mutating patch preflight before applying any changes, then compiles and packages the kernel.

A successful compile and ZIP integrity check do not establish physical-device boot compatibility. Keep the package experimental until the RMX2170 boots and its core hardware functions are checked.
