#!/system/bin/sh
# AY Shadow V6 Alpha4 / Eng. Ahmed Yasir
# READ-ONLY diagnostics for RMX2170, usable on known-working V5 or V6.
# Run inside Termux: su -c 'sh /sdcard/Download/v6_diagnostics.sh'
set -u
echo '=== AY Shadow V6 diagnostics (READ ONLY) ==='
if [ "$(id -u)" != "0" ]; then
  echo 'ERROR: run as root through KernelSU: su -c sh /path/to/v6_diagnostics.sh'
  exit 1
fi
echo '=== DEVICE ==='
getprop ro.product.device
getprop ro.build.version.release
cat /proc/version
echo '=== ROOT / SELINUX ==='
id
getenforce 2>&1
echo '=== V6 POWER ENGINE ==='
D=/sys/kernel/ay_shadow
if [ -d "$D" ]; then
  for key in state enabled delay_seconds cap_percent \
             wakeboost wakeboost_ms game_mode game_floor_percent \
             thermal_guard battery_temp_decic restore_ms deep_entries \
             game_denials screen_off_seconds post_suspend_count cap_applied telemetry; do
    if [ -r "$D/$key" ]; then
      printf '%s: ' "$key"
      cat "$D/$key" 2>&1
    else
      echo "$key: inaccessible"
    fi
  done
else
  echo 'V6 engine sysfs unavailable (expected on working V5).'
fi
echo '=== CPU POLICY READOUT ==='
for d in /sys/devices/system/cpu/cpufreq/policy*; do
  [ -d "$d" ] || continue
  echo "$d"
  for x in scaling_governor scaling_min_freq scaling_max_freq \
           cpuinfo_min_freq cpuinfo_max_freq scaling_cur_freq; do
    [ -r "$d/$x" ] && { printf '%s: ' "$x"; cat "$d/$x"; }
  done
done
echo '=== ZRAM ==='
cat /proc/swaps 2>&1
[ -r /sys/block/zram0/mm_stat ] && cat /sys/block/zram0/mm_stat
echo '=== BATTERY ==='
dumpsys battery 2>&1 | grep -E 'level:|temperature:|USB powered:|status:|health:'
echo '=== SUSPEND SUPPORT ==='
[ -r /sys/power/state ] && cat /sys/power/state
echo '=== FINISHED - NO SETTINGS CHANGED ==='
