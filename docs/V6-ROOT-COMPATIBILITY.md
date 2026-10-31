# V6 TITAN — Root/app compatibility audit (V5 RC2 baseline)

Status: read-only audit committed to Alpha5; **no kernel-side root concealment patch** and
no claim of banking/DRM app compatibility. Do not merge or flash until real device tests.

## Duck Detector baseline (realme 7 Pro RMX2170, Android 14, 2026-11-01)
- Overall 6 danger, 2 warning, 18 ready.
- **Strongest actionable kernel signal:** uname() and System.getProperty("os.version")
  returned `4.14.357-g47510416`, but `/proc/sys/kernel/osrelease` and
  `/proc/version` returned `4.14.357-AY-Shadow-V5-RC2`.
  `uname -v` and `/proc/sys/kernel/version` also differed.
  Determine whether SUSFS spoof_uname userspace configuration, a kernel UTS hook,
  or another component causes this before modifying V6.
- Key attestation failed and no certificate chain was available. Locked/green
  Android *properties* are not proof of a hardware-verified boot chain.
- LSPosed detection: 3 installed modules and an unexpected INTERNET GID verdict;
  direct Xposed bridge/class/map probes were clean. Do not conflate modules
  installed with proven live injection.
- Network boundary issues: AF_NETLINK RTM_GETLINK/RTM_GETNEIGH returned sensitive
  network information to an untrusted app. Audit ROM policy and kernel
  backports against appropriate Android API/targetSdk behavior. Do not simply
  enable permissive SELinux or filter the scanner.
- Virtualization flag relied on qemu_hw_prop property-area mapping, not proof of
  an emulated CPU. TEE 'TAMPERED' was assigned despite an unavailable attestation
  chain: treat as unresolved until verified by authoritative tests.
- SU, Zygisk, mounting, memory and root manager detections were clean in
  the sampled app context, not proof that the whole device is stock.

## Compatibility goals for V6
1. Reproducible **kernel identity across interfaces**; prefer removing unintended
   overrides rather than injecting synthetic uname values.
2. Enforcing SELinux and least-privilege per-app root permissions; never
   add blanket app exceptions or broad allow policies.
3. No tampering with Android Verified Boot, KeyMint/TEE attestation, or
   server-side Play Integrity verdicts. Genuine certification may require
   restoring the full OEM image and a legitimately locked bootloader.
   **Do not relock a custom ROM/kernel:** risk of boot failure or data wipe.
4. Keep V5-proven fingerprint and DT2W paths, V6 DeepDoze thermal/wake safety.
5. Collect real application launch/compatibility logs, without sensitive tokens.
   Check the target app's own compatibility requirements before modifying kernel.

## Read-only on-device diagnosis
```sh
su -c 'sh /sdcard/Download/v6_root_audit.sh'
```
Compare with the Duck Detector report before and after optional module changes.
The script does not make changes. On V5 it is safe to run from a root shell.
Do not upload logs containing network identifiers, private file paths or secrets.

## References
- https://source.android.com/docs/security/features/keystore/attestation
- https://source.android.com/docs/security/features/verifiedboot/boot-flow
- https://developer.android.com/google/play/integrity/verdicts
- https://kernelsu.org/guide/app-profile.html
- https://github.com/sidex15/susfs4ksu-module/wiki
