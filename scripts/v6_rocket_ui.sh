#!/system/bin/sh
# AY Shadow V6 Rocket UI: reversible Android animation controls.
# The kernel is not responsible for Android's window animations.
set -eu
[ "$(id -u)" = 0 ] || { echo "Root required"; exit 1; }
B=/data/local/tmp/ay_shadow_rocket
D=/sys/kernel/ay_shadow
mkdir -p "$B"
chmod 700 "$B"
case "${1:-}" in
  on)
    for key in window_animation_scale transition_animation_scale animator_duration_scale; do
      [ -f "$B/$key" ] || settings get global "$key" > "$B/$key"
      settings put global "$key" 0
    done
    # Existing bounded 250 ms wake boost; no unlimited CPU frequency.
    [ ! -w "$D/wakeboost" ] || echo 1 > "$D/wakeboost"
    # Optional CPU-frequency floor on each BTN_TOUCH; battery guard in kernel.
    [ ! -w "$D/touchboost" ] || echo 1 > "$D/touchboost"
    echo "Rocket UI ON. TouchBoost is available only on Alpha5 kernel, with thermal guard."
    ;;
  off)
    for key in window_animation_scale transition_animation_scale animator_duration_scale; do
      if [ -f "$B/$key" ]; then
        old="$(cat "$B/$key")"
        if [ "$old" = null ]; then
          settings delete global "$key"
        else
          settings put global "$key" "$old"
        fi
        rm -f "$B/$key"
      fi
    done
    [ ! -w "$D/wakeboost" ] || echo 0 > "$D/wakeboost"
    [ ! -w "$D/touchboost" ] || echo 0 > "$D/touchboost"
    echo "Animations restored; both optional CPU boosts disabled."
    ;;
  status)
    for key in window_animation_scale transition_animation_scale animator_duration_scale; do
      printf "%s: " "$key"
      settings get global "$key"
    done
    for key in wakeboost touchboost touchboost_ms touchboost_floor_percent touch_events; do
      [ ! -r "$D/$key" ] || { printf "%s: " "$key"; cat "$D/$key"; }
    done
    ;;
  *) echo "Usage: sh v6_rocket_ui.sh on|off|status"; exit 2 ;;
esac
