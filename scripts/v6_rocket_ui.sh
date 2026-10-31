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
    echo "Rocket UI enabled. App-specific animations are not removed."
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
    echo "Original animation values restored; wake boost disabled."
    ;;
  status)
    for key in window_animation_scale transition_animation_scale animator_duration_scale; do
      printf "%s: " "$key"
      settings get global "$key"
    done
    [ ! -r "$D/wakeboost" ] || { printf "wakeboost: "; cat "$D/wakeboost"; }
    ;;
  *) echo "Usage: sh v6_rocket_ui.sh on|off|status"; exit 2 ;;
esac
