# AY Shadow V6 TITAN Alpha5 — Rocket Launch (experimental)
Realme 7 Pro RMX2170 / Android 14 / Eng. Ahmed Yasir

## Actual implementation
1. **700ms bounded touch-to-launch CPU floor** when `BTN_TOUCH` is pressed
   on the existing Novatek `touchpanel` input device. The floor defaults to
   30% above the hardware policy minimum within the device's CPUFreq range.
   The CPU max remains governed by existing policy and Qualcomm thermals.
   Input events are subscribed only after enabling root-only
   `/sys/kernel/ay_shadow/touchboost=1`; runtime default remains OFF until
   physical validation. No background polling and no wakelock.
2. **Fail-closed thermal guard:** before applying the touch floor require
   a recent battery reading under 40.0 C; thermal sampler runs only while
   display ON and touchboost/game mode enabled.
3. **Android zero animations**, entirely user-space. The reversible
   `scripts/v6_rocket_ui.sh on|off` preserves original window, transition
   and animator scales, optionally enabling both bounded WakeBoost and
   TouchBoost on an approved V6 kernel. No launcher or GPU overclock.
4. **Per-app ART ahead-of-time compilation**, user opt-in via
   `scripts/v6_app_launch.sh` on a single installed non-system package.
   Android 14 ART Service handles dexopt. First choose speed-profile; if
   insufficient profile data, full speed compiles more code but costs
   disk and compile time. Compilation requires battery below 40.0 C.
   Avoid doing this while playing or under low battery; no global all-app
   compile, no cache clearing, no persistent app monitoring.
5. **Native double tap immediately after boot:** separate patch defaults
   `DouTap_enable=1` in the original Novatek common driver. It does not
   bypass Android's first PIN unlock, bootloader, or recovery.
6. **UltraDoze unchanged:** after 600 real elapsed seconds screen OFF,
   no app exemption, minimum allowed CPUFreq cap; display wake clears it.
   Original fingerprint, touchscreen wake IRQ, thermal, KSU/SUSFS intact.
7. **Root detection notes only:** see V6-ROOT-COMPATIBILITY.md. Never
   misrepresent a failed TEE/Play Integrity attestation as passed.

## Controls
After installing and validating an appropriate V6 test boot:
```sh
su -c 'sh /sdcard/Download/v6_rocket_ui.sh on'
su -c 'sh /sdcard/Download/v6_rocket_ui.sh off'
```

For individual apps, even on V5 (requires `su`):
```sh
su -c 'sh /sdcard/Download/v6_app_launch.sh profile com.example.app'
su -c 'sh /sdcard/Download/v6_app_launch.sh full com.example.app'
su -c 'sh /sdcard/Download/v6_app_launch.sh reset com.example.app'
```
Replace `com.example.app` with a real third-party package name.
The full mode is more demanding and may consume substantial storage.

## Hardware acceptance
- GitHub source compile success is not a flash test.
- Verify screen-on/off event sequence and double-tap after 10 minutes.
- Measure app cold/warm launches 10 times and P50/P90, compare to V5 RC2.
- Record battery temp, thermal throttling, input latency, app stability,
  overnight drain, and power-button/fingerprint functionality.
- Keep verified V5 RC2 boot/OrangeFox recovery backup.
- Do not flash a raw Actions `Image.gz-dtb` as if it were a flashable ZIP.

## Official Android docs
- https://source.android.com/docs/core/runtime/jit-compiler
- https://source.android.com/docs/core/runtime/configure/art-service
- https://docs.kernel.org/admin-guide/pm/cpufreq.html
