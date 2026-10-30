#!/usr/bin/env python3
"""Package a compiled AY Shadow kernel for an RMX2170 ROM boot using a known-working AnyKernel3 ZIP.
Inputs are supplied separately because the MelloDerp boot image is not bundled in this repository.
Outputs are EXPERIMENTAL and untested on actual hardware.
"""
import argparse,hashlib,struct,zlib,zipfile
from pathlib import Path

def digest(x):return hashlib.sha256(x).hexdigest()
def round_up(n,p):return ((n+p-1)//p)*p
def dtbs(x):
  output=[];pos=0
  while pos<len(x):
    if x[pos:pos+4]!=bytes.fromhex("d00dfeed"):raise ValueError("Bad FDT magic")
    n=struct.unpack_from(">I",x,pos+4)[0]
    if not 100000<=n<=len(x)-pos:raise ValueError("Bad FDT size")
    output.append(x[pos:pos+n]);pos+=n
  if len(output)!=4:raise ValueError("Expected four ROM DTBs")
  return output
def rom_dtb(boot_path):
  b=boot_path.read_bytes()
  if b[:8]!=b"ANDROID!":raise ValueError("Not an Android boot image")
  kernel,ramdisk,second,page,version=[struct.unpack_from("<I",b,o)[0] for o in (8,16,24,36,40)]
  recovery=struct.unpack_from("<I",b,1632)[0]
  size=struct.unpack_from("<I",b,1648)[0]
  if page!=4096 or version!=2:raise ValueError("Expected Android boot image header v2, 4096-byte page")
  offset=page+sum(round_up(v,page) for v in (kernel,ramdisk,second,recovery))
  blob=b[offset:offset+size]
  dtbs(blob)
  if digest(blob)!="260293a864b5c1ac38f5f3221265d4921607a4083aff9606b38ae4d643dc9da9":
    raise ValueError("Boot DTBs are not from the verified reference MelloDerp ROM")
  return blob
def main():
  p=argparse.ArgumentParser()
  for name in ("image","rom_boot","base_flashable","output"):
    p.add_argument("--"+name.replace("_","-"),required=True,type=Path)
  a=p.parse_args()
  image=a.image.read_bytes()
  decomp=zlib.decompressobj(31)
  decomp.decompress(image);decomp.flush()
  if not decomp.eof or not decomp.unused_data:raise ValueError("Expected Image.gz-dtb")
  gzip=image[:-len(decomp.unused_data)]
  new_dtbs=dtbs(decomp.unused_data)
  original=rom_dtb(a.rom_boot)
  matches=sum(digest(d) in {digest(o) for o in dtbs(original)} for d in new_dtbs)
  if matches<3:raise ValueError("Compiled device trees differ too much from the ROM")
  payload=gzip+original
  with zipfile.ZipFile(a.base_flashable) as z:
    content={i.filename:z.read(i) for i in z.infolist() if not i.is_dir()}
  script=content["anykernel.sh"].decode()
  for needle in ("supported.versions=14","do.devicecheck=1","Cannot verify Realme 7 Pro/RMX2170","PATCH_VBMETA_FLAG=0","split_boot","flash_boot"):
    if needle not in script:raise ValueError("Base recovery package did not pass safety check: "+needle)
  script=script.replace("AY Shadow Kernal v2.1","AY Shadow Kernal v3.0")
  script=script.replace("boot-before-AYShadow-v2.1-","boot-before-AYShadow-v3.0-")
  content["anykernel.sh"]=script.encode()
  content["zImage"]=payload
  content["README.txt"]=(
    "AY Shadow Kernal v3.0 — EXPERIMENTAL RMX2170 MelloDerp Android 14.\n"
    "A new compiled Linux 4.14.357 kernel with KernelSU Next and SUSFS.\n"
    "FLASH AT YOUR OWN RISK. No physical hardware boot test has been performed.\n"
    "Back up your CURRENT boot partition in OrangeFox before flashing.\n"
    "Only boot kernel is replaced; original ROM device tree is retained.\n"
    "If the device bootloops, restore YOUR previous boot image.\n"
  ).encode()
  content["AY-Shadow-v3-checksums.txt"]=(
    "Compiled image SHA256: "+digest(image)+"\n"
    "ROM DTB SHA256: "+digest(original)+"\n"
    "AnyKernel zImage SHA256: "+digest(payload)+"\n"
    "DTB matches: "+str(matches)+"/4\n"
  ).encode()
  a.output.parent.mkdir(parents=True,exist_ok=True)
  with zipfile.ZipFile(a.output,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for name,data in sorted(content.items()):z.writestr(name,data)
  with zipfile.ZipFile(a.output) as z:
    if z.testzip() is not None:raise ValueError("ZIP CRC test failed")
  print("Created:",a.output,"sha256",digest(a.output.read_bytes()))
if __name__=="__main__":main()
