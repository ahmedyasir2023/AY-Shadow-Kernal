# AY Shadow V6 TITAN Alpha 3 — Safety & telemetry
Designed by **Eng. Ahmed Yasir**. Target RMX2170 / MelloDerp Android 14.

## Implemented
This branch inherits Alpha2's real kernel-based opt-in DeepDoze, InstantWake and temperature-gated CPU GameBoost, and adds:

1. **Root-only inhibit flag** in /sys/kernel/ay_shadow/inhibit. When set to 1, it clears the active DeepDoze cap and cancels a pending timer. Setting back to 0 restores the original 10-minute deadline without waking Android just to change frequencies.
2. **Wake policy timing**: restore_ms measures the jiffies elapsed between a screen-unblank notification and completion of a scheduled CPUFreq policy refresh. This is NOT equal to screen-on latency or biometric unlock time. It is instrumentation for the immediate restore path.
3. **Thermal freshness guard**: GameBoost is not permitted when the last successful battery thermal sampling is older than 10 seconds. Any unavailable sensor or >=40 C disables the optional game floor. Existing Qualcomm thermal controls are never bypassed.
4. **Counters**: deep_entries, game_denials and expanded telemetry for real on-device testing.
5. **Read-only Termux diagnostics**: scripts/v6_diagnostics.sh reports current kernel, sysfs state, CPUFreq policies, SELinux, battery and ZRAM. Does not write to CPU or sysfs. Can also establish a V5 baseline.

## Alpha3 limitations / gates
- Neither V6 Alpha1 nor Alpha2 has been tested on the actual user's phone. Only the user-tested V5 RC2 boot/fingerprint/root is known good.
- Alpha3 defaults all experimental modes OFF at boot, including DeepDoze, InstantWake and GameBoost.
- Inhibit is an **interface**, not an automatic Android call/music/navigation detector. Android PowerHAL/privileged companion integration is future work; claiming automatic app exceptions without such integration would be incorrect.
- Only V5 has a tested recovery ZIP. CI Image.gz-dtb artifacts are NOT flashable. Before any V6 recovery ZIP, operator must verify identical working V5 fingerprint DTBs, AnyKernel installer, safe Boot backup/restore and ROM boot compatibility.
- Need physical on-device validation of FB notifier events, per-cluster policy maximum restoration, battery temp access, fingerprint, root, charging, modem, alarms, incoming calls and suspend residency.
- CPUFreq policy restore time below 100ms is an engineering TARGET requiring device verification, not a demonstrated result.
- SELinux Permissive issue is **not** fixed by this stage.

### Read-only Termux
Copy scripts/v6_diagnostics.sh to /sdcard/Download and run:

    su -c 'sh /sdcard/Download/v6_diagnostics.sh'

The script is safe to run on V5 and does not need a V6 flash.

### Relevant documentation
https://docs.kernel.org/admin-guide/pm/cpufreq.html
https://source.android.com/docs/core/power/platform_mgmt
