# AY Shadow Kernal V5 — RC1 security/compatibility engineering plan

**Device:** Realme 7 Pro RMX2170, MelloDerp Android 14.
**Stable fallback:** V4 fingerprint-compatible kernel, previously confirmed by the user to boot with both fingerprint and KernelSU Next root working.
**V5 status:** experimental kernel source branch; **not stable, not a ready-to-flash ZIP, and not tested on-device**.

## Exact software baseline (unchanged)
- ShadowBladeX Astra upstream pin: `7306b28fccd87db72f25b314105747b1ce6f653c`.
- Linux 4.14.357; same FPC/Goodix optical fingerprint source and four known-working DTBs used in V4's recovery package.
- KernelSU Next v3.4.2 legacy, kernel code 33355.
- SUSFS v2.3.0 (NON-GKI).
- 300Hz scheduling, CPU_BOOST, IRQ balancing, thermal guards.
- V4 SELinux behavior and runtime modules are NOT modified in V5 RC1.

## Changes in V5 RC1
1. Kernel name `-AY-Shadow-V5-RC1` in Kconfig (the runtime displayed string can still be overridden by a system component such as SUSFS; build Kconfig and release string are checked separately).
2. Explicit `CONFIG_SECCOMP=y` and `CONFIG_SECCOMP_FILTER=y`. This is an experimental security improvement to **test**, not a promise that the KernelSU app's "Seccomp: Disabled" indicator will change. The app or shell's reported Seccomp status is per-process; a supported kernel filter does not automatically put every process under a filter.
3. Build-time checks for root features, fingerprint, netfilter and TUN network support, SELinux, thermals and 300Hz/CPU_BOOST.
4. Read-only diagnostics tool `scripts/ay-shadow-v5-diagnostics.sh` captures basic runtime security and crash-buffer state. User must inspect/redact secrets and identifiers before sharing.

## Planned for later V5 milestones, not yet implemented
- Investigate SELinux Permissive origin (boot parameters, init/vendor sepolicy, or module). **Do not blindly force Enforcing:** that can break device initialization; review avc denials and policy first.
- Classify HTTP Injector startup crashes using actual `logcat -b crash`, then bisect Zygisk and OverlayFS module interference.
- Benchmarked CPU/GPU response profiles and reversible thermal-safe changes, avoiding overclock, undervolt and thermal-disable shortcuts.
- RAM/ZRAM and idle/battery tuning only after baseline energy/thermal measurements and repeated device tests.
- Validate Wi-Fi, Bluetooth, SIM, camera, fingerprint, charging, storage encryption, root authorization, and modules before release.

## Release gates
1. GitHub Actions builds `Image.gz-dtb`; verifies `CONFIG_SECCOMP_FILTER=y`, fingerprint, thermal and KernelSU options, and saves SHA256.
2. Human reviewer must confirm DTB packaging and working OrangeFox installer before creating ANY test-flashable ZIP. Artifact from GitHub Actions **must not be flashed directly**.
3. Back up current V4 Boot partition, preferably off-phone; preserve OrangeFox restore and V4 ZIP.
4. Physical-device smoke tests: full boot, existing fingerprint, new fingerprint enrollment without deleting templates, root, OverlayFS/MetaModule, Zygisk, phone calls, mobile data, Wi-Fi, camera, charging, SELinux, Seccomp filter behavior and app crash regressions.
5. Only after device testing: tag release; no automatic Stable label from CI.

## No claims about total root hiding
SUSFS support does not mean the root is undetectable. Integrity and per-app compatibility are separate concerns.

## Interpreting KernelSU's "Seccomp Disabled" accurately
The KernelSU Next Manager `Home.kt` code obtains this value with `Os.prctl(21,0,0,0,0)` (`PR_GET_SECCOMP`) from its own process, then labels `0` "Disabled", `1` "Strict", `2` "Filter". This does **not** report whether the kernel was built with `CONFIG_SECCOMP_FILTER=y`, and a fully functional kernel may still show "Disabled" for the Manager process. V5 enabling this Kconfig option is a separate experiment to supply optional filter capabilities; it is **not** a guaranteed way to change the Manager card or to fix app crashes.

Source (KernelSU Next code): https://github.com/KernelSU-Next/KernelSU-Next/blob/main/manager/app/src/main/java/com/rifsxd/ksunext/ui/screen/Home.kt
