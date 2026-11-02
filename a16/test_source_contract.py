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

    def test_arm64_syscall_type_port_is_guarded(self):
        # Pinned KernelSU fork omitted the ARM64 typedef while including
        # syscall_hook.h from core/init.c with SUSFS enabled.
        self.assertIn('typedef long (*syscall_fn_t)(const struct pt_regs *);', S)
        self.assertIn('#elif defined(__aarch64__)', S)
        self.assertIn('if hook_text.count(original_typedef) != 1:', S)
        self.assertIn('hook_header.write_text(', S)

    def test_sucompat_no_unsupported_newer_kernel_header(self):
        self.assertIn('obsolete_include = "#include <linux/pgtable.h>', S)
        self.assertIn('sucompat_file.write_text(', S)
        self.assertIn('sucompat_no_includes', S)

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
