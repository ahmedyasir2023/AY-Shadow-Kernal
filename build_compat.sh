#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="$ROOT/work/compat-source"
OUT="$ROOT/work/compat-out"
BASE_SHA=7306b28fccd87db72f25b314105747b1ce6f653c
mkdir -p "$ROOT/work" "$ROOT/dist/compat"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --depth 1 --branch astra-ksu https://github.com/theshaenix/ShadowBladeX.git "$SRC"
fi
[[ "$(git -C "$SRC" rev-parse HEAD)" == "$BASE_SHA" ]] || {
  echo "Upstream Astra changed; source needs fresh review" >&2; exit 2;
}
python3 scripts/compat_patch.py "$SRC"
CLANG_DIR="${CLANG_DIR:-$HOME/toolchains/clang}"
GCC_DIR="${GCC_DIR:-$HOME/toolchains/gcc-aarch64-linux-gnu-9.3}"
if [[ ! -x "$CLANG_DIR/bin/clang" ]]; then
  git clone --depth 1 --branch lineage-20.0 https://github.com/LineageOS/android_prebuilts_clang_kernel_linux-x86_clang-r416183b.git "$CLANG_DIR"
fi
if [[ ! -x "$GCC_DIR/bin/aarch64-linux-gcc" ]]; then
  git clone --depth 1 --branch lineage-23.0 https://github.com/LineageOS/android_prebuilts_gcc_linux-x86_aarch64_aarch64-linux-gnu-9.3.git "$GCC_DIR"
fi
export PATH="$CLANG_DIR/bin:$GCC_DIR/bin:$PATH"
export ARCH=arm64 CROSS_COMPILE=aarch64-linux- CLANG_TRIPLE=aarch64-linux-gnu-
mkdir -p "$OUT"
make -C "$SRC" O="$OUT" ARCH=arm64 LLVM=1 LLVM_IAS=1 atoll_defconfig
python3 scripts/compat_verify.py "$SRC" "$OUT/.config"
set -o pipefail
make -C "$SRC" -j"${BUILD_JOBS:-4}" O="$OUT" ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy \
  OBJDUMP=llvm-objdump STRIP=llvm-strip \
  CLANG_TRIPLE="$CLANG_TRIPLE" CROSS_COMPILE="$CROSS_COMPILE" \
  Image.gz-dtb 2>&1 | tee "$ROOT/work/compat-build.log"
test -s "$OUT/arch/arm64/boot/Image.gz-dtb"
cp "$OUT/arch/arm64/boot/Image.gz-dtb" "$ROOT/dist/compat/AY-Shadow-FP-Compat-EXPERIMENTAL-Image.gz-dtb"
cp "$OUT/.config" "$ROOT/dist/compat/AY-Shadow-FP-Compat.config"
echo "Experimental kernel built; NOT VERIFIED to boot on RMX2170. Do not flash raw image."
