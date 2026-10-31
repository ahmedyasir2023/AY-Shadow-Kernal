#!/system/bin/sh
# AY Shadow V5 security/app crash triage. READ-ONLY; no root changes or policy toggles.
# Run as: adb shell sh /sdcard/Download/ay-shadow-v5-diagnostics.sh
OUT="/sdcard/Download/AY-Shadow-V5-Diagnostics.txt"
{
  echo "AY Shadow V5 diagnostic (read-only)"
  date
  echo "### OS/kernel"
  getprop ro.product.device
  getprop ro.build.version.sdk
  uname -a
  echo "### Security"
  getenforce 2>&1
  echo "Current shell Seccomp mode (not whole-device status):"
  grep '^Seccomp' /proc/self/status 2>&1
  echo "### Kernel feature config, when available"
  if [ -r /proc/config.gz ]; then
    gzip -dc /proc/config.gz 2>/dev/null | grep -E '^CONFIG_(SECCOMP|SECCOMP_FILTER|SECURITY_SELINUX|KSU|KSU_SUSFS)='
  fi
  echo "### Crash buffer: launch the failing app before collecting"
  logcat -d -b crash -v brief -t 300 2>&1
} > "$OUT"
echo "Saved $OUT"
echo "WARNING: crash logs may contain personal identifiers, server addresses or credentials; redact before sharing."
