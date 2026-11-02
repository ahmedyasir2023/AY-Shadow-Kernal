#!/usr/bin/env python3
"""Ahmed Super Kernal A16. Integrate root/hide only, fail closed."""
from pathlib import Path
import argparse, os, re, shutil, subprocess

def fail(message):
    raise SystemExit("A16 PORT BLOCKED: " + message)

def putcfg(text, name, value):
    pat = re.compile(r"^(?:CONFIG_" + re.escape(name) +
                     r"=.*|# CONFIG_" + re.escape(name) + r" is not set)$", re.M)
    lines = pat.findall(text)
    if len(lines) > 1:
        fail("Duplicate Kconfig key: " + name)
    replacement = "CONFIG_" + name + "=" + value
    return pat.sub(replacement, text) if lines else text.rstrip() + "\n" + replacement + "\n"

p = argparse.ArgumentParser()
p.add_argument("--src", type=Path, required=True)
p.add_argument("--ksu", type=Path, required=True)
p.add_argument("--susfs", type=Path, required=True)
a = p.parse_args()
src, ksu, susfs = (path.resolve() for path in (a.src, a.ksu, a.susfs))
m = (src / "Makefile").read_text()
v = tuple(int(re.search(r"^" + x + r"\s*=\s*(\d+)", m, re.M).group(1))
          for x in ("VERSION", "PATCHLEVEL", "SUBLEVEL"))
if v != (4,14,336):
    fail("Expected EXACT Linux 4.14.336; got " + str(v))
cfg = src / "arch/arm64/configs/atoll_defconfig"
tp = src / "drivers/input/touchscreen/oppo_touchscreen/touchpanel_common_driver.c"
nvt = src / "drivers/input/touchscreen/oppo_touchscreen/Novatek"
if not cfg.is_file() or not tp.is_file() or not nvt.is_dir():
    fail("Missing protected atoll/Novatek hardware source")
kc = ksu / "kernel/Kconfig"
if not kc.is_file() or "config KSU_SUSFS\n" not in kc.read_text():
    fail("SUSFS-capable KernelSU Next source required")
# KernelSU Next dev-susfs ARM64 non-GKI compatibility. Its header declares
# syscall_fn_t for x86_64/RISC-V, but not AArch64. The syscall table hooks
# are disabled by CONFIG_KSU_SUSFS; this declaration is still parsed by
# core/init.c and must have the correct ARM64 pt_regs signature.
hook_header = ksu / "kernel/hook/syscall_hook.h"
hook_text = hook_header.read_text()
original_typedef = ("#if defined(__x86_64__)\n"
                    "typedef sys_call_ptr_t syscall_fn_t;\n"
                    "#elif defined(__riscv)\n")
revised_typedef = ("#if defined(__x86_64__)\n"
                   "typedef sys_call_ptr_t syscall_fn_t;\n"
                   "#elif defined(__aarch64__)\n"
                   "typedef long (*syscall_fn_t)(const struct pt_regs *);\n"
                   "#elif defined(__riscv)\n")
if hook_text.count(original_typedef) != 1:
    fail("KernelSU Next ARM64 syscall type context changed; manual review required")
hook_header.write_text(hook_text.replace(original_typedef, revised_typedef, 1))
# Pinned KSU fork accidentally includes linux/pgtable.h from a newer
# Linux series. Realme's 4.14.336 source has no such header. sucompat.c
# does not use pgd/pud/pmd/pte interfaces; it already includes linux/mm.h.
# This is a source-only compatibility adjustment, not a hardware change.
sucompat_file = ksu / "kernel/feature/sucompat.c"
sucompat_src = sucompat_file.read_text()
obsolete_include = "#include <linux/pgtable.h>\n"
if sucompat_src.count(obsolete_include) != 1:
    fail("Unexpected KernelSU Next pgtable.h include layout")
if not (src / "include/linux/mm.h").is_file() or (src / "include/linux/pgtable.h").exists():
    fail("Kernel header layout changed; refuse obsolete include removal")
sucompat_no_includes = "\n".join(
    line for line in sucompat_src.splitlines()
    if not line.lstrip().startswith("#include")
)
if any(token in sucompat_no_includes for token in
       ("pgd_(", "pud_(", "pmd_(", "pte_(", "p4d_(", "pgprot(")):
    fail("sucompat.c uses page table API; include must be ported, not removed")
sucompat_file.write_text(sucompat_src.replace(obsolete_include, "", 1))
patches = list((susfs / "kernel_patches").glob("50_add_susfs_in_kernel*4.14*.patch"))
if len(patches) != 1:
    fail("Exactly one upstream Linux 4.14 SUSFS VFS patch required")
for name, dest in (("fs", src / "fs"), ("include/linux", src / "include/linux")):
    folder = susfs / "kernel_patches" / name
    if not folder.is_dir():
        fail("Missing SuSFS " + name)
    for f in folder.iterdir():
        if f.is_file():
            target = dest / f.name
            if target.exists():
                fail("Refusing overwrite of original kernel file: " + str(target))
            shutil.copy2(f, target)
