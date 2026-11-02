#!/usr/bin/env bash
# A16 experimental source build. Never modifies handset or creates flashable ZIP.
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC=/tmp/a16-source
OUT=/tmp/a16-out
CLANG=/tmp/a16-clang
mkdir -p "$ROOT/dist/a16" "$ROOT/work"
test -f "$SRC/fs/susfs.c" && test -f "$SRC/drivers/kernelsu/Kconfig"
if [[ ! -x "$CLANG/bin/clang" ]]; then
  git clone --depth 1 https://github.com/bluegreensea/android_prebuilts_clang_kernel_linux-x86_clang-r563880c.git "$CLANG"
fi
export PATH="$CLANG/bin:$PATH"
export ARCH=arm64
export CLANG_TRIPLE=aarch64-linux-gnu-
export CROSS_COMPILE=aarch64-linux-gnu-
echo "Using: $(clang --version | head -n 1)"
make -C "$SRC" O="$OUT" ARCH=arm64 CC=clang LLVM=1 LLVM_IAS=1 atoll_defconfig
python3 "$ROOT/a16/verify_config.py" "$OUT/.config"
make -C "$SRC" -j4 O="$OUT" ARCH=arm64 \
  CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy \
  OBJDUMP=llvm-objdump STRIP=llvm-strip \
  LLVM=1 LLVM_IAS=1 CLANG_TRIPLE="$CLANG_TRIPLE" CROSS_COMPILE="$CROSS_COMPILE" \
  Image.gz-dtb 2>&1 | tee "$ROOT/work/a16-build.log"
RAW="$OUT/arch/arm64/boot/Image.gz-dtb"
test -s "$RAW"
cp "$RAW" "$ROOT/dist/a16/Ahmed-Super-Kernal-A16-Image.gz-dtb"
cp "$OUT/.config" "$ROOT/dist/a16/config"
make -s -C "$SRC" O="$OUT" ARCH=arm64 CC=clang LLVM=1 LLVM_IAS=1 kernelrelease \
  > "$ROOT/dist/a16/kernelrelease.txt"
(cd "$ROOT/dist/a16" && sha256sum Ahmed-Super-Kernal-A16-Image.gz-dtb > SHA256SUMS)
echo "A16 compilation completed. RAW SOURCE ARTIFACT ONLY, NOT FLASHABLE."
