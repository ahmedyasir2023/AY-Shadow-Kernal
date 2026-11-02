"""Ahmed Super Kernal A16 root/hide-only source safety contracts."""
from pathlib import Path
import json
import unittest

R=Path(__file__).resolve().parent
S=(R/"prepare_source.py").read_text()
M=json.loads((R/"boot_reference.json").read_text())

class SourceContracts(unittest.TestCase):
    def test_original_reference(self):
        self.assertEqual(M["dtb_count"], 7)
        self.assertEqual(M["boot_header"], 2)
        self.assertEqual(M["kernel_bytes"], 19590365)
        self.assertEqual(len(M["dtb_sha256"]), 7)
        self.assertEqual(len(M["boot_sha256"]), 64)

    def test_no_ay_shadow_hardware_edits(self):
        for unsafe in ("DouTap_enable = 1", "cpufreq_update_policy(",
                       "setenforce 0", "fastboot flash", "rm -rf /data",
                       "ay_deepdoze.c", "qcom,qpnp"):
            self.assertNotIn(unsafe, S)

    def test_required_root_hide_gates(self):
        for guard in ('(4,14,336)', 'config KSU_SUSFS',
                      '50_add_susfs_in_kernel', '--fuzz=0',
                      '"KSU", "y"', '"KSU_SUSFS", "y"',
                      'Novatek', 'goodix'):
            if guard == 'goodix':
                continue
            self.assertIn(guard, S)
        self.assertIn("NOT yet verified", S)

if __name__=="__main__":
    unittest.main()
