# V6 Alpha5.1 — Qualcomm DSI panel events, automatic DeepDoze repair

Observed on RMX2170 V6 Alpha5 AUTO after >10 minutes of screen off:
`enabled=1 delay_seconds=600 cap_percent=0 fb_events=0 wake_events=0 screen_on=1 deep_entries=0 restore_ms=-1 cap_applied=0`.
The fb notifier never reached AY Shadow, so the 600-second deadline was never armed.
`post_suspend=126` proves resumes happened, not that the DeepDoze cap worked.

## Implementation
- Pinned physical display uses `CONFIG_DRM_MSM_DSI_STAGING=y`. The tested
  Alpha5 AUTO .config lacks `CONFIG_MSM_DRM_NOTIFY`, so registering that
  notifier alone would NOT fix screen callbacks.
- Source patch touches only Qualcomm DSI panel enable and disable completion,
  guarded by exact pinned source structure. Calls `ay_shadow_panel_event`
  after releasing panel mutex. The callback queues CPUFreq policy adjustments;
  it does not directly set clocks or mask touch wake interrupts.
- Original FB notifier remains as fallback. New `panel_events` counter in
  read-only `/sys/kernel/ay_shadow/telemetry` proves actual DSI notifications.
- 600 BOOTTIME second delay, 0% above hardware floor, screen-ON immediate
  cap removal, 250ms WakeBoost and 700ms thermal-gated TouchBoost retained.
- Hardware fingerprint, DT2W, charger and thermal code untouched.

## No-install recommendation before QA
This is an **experimental repair candidate**, not yet validated on RMX2170.
Keep the known-booting Alpha5 AUTO as the recovery baseline. After CI success,
a strictly checked OrangeFox test package can be built from the exact new
kernel Image.gz-dtb and trusted original V5 display DTBs. Do NOT flash raw
GitHub Actions artifacts.

## Device acceptance
1. Verify boot, fingerprint, DT2W and charge.
2. Screen off/on twice: panel_events and wake_events must increment.
3. Leave display off 12–15 minutes; `deep_entries` should increase when
   work executes. Long true suspend may postpone the cap until resume.
4. `cap_applied` increases only when CPUFreq policy callbacks run in DeepDoze.
   It is not a direct measurement of instantaneous CPU clock while asleep.
5. Wake and verify restore_ms and screen_on=1, without a stuck cap.
6. Compare standby drain and temperature; source compile alone does not
   prove runtime power savings.

Reference: Linux CPUFreq https://docs.kernel.org/admin-guide/pm/cpufreq.html