# Reject failed or fuzzy patch applications. NEVER emit a flashable ZIP from a failed port.
command = ["patch", "-d", str(src), "-p1", "--fuzz=0", "--batch", "-i", str(patches[0])]
check = subprocess.run(command + ["--dry-run"], capture_output=True, text=True)
if check.returncode:
    fail("SuSFS patch does not apply cleanly; source port needed:\n" +
         (check.stdout + check.stderr)[-3000:])
subprocess.run(command, check=True)
if not (src/"fs/susfs.c").exists() or not (src/"include/linux/susfs.h").exists():
    fail("Missing SuSFS compiled sources")
drivers = src / "drivers"
symlink = drivers / "kernelsu"
if symlink.exists() or symlink.is_symlink():
    fail("KernelSU already installed; avoid duplicate integration")
symlink.symlink_to(os.path.relpath(ksu / "kernel", drivers))
mk = drivers / "Makefile"
if "CONFIG_KSU" in mk.read_text():
    fail("KernelSU Kbuild entry already present")
mk.write_text(mk.read_text().rstrip() + "\nobj-$(CONFIG_KSU) += kernelsu/\n")
conf = drivers / "Kconfig"
if "drivers/kernelsu/Kconfig" in conf.read_text():
    fail("KernelSU Kconfig already present")
conf.write_text(conf.read_text().rstrip() + '\nsource "drivers/kernelsu/Kconfig"\n')
txt = cfg.read_text()
for name, val in (("LOCALVERSION", '"-Ahmed-Super-Kernal-A16"'),
                  ("KPROBES", "y"), ("KPROBE_EVENTS", "y"),
                  ("KSU", "y"), ("KSU_SUSFS", "y")):
    txt = putcfg(txt, name, val)
if "CONFIG_KSU_SUSFS_SUS_SU=y" in txt:
    txt = txt.replace("CONFIG_KSU_SUSFS_SUS_SU=y",
                      "# CONFIG_KSU_SUSFS_SUS_SU is not set")
cfg.write_text(txt)
print("A16 root and SuSFS source patches applied; kernel build and hardware boot are NOT yet verified.")
, '', sucompat_src, flags=re.M)
if re.search(r'\b(?:pgd_|pud_|pmd_|pte_|p4d_|pgprot)\w*\s*\(', sucompat_no_includes):
    fail("sucompat.c uses page table API; include must be ported, not removed")
sucompat_file.write_text(sucompat_src.replace(obsolete_include, "", 1))
patches = list((susfs / "kernel_patches").glob("50_add_susfs_in_kernel*4.14*.patch"))
if len(patches) != 1:
    fail("Exactly one upstream Linux 4.14 SUSFS VFS patch required")
for name, dest in (("fs", src / "fs"), ("include/linux", src / "include/linux")):
    folder = susfs / "kernel_patches" / name
    if not folder.is_dir():
        fail("Missing SuSFS " + name)
    for f in folder.iterdir():
        if f.is_file():
            target = dest / f.name
            if target.exists():
                fail("Refusing overwrite of original kernel file: " + str(target))
            shutil.copy2(f, target)
# Reject failed or fuzzy patch applications. NEVER emit a flashable ZIP from a failed port.
command = ["patch", "-d", str(src), "-p1", "--fuzz=0", "--batch", "-i", str(patches[0])]
check = subprocess.run(command + ["--dry-run"], capture_output=True, text=True)
if check.returncode:
    fail("SuSFS patch does not apply cleanly; source port needed:\n" +
         (check.stdout + check.stderr)[-3000:])
subprocess.run(command, check=True)
if not (src/"fs/susfs.c").exists() or not (src/"include/linux/susfs.h").exists():
    fail("Missing SuSFS compiled sources")
drivers = src / "drivers"
symlink = drivers / "kernelsu"
if symlink.exists() or symlink.is_symlink():
    fail("KernelSU already installed; avoid duplicate integration")
symlink.symlink_to(os.path.relpath(ksu / "kernel", drivers))
mk = drivers / "Makefile"
if "CONFIG_KSU" in mk.read_text():
    fail("KernelSU Kbuild entry already present")
mk.write_text(mk.read_text().rstrip() + "\nobj-$(CONFIG_KSU) += kernelsu/\n")
conf = drivers / "Kconfig"
if "drivers/kernelsu/Kconfig" in conf.read_text():
    fail("KernelSU Kconfig already present")
conf.write_text(conf.read_text().rstrip() + '\nsource "drivers/kernelsu/Kconfig"\n')
txt = cfg.read_text()
for name, val in (("LOCALVERSION", '"-Ahmed-Super-Kernal-A16"'),
                  ("KPROBES", "y"), ("KPROBE_EVENTS", "y"),
                  ("KSU", "y"), ("KSU_SUSFS", "y")):
    txt = putcfg(txt, name, val)
if "CONFIG_KSU_SUSFS_SUS_SU=y" in txt:
    txt = txt.replace("CONFIG_KSU_SUSFS_SUS_SU=y",
                      "# CONFIG_KSU_SUSFS_SUS_SU is not set")
cfg.write_text(txt)
print("A16 root and SuSFS source patches applied; kernel build and hardware boot are NOT yet verified.")
