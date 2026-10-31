# AY Shadow V6 TITAN Alpha 2
Designed by Eng. Ahmed Yasir. Target: Realme 7 Pro RMX2170, MelloDerp Android 14.

## New kernel code (not configuration-only)
The existing V6 Alpha1 C driver now implements:
- **InstantWake**: opt-in CPUFreq minimum floor for the first 250ms after a display-unblank event. It is cleared by a delayed work item. Default OFF until phone tests. Adjustable 100–500 ms.
- **GameBoost**: opt-in CPUFreq minimum floor for screen-on use, defaults to 25% of available hardware min/max range. Adjustable 10–35%. Default OFF.
- **ThermalGuard**: GameBoost works only while battery temperature can be read from the battery power-supply API and is below 40.0 C; sampling runs every 5 seconds only while gaming with the display on. Unknown/unreadable temperature disables boost (fail closed). Qualcomm thermal restrictions remain authoritative, not replaced or disabled.
- **DeepDoze**: the existing 600-second screen-off delayed CPUFreq ceiling and early unblank restore remain intact. Also OFF until physical verification.
- **Telemetry**: screen events, wake events, wakeboost, game mode, thermal gate, last battery temperature, number of samples.

Root-only sysfs files on the running V6 kernel are expected at /sys/kernel/ay_shadow/:
enabled, delay_seconds, cap_percent, state, telemetry,
wakeboost, wakeboost_ms, game_mode, game_floor_percent,
battery_temp_decic, thermal_guard.

## Validation conditions
Before any V6 flash, keep a VERIFIED working V5 RC2 Boot backup off the phone. Image.gz-dtb from CI is NOT flashable and cannot be safely substituted for the ROM boot image.

When a separate recovery ZIP is reviewed and device-tested:
1. Boot with enabled=0, wakeboost=0 and game_mode=0; verify fingerprint, charging, modem, camera, decryption and root.
2. Check that actual screen off and on update fb_events. If not, no feature should be enabled: the real ROM may not emit FB notifications.
3. Compare battery_temp_decic with Android dumpsys battery. A missing battery sensor must leave thermal_guard=0.
4. Validate InstantWake first: enable wakeboost only, verify boost expires and existing frequency/governor returns. Measure screen unlock latency and battery impact.
5. Validate GameBoost separately, check battery temperature sensor and Qualcomm GPU/CPU thermal throttling under real gaming load. Confirm auto-off on screen off and temp >=40.0 C.
6. Enable DeepDoze last after fingerprint and background call/alarm tests, measuring suspend residency and idle drain relative to V5.
7. Disable all three modes or restore V5 immediately if a regression occurs.

## Scope honesty
This is a real in-kernel CPUFreq change, not an Android APK, but it is not a GPU overclock, a proven FPS increase, or a device-validated battery improvement. Further SmartThermal CPU/GPU temperature integration, Control Center GUI and SELinux repair are still future phases.

Design: power_supply_get_by_name plus power_supply_put is supported by the pinned ShadowBladeX source. The game boost never directly alters thermal policy or charging limits.
