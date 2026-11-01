# AY Shadow V7 HyperSpeed — experimental, not yet tested on device

Target: Realme 7 Pro (RMX2170) running MelloDerp Android 14, Snapdragon 720G / atoll.

## Actual feature changes from V6 Alpha5.2
- **Adaptive input pipeline:** ordinary real touchscreen BTN_TOUCH press -> brief CPUFreq policy floor at 55% of the permitted frequency range for up to 800 ms. Rapid successive taps within 350 ms -> Turbo at 70% for up to 450 ms, only while battery temperature is below 37.5 C and the latest battery sample is fresh. This modifies policy **minimum**, does not overclock or bypass policy maximum, and may yield no gains if the governor was already fast enough.
- **Quick first interaction after screen-on:** Qualcomm DSI physical panel-on event immediately drops DeepDoze limit and requests a high-priority CPU policy refresh. WakeBoost default is a 40% floor for 400 ms. The DSI hardware timings themselves are **not** modified.
- **Thermal guard:** touch boosts stop at 40.0 C or when battery temperature cannot be read. The extra turbo stage stops at 37.5 C. All hardware thermal/governor maximums remain authoritative.
- **DeepDoze:** ten-minute screen-off BOOTTIME policy cap at the minimum hardware frequency, with no application exceptions, no wakeups created by this module, and automatic screen-on restoration.
- **App launch path:** opt-in one-shot ART compilation tool `scripts/v7_art_optimizer.sh` can compile an individual installed user app (`profile-one` or `full-one`) or explicitly requested `profile-all`. It checks battery temperature and remaining charge, and changes neither app data nor SELinux. This may help some app startups, uses disk space and CPU during compilation, and is not automatically run at boot.
- **Instrumentation:** sysfs `touch_turbo` root-writable toggle, `turbo_events` read-only count, `telemetry` `turbo_active`/`turbo_events`, alongside existing event/temperature/DeepDoze counters.

## Preservation and kernel release gates
- Pinned upstream Qualcomm kernel source commit 7306b28fccd87db72f25b314105747b1ce6f653c.
- Source-integrated KernelSU-Next 3.4.2 legacy / SUSFS 2.3.0 untouched; same Novatek native DT2W and Oppo optical fingerprint interfaces as working prior build.
- Boot installer must preserve four exact DTBs from the supplied working V6 Alpha5 AUTO AnyKernel3 ZIP, avoid DTBO/AVB modification, and enforce RMX2170 + installed Android 14 check.
- GitHub raw `Image.gz-dtb` **cannot** be flashed via recovery. Packaging does not validate hardware boot. Maintain an independent boot recovery image.
- Never represent a source build passing as proof of lower app-open latency, smoother UI, deeper suspend or power savings.

## On-device qualification
1. Check `cat /proc/version`, `su -c id`, `cat /sys/kernel/ay_shadow/telemetry`, `getprop ro.product.device`.
2. Test ordinary tap and rapid two-tap; verify `touch_events` and `turbo_events` increment; check that thermal guard disables boosts above threshold.
3. Screen OFF > 600 s, then test restoration plus fingerprint, DT2W, calls, alarms, charging and background notifications. Confirm `deep_entries` increases and screen event count is correct.
4. Compare median of at least 10 cold starts per app using `adb shell am start -W -S -n package/activity` across comparable thermal, battery, app-update, and ROM states. Exclude the first after ART compilation.
5. Profile idle battery drain, boot integrity, and any reboots over at least one day before declaring stable.

Artifacts are **experimental** until these checks are completed.
