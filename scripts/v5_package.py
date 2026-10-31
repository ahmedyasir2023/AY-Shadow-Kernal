#!/usr/bin/env python3
"""Package the RC2 compiled gzip with the EXACT fingerprint-working V4 DTB bundle.

The provided MelloDerp boot is a compatibility REFERENCE, not the DTB payload.
Do not replace V4 working panel/biometric DTBs with ROM stock counterparts.
"""
from pathlib import Path
import argparse
import hashlib
import re
import zipfile
import zlib
from package_recovery import digest, dtbs, rom_dtb

START = "# AY_SHADOW_DESIGNER_BEGIN"
BANNER = """# AY_SHADOW_DESIGNER_BEGIN
ui_print ' ';
ui_print '+==============================================+';
ui_print '|          A Y  S H A D O W  V 5               |';
ui_print '|             R C 2  EDITION                   |';
ui_print '|       ~*~  Eng. Ahmed Yasir  ~*~             |';
ui_print '|          Realme 7 Pro / RMX2170             |';
ui_print '+==============================================+';
ui_print '  KernelSU Next 3.4.2 | SUSFS 2.3.0';
# AY_SHADOW_DESIGNER_END
"""
def banner(script):
    script = script.replace("\r\n", "\n")
    for s in ("do.devicecheck=1", "supported.versions=14", "PATCH_VBMETA_FLAG=0",
              "Cannot verify Realme 7 Pro/RMX2170", "split_boot", "flash_boot",
              "backup_dir=/sdcard/AY-Shadow-Backups", "ro.boot.slot_suffix",
              "BLOCK=boot", "IS_SLOT_DEVICE=0"):
        if s not in script:
            raise ValueError("Unsafe V4 installer: missing " + s)
    if START in script:
        raise ValueError("Banner already installed")
    pat = re.compile(r"(?m)^([ \t]*\.[ \t]+tools/ak3-core\.sh;?[ \t]*)$")
    hits = list(pat.finditer(script))
    if len(hits) != 1:
        raise ValueError("AnyKernel core import missing or ambiguous")
    prop = re.compile(r"(?m)^kernel\.string=[^\n]*$")
    if len(prop.findall(script)) != 1:
        raise ValueError("kernel.string property missing or ambiguous")
    script = prop.sub("kernel.string=AY Shadow V5 RC2 by Eng. Ahmed Yasir", script)
    hit = list(pat.finditer(script))[0]
    script = script.replace("AY Shadow FP-Compat v4 Experimental",
                            "AY Shadow V5 RC2 - Eng. Ahmed Yasir")
    script = script.replace("AYShadow-FP-Compat-", "AYShadow-V5-RC2-")
    hit = list(pat.finditer(script))[0]
    return script[:hit.end()] + "\n" + BANNER + script[hit.end():]

def image_kernel(data):
    obj = zlib.decompressobj(31)
    obj.decompress(data)
    obj.flush()
    if not obj.eof or not obj.unused_data:
        raise ValueError("Invalid Image.gz-dtb")
    dtbs(obj.unused_data)
    return data[:-len(obj.unused_data)], dtbs(obj.unused_data)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("image", "rom-boot", "base-v4", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--trusted-v4-sha256", required=True)
    a = parser.parse_args()
    expected = a.trusted_v4_sha256.lower()
    if not re.fullmatch("[a-f0-9]{64}", expected):
        parser.error("Supply a trusted 64-hex SHA256 for a known working V4 ZIP")
    if a.base_v4.resolve() == a.output.resolve():
        parser.error("Output must not overwrite V4")
    if digest(a.base_v4.read_bytes()) != expected:
        raise ValueError("V4 ZIP checksum mismatch")
    kernel, compiled = image_kernel(a.image.read_bytes())
    original = rom_dtb(a.rom_boot)
    originals = {digest(x) for x in dtbs(original)}
    with zipfile.ZipFile(a.base_v4) as zin:
        if zin.testzip() is not None:
            raise ValueError("Damaged original ZIP")
        items = zin.infolist()
        names = [i.filename for i in items]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate paths in V4 ZIP")
        for item in items:
            if item.filename.startswith("/") or ".." in Path(item.filename).parts or "\\" in item.filename:
                raise ValueError("Unsafe ZIP member")
        for name in ("anykernel.sh", "zImage", "tools/ak3-core.sh"):
            if name not in names:
                raise ValueError("Missing V4 file " + name)
        old_kernel, working_dtbs = image_kernel(zin.read("zImage"))
        working_hashes = {digest(x) for x in working_dtbs}
        if len(working_hashes & originals) < 3:
            raise ValueError("V4 DTBs do not match the supplied MelloDerp ROM")
        if len(working_hashes & {digest(x) for x in compiled}) < 3:
            raise ValueError("Compiled kernel DTBs too different from working V4")
        if kernel == old_kernel:
            raise ValueError("Compiled gzip kernel identical to V4: no kernel change")
        # Keep all four working V4 FDTs byte-for-byte AND in their existing order.
        payload = kernel + b"".join(working_dtbs)
        script = banner(zin.read("anykernel.sh").decode("utf-8"))
        a.output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(a.output, "w") as zout:
            for item in items:
                data = payload if item.filename == "zImage" else script.encode() if item.filename == "anykernel.sh" else zin.read(item)
                zout.writestr(item, data)
            zout.writestr("AY-Shadow-V5-RC2-README.txt",
              "EXPERIMENTAL / Eng. Ahmed Yasir / RMX2170 Android 14.\n"
              "Backup Boot off-device and preserve working V4 recovery ZIP.\n"
              "Device boot/fingerprint/root tests not performed for RC2.\n"
              "Original V4 working DTBs retained; ROM boot used ONLY for verification.\n")
    with zipfile.ZipFile(a.output) as zipcheck:
        if zipcheck.testzip() is not None:
            raise ValueError("Output ZIP CRC invalid")
    print("EXPERIMENTAL ZIP:", a.output, "SHA256:", digest(a.output.read_bytes()))

if __name__ == "__main__":
    main()
