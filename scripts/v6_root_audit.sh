#!/system/bin/sh
# AY Shadow V6 — read-only compatibility audit for V5/V6.
# No spoofing, netlink probes, configuration writes, or privilege escalation.
set -u

say() { printf '%s\n' "$1"; }
read_one() {
  label="$1"; path="$2"
  printf '%s: ' "$label"
  if [ -r "$path" ]; then
    head -n 1 "$path" 2>/dev/null || echo unavailable
  else
    echo unavailable
  fi
}
property() { printf '%s: %s\n' "$1" "$(getprop "$1" 2>/dev/null)"; }

say '=== AY SHADOW ROOT / APP COMPATIBILITY (READ ONLY) ==='
say '=== SYSTEM ==='
property ro.product.device
property ro.build.version.release
property ro.build.version.sdk
say '=== KERNEL IDENTITY (ALL SOURCES) ==='
native_release="$(uname -r 2>/dev/null || true)"
proc_release="$(cat /proc/sys/kernel/osrelease 2>/dev/null || true)"
native_build="$(uname -v 2>/dev/null || true)"
proc_build="$(cat /proc/sys/kernel/version 2>/dev/null || true)"
printf 'uname -r: %s\n' "$native_release"
printf '/proc/sys/kernel/osrelease: %s\n' "$proc_release"
printf 'uname -v: %s\n' "$native_build"
printf '/proc/sys/kernel/version: %s\n' "$proc_build"
read_one '/proc/version' /proc/version
if [ -n "$native_release" ] && [ -n "$proc_release" ] &&
   [ "$native_release" != "$proc_release" ]; then
  say 'CHECK: KERNEL RELEASE MISMATCH (review modules and kernel patches)'
else
  say 'CHECK: no observable kernel release mismatch'
fi
if [ -n "$native_build" ] && [ -n "$proc_build" ] &&
   [ "$native_build" != "$proc_build" ]; then
  say 'CHECK: KERNEL BUILD MISMATCH (review modules and kernel patches)'
else
  say 'CHECK: no observable kernel build mismatch'
fi
say '=== BOOT PROPERTY SIGNALS (NOT HARDWARE ATTESTATION) ==='
property ro.boot.flash.locked
property ro.boot.vbmeta.device_state
property ro.boot.verifiedbootstate
say '=== SELINUX ==='
getenforce 2>/dev/null || echo unavailable
say '=== KERNEL FEATURES ==='
[ -r /proc/config.gz ] && echo '/proc/config.gz readable' || echo '/proc/config.gz unavailable'
[ -d /sys/kernel/ay_shadow ] && echo 'AY V6 sysfs present' || echo 'AY V6 sysfs absent (normal on V5)'
say '=== SUSFS MODULE STATUS (NAMES ONLY; IF ROOT) ==='
if [ "$(id -u)" = 0 ]; then
  found=0
  for d in /data/adb/modules/*; do
    [ -d "$d" ] || continue
    case "${d##*/}" in
      *[Ss][Uu][Ss][Ff][Ss]*|*[Zz][Yy][Gg][Ii][Ss][Kk]*|*[Ll][Ss][Pp][Oo][Ss][Ee][Dd]*)
        printf 'module folder: %s\n' "${d##*/}"
        if [ -e "$d/disable" ]; then echo 'module disabled'; else echo 'module not marked disabled'; fi
        found=1 ;;
    esac
  done
  [ "$found" -eq 1 ] || say 'No matching module folder names (not proof of absence)'
else
  say 'Run as root to inspect module names; no root required for other checks'
fi
say '=== INTERPRETATION ==='
say 'Kernel uname differences are consistency evidence, not proof of malware.'
say 'Boot properties cannot substitute for TEE/Play Integrity attestation.'
say 'This tool never attempts to bypass app security checks.'
say '=== DONE ==='
