# AY Shadow V6 TITAN Alpha4 — Ultra DeepDoze
Eng. Ahmed Yasir | Realme 7 Pro RMX2170 | MelloDerp Android 14

## Approved behavior: NO application exceptions

1. While the screen is on, keep dynamic Performance (existing schedutil and optionally opt-in wake/game boosts).
2. Once screen is off for **600 real elapsed seconds**, apply the lowest **allowed** CPUFreq policy maximum: default cap_percent=0. No software/application exemptions for calls, navigation, music, downloads or messaging.
3. Remove all app-based bypass logic and the prior root-only inhibit control. No UID whitelist is implemented.
4. On screen unblank, immediately clear the UltraDoze state and queue frequency-policy restoration.
5. The BOOTTIME clock counts time during kernel suspend. A PM_POST_SUSPEND notifier rechecks the 10-minute deadline after waking. No extra alarm is set just to change frequency while the phone is suspended.
6. All experimental profiles remain disabled at boot until the actual RMX2170 screen notifier, fingerprint and unlock behavior are validated. This is a deliberate safety gate, not an app exemption.

## Kernel safety rules retained

No disabling Qualcomm thermal protection, battery safety, fingerprint drivers, power-button wakeup or hardware IRQs. A minimum CPU clock is not identical to suspension of applications, disabling wakelocks, or shutting down the modem. The kernel source alone does NOT guarantee that calls/alarms/background processes cease or that battery drain becomes zero. Truly changing Android DeviceIdle policy requires an independently audited system/privileged userspace component, not claimed in this stage.

Forcing heavy background tasks onto minimum CPU speed can prolong them and can worsen energy use; physical power measurements must determine whether UltraDoze actually saves power.

## Double-Tap-to-Wake — native RMX2170 path preserved

The pinned kernel source already contains the device's native Novatek NT36672C_NF touch gesture implementation for project 19721:
- Device tree declares `compatible = "novatek,nf_nt36672c"`, `black_gesture_support` and `new_set_irq_wake_support`.
- Defconfig must retain `CONFIG_TOUCHPANEL_NOVA=y`, `CONFIG_TOUCHPANEL_NOVA_NT36672C_NOFLASH=y` and `CONFIG_TOUCHPANEL_NEW_SET_IRQ_WAKE=y`.
- The Novatek driver recognizes `DTAP_DETECT` as `DouTap`; the common touch driver reports `KEY_DOUBLE_TAP`.
- The common suspend path uses `enable_irq_wake(ts->irq)` for the enabled gesture path. The V6 DeepDoze driver must never mask this IRQ, disable IRQ wake, power off the touch controller, or remove the device-tree gesture flags.
- UltraDoze only caps CPUFreq. The touch controller remains the low-power gesture detector and its IRQ is the hardware wake source; no app whitelist or continuously running CPU is needed.

**The ROM setting remains authoritative.** The upstream common driver initializes `DouTap_enable` to 0 and exposes `/proc/touchpanel/double_tap_enable`; the Android ROM/settings service is expected to enable it when the user turns on Double Tap to Wake. V6 deliberately does not force the proc value to 1 at boot, because that would override the user's setting and could increase idle drain.

The read-only Termux diagnostic prints `/proc/touchpanel/double_tap_enable`, `/proc/touchpanel/gesture_enable`, touch IRQ counts and matching wakeup sources when available.

**Required physical test:** turn on Double Tap to Wake in Android settings, verify the proc value is 1, turn the display off, wait beyond 10 minutes until UltraDoze is active, then double-tap the display. Confirm the screen wakes, fingerprint unlock works, and the V6 telemetry reports the screen-on transition. Repeat after natural suspend. This behavior is source-supported but not yet verified on the actual phone running V6.

## Available root-only settings on a future approved V6 kernel

- /sys/kernel/ay_shadow/enabled — opt-in UltraDoze (0 default)
- /sys/kernel/ay_shadow/delay_seconds — default 600, allowed 300..1800
- /sys/kernel/ay_shadow/cap_percent — default 0, allowed 0..95
- /sys/kernel/ay_shadow/state and telemetry — engine state and counters
- /sys/kernel/ay_shadow/screen_off_seconds — elapsed BOOTTIME seconds
- /sys/kernel/ay_shadow/post_suspend_count — PM resume events
- /sys/kernel/ay_shadow/cap_applied — CPU policy cap application count
- /sys/kernel/ay_shadow/wakeboost and game_mode — optional, only while display ON, both default OFF

## Test requirements
1. Retain off-device V5 RC2 boot backup and proven OrangeFox recovery method.
2. On actual V6 candidate boot, do NOT activate UltraDoze until events for both screen-off and screen-on reliably increment fb_events.
3. Verify fingerprint, wake button, root, modem, charging and battery temperature.
4. When opt-in UltraDoze is enabled, verify 10-minute wall elapsed transition, frequency cap, PM resume handling, immediate restore, then compare V5/V6 idle drain.
5. Disable via root if unstable; restore V5 if boot or unlock fails.

## Status
Code only; **NOT FLASHABLE** from GitHub Actions. Source compile and regression tests must pass; device tests not performed.

Linux CPUFreq: https://docs.kernel.org/admin-guide/pm/cpufreq.html
Android power: https://source.android.com/docs/core/power/platform_mgmt
