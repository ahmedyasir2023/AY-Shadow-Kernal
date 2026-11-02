#!/usr/bin/env python3
"""Adapt exactly two SuSFS include-context hunks for RMX2170 4.14.336."""
import argparse
from pathlib import Path

a=argparse.ArgumentParser()
a.add_argument("--src",type=Path,required=True)
a.add_argument("--susfs",type=Path,required=True)
x=a.parse_args()
ns=(x.src/"fs/namespace.c").read_text()
mmu=(x.src/"fs/proc/task_mmu.c").read_text()
oplus=("#ifdef CONFIG_OPLUS_SECURE_GUARD\n"
       "#ifdef CONFIG_OPLUS_MOUNT_BLOCK\n"
       "#ifdef CONFIG_OPLUS_KEVENT_UPLOAD\n"
       "#include <linux/oplus_kevent.h>\n"
       "#endif /* CONFIG_OPLUS_KEVENT_UPLOAD */\n"
       "#endif /* CONFIG_OPLUS_MOUNT_BLOCK */\n"
       "#endif /* CONFIG_OPLUS_SECURE_GUARD*/\n")
if ns.count('#include "internal.h"\n'+oplus)!=1:
    raise SystemExit("Namespace includes changed; refuse unsafe SUSFS port")
if mmu.count('#include <linux/mm_inline.h>\n#include <linux/ctype.h>\n')!=1:
    raise SystemExit("task_mmu includes changed; refuse unsafe SUSFS port")
files=list((x.susfs/"kernel_patches").glob("50_add_susfs_in_kernel*4.14*.patch"))
if len(files)!=1:
    raise SystemExit("Exactly one 4.14 SuSFS patch expected")
path=files[0]
s=path.read_text()
start=s.index("diff --git a/fs/namespace.c b/fs/namespace.c")
end=s.index("diff --git ",start+10)
piece=s[start:end]
if piece.count("@@ -27,10 +27,39 @@")!=1:
    raise SystemExit("SuSFS namespace hunk header changed")
piece=piece.replace("@@ -27,10 +27,39 @@","@@ -27,17 +27,46 @@",1)
old=' #include "pnode.h"\n #include "internal.h"\n \n'
new=(' #include "pnode.h"\n #include "internal.h"\n' +
     ''.join(' '+line+'\n' for line in oplus.rstrip('\n').split('\n'))+' \n')
if piece.count(old)!=1:
    raise SystemExit("SuSFS namespace preimage changed")
piece=piece.replace(old,new,1)
s=s[:start]+piece+s[end:]
# This source contains an extra, unrelated ctype.h include between two
# upstream patch-context lines. Relocate that include without changing code.
# The original, unmodified task_mmu SuSFS hunk must then apply exactly.
original='#include <linux/mm_inline.h>\n#include <linux/ctype.h>\n'
reordered='#include <linux/ctype.h>\n#include <linux/mm_inline.h>\n'
if mmu.count(original)!=1:
    raise SystemExit("Unexpected A16 task_mmu include layout")
(x.src/"fs/proc/task_mmu.c").write_text(mmu.replace(original,reordered,1))
path.write_text(s)
print("Adapted A16 source include context, no SUSFS hunk skipped or patch fuzz.")
