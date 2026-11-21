# Lightning McQueen RMX2170 v1.1.0

- Target: Realme 7 Pro (RMX2170), MelloDerp Android 14
- Kernel source: crdroidandroid/android_kernel_realme_sm7125, branch 16.0
- Base: Linux 4.14.356
- Defconfig: atoll_defconfig
- In-tree KernelSU Next: v1.1.1
- In-tree SUSFS: v1.5.12

The dedicated GitHub Actions workflow compiles the source and packages the AnyKernel ZIP. This file is intentionally committed to trigger the isolated build workflow.

A CI compile and package check do not establish physical-device boot compatibility. Keep the output experimental until separately confirmed on the RMX2170.
