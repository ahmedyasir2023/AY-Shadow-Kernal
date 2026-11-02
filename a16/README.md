# Ahmed Super Kernal A16

Realme 7 Pro RMX2170 · EvolutionX-16.0-20261102-RMX2170 · Android 16 · **experimental source integration**

## Exact requested scope

**Only** KernelSU Next root and SUSFS hiding. Do not change the source touchscreen, Novatek gesture, optical fingerprint, CPU/GPU clocks, display, radio, charging, thermal, ramdisk, vendor or DTBO. No AY Shadow DeepDoze changes.

## Proven reference

User-provided Evolution X Android Boot v2: 64 MiB, 4 KiB page, compressed kernel Linux 4.14.336, 7 concatenated FDT/DTBs. Original Boot SHA-256: `4101a2db9a8fdc388f44a3ce4a23c14b2a856c5a902126513624b9c6c4db2653`.

## Candidate upstream (not yet reproducibly matched)

- Realme kernel: [realme-atoll/android_kernel_realme_sm7125 @ 10380039](https://github.com/realme-atoll/android_kernel_realme_sm7125/tree/10380039ddcd6ead841e1fc4ca744a2dd6e92fb8) — 4.14.336, atoll_defconfig with Novatek and optical fingerprint.
- KernelSU Next with SUSFS integration candidate: [pershoot/KernelSU-Next @ bea056e](https://github.com/pershoot/KernelSU-Next/tree/bea056e5637d15ddd6b0dc2013e8f2a7d98a9270), experimental fork based on KernelSU Next.
- SuSFS VFS source: [simonpunk/susfs4ksu kernel-4.14](https://gitlab.com/simonpunk/susfs4ksu/-/tree/kernel-4.14), commit prefix 77905b5a. This branch is old and **its patch may be incompatible**; do not declare integration successful until verified by patch and compilation.

## Release gates

1. Verify upstream Linux 4.14.336 and device drivers; abort on any mismatch.
2. Integrate KSU Next and all SUSFS kernel hooks, with a clean patch (no fuzz).
3. Resolve config and compile full ARM64 kernel; verify KSU=y, KSU_SUSFS=y, stock fingerprint & touch.
4. Verify 7 expected RMX2170 DTBs against original Boot; do not substitute four V7 DTBs.
5. Package safely using unchanged Evolution X ramdisk and safe installer checks.
6. On-device boot, KSU Next manager, SUSFS, optical fingerprint, DT2W, calls, battery and rollback tests.

**STATUS: source preparation only. NOT FLASHABLE.** Root/hiding are not currently installed on the user's phone. Root hiding cannot guarantee any app integrity verdict.

Source integration scripts are also available in the local Ahmed-Super-Kernal-A16 source pack; kernel-boot verification remains required.
