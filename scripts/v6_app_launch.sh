#!/system/bin/sh
# AY Shadow V6 Rocket: opt-in AOT for ONE installed user app.
# Not a persistent daemon, no CPU governor changes, no cache deletion.
set -eu
[ "$(id -u)" = 0 ] || { echo "Error: root shell required"; exit 1; }
[ "$#" -eq 2 ] || {
  echo "Usage: sh v6_app_launch.sh profile|full|reset|status com.example.app"
  exit 2
}
mode="$1"
pkg="$2"
case "$pkg" in
  ""|.*|*..*|*.|*[!a-zA-Z0-9._]*)
    echo "Invalid Android package identifier"; exit 2 ;;
esac
if ! pm list packages -3 | grep -Fxq "package:$pkg"; then
  echo "Only installed user apps are supported; system packages are excluded."
  exit 3
fi
case "$mode" in
  profile|full)
    temp="$(cat /sys/class/power_supply/battery/temp 2>/dev/null || true)"
    case "$temp" in
      ""|*[!0-9]*) echo "Battery temperature not readable; compilation skipped."; exit 4 ;;
    esac
    [ "$temp" -lt 400 ] || {
      echo "Battery at or above 40 C: defer expensive compilation."; exit 4;
    }
    if [ "$mode" = profile ]; then
      echo "AOT speed-profile on $pkg (requires a populated app profile)."
      cmd package compile -m speed-profile -f "$pkg"
    else
      echo "Full AOT speed compile on $pkg (increases disk use; can take time)."
      cmd package compile -m speed -f "$pkg"
    fi
    ;;
  reset)
    echo "Restore Android ART compilation state for $pkg; app data unaffected."
    pm compile --reset "$pkg"
    ;;
  status)
    pm path "$pkg"
    echo "Read-only package check; no compilation performed."
    ;;
  *)
    echo "Usage: profile|full|reset|status"; exit 2 ;;
esac
