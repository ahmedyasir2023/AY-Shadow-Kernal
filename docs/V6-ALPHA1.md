# AY Shadow V6 — TITAN Alpha 1
Designed by **Eng. Ahmed Yasir**

**Device:** Realme 7 Pro RMX2170, MelloDerp Android 14.
**Compatibility baseline:** User-tested V5 RC2 boots with fingerprint and KernelSU Next/SUSFS.
**Status:** Experimental V6 KERNEL SOURCE; **not ready to flash**, not device-tested.

## Implemented in Linux 4.14.357 kernel source
- C driver in drivers/misc, built via CONFIG_AY_SHADOW_DEEPDOZE.
- FB_EARLY_EVENT_BLANK / FB_EVENT_BLANK display notifications trigger reversible state machine.
- Performance while display is on uses existing schedutil/WALT; no permanently maximum clock.
- Light Idle starts at screen off; DeepDoze after 600 seconds.
- CPUFREQ_ADJUST applies a real MAX-frequency ceiling, default 55% of hardware min-to-max interval, without raising thermal caps. Immediately clears its state on early-unblank, then schedules policy updates.
- system_freezable_wq timer does not wake Android out of suspend.
- Root-only sysfs: /sys/kernel/ay_shadow/{enabled,delay_seconds,cap_percent,state,telemetry}.
- Default runtime enabled=0 pending actual device framebuffer-event verification.
- V5 root, SUSFS, fingerprint drivers, thermal safety, Seccomp, ZRAM, FQ-CoDel retained.

## Hardware test steps after separate ZIP review
1. Backup the working V5 RC2 Boot off-device and confirm OrangeFox restore.
2. Boot V6 with DeepDoze DISABLED; test fingerprint, root, Wi-Fi, calls, camera, charging and ROM encryption.
3. With display turning off/on, check telemetry fb_events and screen_on=0/1. **If no events are seen, STOP: this DRM/display implementation may not dispatch FB notifiers.**
4. Only after reliable display-event testing: root echo 1 > /sys/kernel/ay_shadow/enabled. Let screen go off for >=10 min, then confirm deepdoze and instant restoration.
5. If anything fails, root echo 0 > /sys/kernel/ay_shadow/enabled or restore V5 Boot.
6. Compare frequency limits, suspend residency, alarms, notification latency and 4-hour idle battery drain versus V5.

## NOT implemented yet
GPU GameBoost, touch boost tuning, ZRAM policy change, charging control, Security Enforcing repair, GUI, root version upgrade. All need measured incremental work. No promise of 0% drain or automatic deep suspend when Android wakelocks are present.

References:
https://source.android.com/docs/core/power/platform_mgmt
https://docs.kernel.org/admin-guide/pm/cpufreq.html
