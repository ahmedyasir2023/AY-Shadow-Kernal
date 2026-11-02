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
start=s.index("diff --git a/fs/proc/task_mmu.c b/fs/proc/task_mmu.c")
end=s.index("diff --git ",start+10)
piece=s[start:end]
if piece.count("@@ -19,6 +19,9 @@")!=1:
    raise SystemExit("SuSFS task_mmu hunk header changed")
piece=piece.replace("@@ -19,6 +19,9 @@","@@ -19,7 +19,10 @@",1)
anchor=" #include <linux/mm_inline.h>\n"
if piece.count(anchor)!=1:
    raise SystemExit("SuSFS task_mmu preimage changed")
piece=piece.replace(anchor,anchor+" #include <linux/ctype.h>\n",1)
s=s[:start]+piece+s[end:]
path.write_text(s)
print("Two exact source-context adjustments, no skipped SuSFS changes or patch fuzz.")
