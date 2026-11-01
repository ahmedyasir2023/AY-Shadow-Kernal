#!/system/bin/sh
# AY Shadow V7: explicit, one-shot ART optimization (not a background daemon).
# May use substantial storage/time. No data deletion, thermal or SELinux bypass.
set -u
[ "$(id -u)" = 0 ] || { echo "Root required"; exit 1; }
usage() { echo "Usage: sh v7_art_optimizer.sh profile-one|full-one PACKAGE | profile-all"; exit 2; }
[ "$#" -ge 1 ] || usage
mode="$1"
[ "$mode" = profile-all ] || [ "$#" = 2 ] || usage
valid_pkg() {
  case "$1" in ""|.*|*.|*..*|*[!a-zA-Z0-9._]*) return 1 ;; esac
  return 0
}
preflight() {
  t="$(cat /sys/class/power_supply/battery/temp 2>/dev/null || true)"
  level="$(cat /sys/class/power_supply/battery/capacity 2>/dev/null || true)"
  case "$t:$level" in *[!0-9:]*|:*|*:) echo "Battery status unavailable; stopped"; return 1 ;; esac
  [ "$t" -lt 390 ] && [ "$level" -ge 35 ] || { echo "Too warm or low battery; stopped"; return 1; }
}
compile_one() {
  pkg="$1"; method="$2"
  valid_pkg "$pkg" || { echo "Invalid package"; return 1; }
  pm list packages -3 | grep -Fxq "package:$pkg" || { echo "Not an installed user app: $pkg"; return 1; }
  preflight || return 1
  echo "Optimizing $pkg with $method (one-shot ART compile)"
  cmd package compile -m "$method" -f "$pkg"
}
case "$mode" in
  profile-one) [ "$#" = 2 ] || usage; compile_one "$2" speed-profile ;;
  full-one) [ "$#" = 2 ] || usage; compile_one "$2" speed ;;
  profile-all)
    [ "$#" = 1 ] || usage
    preflight || exit 4
    list="$(pm list packages -3)" || exit 4
    total=0; fail=0
    echo "$list" | while IFS= read -r entry; do
      pkg="${entry#package:}"
      [ "$pkg" != "$entry" ] || continue
      valid_pkg "$pkg" || continue
      preflight || exit 4
      echo "ART speed-profile: $pkg"
      cmd package compile -m speed-profile -f "$pkg" || echo "Compilation unavailable: $pkg"
    done
    ;;
  *) usage ;;
esac
