#!/system/bin/sh
# AY Shadow Kernal fingerprint diagnostics: READ ONLY
OUT="${1:-/sdcard/Download/AY-Shadow-Fingerprint-Diagnostics.txt}"
mkdir -p "$(dirname "$OUT")" || exit 1
{
  echo 'AY Shadow Kernal fingerprint diagnostic'
  date
  echo '=== Kernel/device ==='
  getprop ro.product.model
  getprop ro.product.device
  getprop ro.build.version.release
  uname -a
  getenforce 2>&1
  echo '=== Fingerprint services ==='
  service list 2>&1 | grep -iE 'fingerprint|biometric' | head -30
  echo '=== Fingerprint HAL ==='
  dumpsys fingerprint 2>&1 | head -100
  echo '=== Fingerprint properties ==='
  getprop | grep -iE 'fingerprint|goodix|fpc|biometric' | head -40
  echo '=== Recent fingerprint logs ==='
  logcat -d -t 16000 -v brief 2>&1 | grep -iE 'fingerprint|goodix|fpc|oppo_fp|udfps|hwservicemanager.*biometric' | tail -150
  echo '=== Kernel messages ==='
  if [ "$(id -u)" = 0 ]; then
    dmesg 2>&1 | grep -iE 'fingerprint|goodix|fpc|oppo_fp|udfps' | tail -120
  fi
} > "$OUT"
echo "Saved: $OUT"
echo 'Review and redact personal/device identifiers before sharing.'
