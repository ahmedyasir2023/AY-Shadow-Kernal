#!/system/bin/sh
# AY Shadow V6 Alpha5.1 / Eng. Ahmed Yasir
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
             wakeboost wakeboost_ms touchboost touchboost_ms touchboost_floor_percent touch_events game_mode game_floor_percent \
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
echo '=== DOUBLE TAP TO WAKE (READ ONLY) ==='
for f in /proc/touchpanel/double_tap_enable /proc/touchpanel/gesture_enable; do
  if [ -r "$f" ]; then
    printf '%s: ' "$f"
    cat "$f"
  else
    echo "$f: unavailable"
  fi
done
echo '=== TOUCH IRQ / WAKE SOURCES ==='
grep -iE 'touch|novatek|nvt|tp' /proc/interrupts 2>/dev/null | head -n 20 || true
if [ -r /proc/wakeup_sources ]; then
  grep -iE 'touch|novatek|nvt|tp' /proc/wakeup_sources 2>/dev/null | head -n 20 || true
elif [ -r /sys/kernel/debug/wakeup_sources ]; then
  grep -iE 'touch|novatek|nvt|tp' /sys/kernel/debug/wakeup_sources 2>/dev/null | head -n 20 || true
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
