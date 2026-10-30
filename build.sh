#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"
BASE_REPO=https://github.com/theshaenix/ShadowBladeX.git
BASE_SHA=3f464b55a3c34dc06efa04dbe58a48b349623098
SRC="$ROOT/work/source"
OUT="$ROOT/work/out"
mkdir -p "$ROOT/work" "$ROOT/dist"
if [[ ! -d "$SRC/.git" ]]; then
  git clone --depth 1 --branch mcqueen-ksu "$BASE_REPO" "$SRC"
fi
ACTUAL="$(git -C "$SRC" rev-parse HEAD)"
[[ "$ACTUAL" == "$BASE_SHA" ]] || { echo "Unreviewed kernel source commit $ACTUAL" >&2; exit 2; }
python3 "$ROOT/scripts/apply.py" "$SRC"
CLANG_DIR="${CLANG_DIR:-$HOME/toolchains/clang}"
GCC_DIR="${GCC_DIR:-$HOME/toolchains/gcc-aarch64-linux-gnu-9.3}"
if [[ ! -x "$CLANG_DIR/bin/clang" ]]; then
  git clone --depth 1 --branch lineage-20.0 https://github.com/LineageOS/android_prebuilts_clang_kernel_linux-x86_clang-r416183b.git "$CLANG_DIR"
fi
if [[ ! -x "$GCC_DIR/bin/aarch64-linux-gcc" ]]; then
  git clone --depth 1 --branch lineage-23.0 https://github.com/LineageOS/android_prebuilts_gcc_linux-x86_aarch64_aarch64-linux-gnu-9.3.git "$GCC_DIR"
fi
export PATH="$CLANG_DIR/bin:$GCC_DIR/bin:$PATH"
export ARCH=arm64 CLANG_TRIPLE=aarch64-linux-gnu- CROSS_COMPILE=aarch64-linux-
mkdir -p "$OUT"
make -C "$SRC" O="$OUT" ARCH=arm64 LLVM=1 LLVM_IAS=1 atoll_defconfig
python3 "$ROOT/scripts/verify_config.py" "$OUT/.config"
set -o pipefail
make -C "$SRC" O="$OUT" -j"${BUILD_JOBS:-4}" ARCH=arm64 LLVM=1 LLVM_IAS=1 \
  CC=clang LD=ld.lld AR=llvm-ar NM=llvm-nm OBJCOPY=llvm-objcopy \
  OBJDUMP=llvm-objdump STRIP=llvm-strip \
  CLANG_TRIPLE="$CLANG_TRIPLE" CROSS_COMPILE="$CROSS_COMPILE" \
  Image.gz-dtb 2>&1 | tee "$ROOT/work/build.log"
IMAGE="$OUT/arch/arm64/boot/Image.gz-dtb"
test -s "$IMAGE"
cp "$IMAGE" "$ROOT/dist/AY-Shadow-Kernal-v3-Image.gz-dtb"
cp "$OUT/.config" "$ROOT/dist/AY-Shadow-Kernal-v3.config"
echo "Compiled experimental image. NOT VERIFIED FOR RMX2170 OR SAFE TO FLASH."
