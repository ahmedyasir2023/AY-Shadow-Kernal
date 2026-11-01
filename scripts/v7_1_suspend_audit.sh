#!/system/bin/sh
# AY Shadow V7.1: passive before/after suspend audit; never writes kernel controls.
set -u
B=/data/local/tmp/ay-shadow-v71-audit
S=/sys/power/suspend_stats
D=/sys/kernel/ay_shadow

[ "$(id -u)" -eq 0 ] || { echo "Root required"; exit 1; }

snapshot() {
  mkdir -p "$B" || exit 1
  chmod 0700 "$B"
  cat /proc/sys/kernel/random/boot_id > "$B/boot_id"
  for k in success fail failed_freeze failed_suspend; do
    cat "$S/$k" > "$B/$k" || exit 1
  done
  cat "$D/telemetry" > "$B/telemetry"
  cat /sys/class/power_supply/battery/capacity > "$B/capacity"
  if [ -r /proc/wakeup_sources ]; then
    awk 'NR>1 && $1!="" && $3 ~ /^[0-9]+$/ && $4 ~ /^[0-9]+$/ {
      e[$1]+=$3; w[$1]+=$4
    } END {for (n in e) print n, e[n], w[n]}' /proc/wakeup_sources > "$B/wakeup"
  fi
  echo "Saved baseline for this boot. Turn screen off for >=11 minutes."
}

report() {
  [ -r "$B/boot_id" ] || { echo "Run: sh v7_1_suspend_audit.sh before"; exit 2; }
  previous="$(cat "$B/boot_id")"
  current="$(cat /proc/sys/kernel/random/boot_id)"
  [ "$current" = "$previous" ] || {
    echo "Boot ID changed; cannot compare across reboot."; exit 3;
  }
  echo "=== SUSPEND DELTAS (same boot) ==="
  for k in success fail failed_freeze failed_suspend; do
    before="$(cat "$B/$k")"
    after="$(cat "$S/$k")"
    delta=$((after-before))
    [ "$delta" -ge 0 ] || { echo "Counters reset: $k"; exit 4; }
    printf '%s: before=%s after=%s change=%s\n' "$k" "$before" "$after" "$delta"
  done
  echo "=== BATTERY (percentage-points only) ==="
  printf 'before=%s after=%s\n' "$(cat "$B/capacity")" "$(cat /sys/class/power_supply/battery/capacity)"
  echo "=== KERNEL WAKEUP SOURCES (cumulative event changes) ==="
  if [ -r "$B/wakeup" ] && [ -r /proc/wakeup_sources ]; then
    awk 'NR==FNR {be[$1]=$2; bw[$1]=$3; next}
      NR>1 && $1!="" && $3 ~ /^[0-9]+$/ && $4 ~ /^[0-9]+$/ {
        e[$1]+=$3; w[$1]+=$4
      }
      END {
        for (n in e) {
          de=e[n]-be[n]; dw=w[n]-bw[n];
          if (de>0 || dw>0) printf "%-30s events_delta=%d wakeups_delta=%d\n", n, de, dw
        }
      }' "$B/wakeup" /proc/wakeup_sources
  else
    echo "No readable wakeup sources (not a kernel failure)"
  fi
  echo "=== LAST FAILURE (not necessarily a regression) ==="
  for k in last_failed_step last_failed_errno last_failed_dev; do
    printf '%s=' "$k"; cat "$S/$k"
  done
  echo "=== AY SHADOW ==="
  cat "$D/telemetry"
}

case "${1:-}" in
  before) snapshot ;;
  after) report ;;
  *) echo "Usage: su -c 'sh v7_1_suspend_audit.sh before|after'"; exit 2 ;;
esac
