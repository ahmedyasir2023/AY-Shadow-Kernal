import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from v5_package import banner, START
BASE = """properties() { '
kernel.string=Existing V4
do.devicecheck=1
supported.versions=14
'; }
PATCH_VBMETA_FLAG=0
echo "Cannot verify Realme 7 Pro/RMX2170"
. tools/ak3-core.sh;
split_boot;
flash_boot;
"""
class RecoveryTests(unittest.TestCase):
    def test_branding(self):
        result = banner(BASE)
        self.assertIn("Eng. Ahmed Yasir", result)
        self.assertLess(result.index(". tools/ak3-core.sh"),result.index(START))
        self.assertLess(result.index(START),result.index("split_boot"))
        self.assertIn("kernel.string=AY Shadow V5 RC2",result)
    def test_reject_unsafe(self):
        with self.assertRaises(ValueError):
            banner(BASE.replace("do.devicecheck=1","do.devicecheck=0"))
    def test_recovery_banner_keeps_backup(self):
        result = banner(BASE)
        self.assertIn("backup_dir=/sdcard/AY-Shadow-Backups", result)
        self.assertIn("ro.boot.slot_suffix", result)
    def test_reject_repeat(self):
        with self.assertRaises(ValueError):
            banner(banner(BASE))
if __name__ == "__main__":
    unittest.main()
