#!/bin/bash -x

#SEED="$1"
#UPDATE_LIMIT="$2"

SEED="923"
UPDATE_LIMIT="3000"

# cmix-lex-transformer: FXCM_TF_INPUTS=1 additionally feeds the transformer's
# bit prediction (stretch(lstmpr)) into fxcm_v26's mixer layers 1 and 2, as
# fx2-cmix's fxcmv1 did with the lstm. Default 0 = cmix-lex's fxcm_v26 unchanged.
CFLAGS_DEFINES="-DSEED=$SEED -DUPDATE_LIMIT=$UPDATE_LIMIT"
if [[ "${FXCM_TF_INPUTS:-0}" == "1" ]]; then
  CFLAGS_DEFINES="$CFLAGS_DEFINES -DFXCM_TF_INPUTS=1"
fi
# lext_big: memory knobs (env var -> -D define; unset = cmix-lex defaults).
# PPMD_ORDER=25 PPMD_MEM_MB=14000 PPMD_TEXT_DIV=8 FXCM_CM_SCALE=1 FXCM_BUF_BITS=24
# FXCM_MHASH_BITS=22 CMIX_HISTORY_MB=60 CMIX_SHARED_MAP_MULT=1
# LEXT_LSTM (unset = off): 1/2/3 = online lstm byte mixer alongside the transformer,
# fed the ppmd's distribution / the transformer's / both (src/predictor.cpp).
# FXCM_TF_MIXER (unset = off): 1/2 = 19th fxcm_v26 layer-1 mixer selected by the transformer's
# expected byte (fx2-cmix's mxA[9]); 2 adds a confidence bucket (src/models/fxcmv1.cpp).
# CMIX_L0_LR_SCALE / CMIX_L1_LR_SCALE / CMIX_SSE_RATE_SCALE (unset = 1.0, and the scaled
# expressions are not even compiled): float scales on the learning rate of the 23 layer-0 cmix
# mixers, of the layer-1 mixer (0.0003), and of the two SSE stages' adaptation rates (106/127 of
# 32768, integer-rounded) (src/predictor.cpp AddMixer, src/mixer/sse.cpp).
# CMIX_L0_MIXER_MASK (unset = 0x7fffff = all 23): bit i keeps layer-0 cmix mixer i (src/predictor.cpp
# AddMixers); the Hutter time/memory study of the mixer ensemble (15 % of the CPU time, ~0.65 % each).
# LEXT_TF_APM (unset = off): APM/SSE stage on the transformer's bit prediction (src/mixer/tf-apm.h): 1 = final
# refinement keyed by the transformer's confidence, 2 = APM-refined p_tf as an extra mixer input, 3 = both.
for knob in PPMD_ORDER PPMD_MEM_MB PPMD_TEXT_DIV PPMD_CUTOFF FXCM_PREFETCH FXCM_CM_SCALE FXCM_BUF_BITS FXCM_MHASH_BITS CMIX_HISTORY_MB CMIX_SHARED_MAP_MULT LEXT_LSTM FXCM_TF_MIXER CMIX_L0_LR_SCALE CMIX_L1_LR_SCALE CMIX_SSE_RATE_SCALE CMIX_MMAP_TO_DISK CMIX_PPMD_REMAP_INTERVAL CMIX_L0_MIXER_MASK FXCM_CM_DIV LEXT_TF_APM; do
  if [[ -n "${!knob:-}" ]]; then
    CFLAGS_DEFINES="$CFLAGS_DEFINES -D$knob=${!knob}"
  fi
done
echo "CFLAGS_DEFINES=$CFLAGS_DEFINES"
# TF_WINDOW (unset = 1024): sliding attention window of the transformer inference engine, passed as
# -DATTN_WIN=$TF_WINDOW to the cpp_infer objects only (makefile CFLAGS_TF_DEFINES -> CPPFLAGS_TRANSFORMER;
# cpp_infer/src/attn_window.h sizes the KV rings/scratch from it). It must equal the window the .tfwc2
# weights (TFWEIGHTS below) were trained/exported with -- the loader refuses a mismatching config.ints[6].
CFLAGS_TF_DEFINES=""
if [[ -n "${TF_WINDOW:-}" ]]; then
  if ! [[ "$TF_WINDOW" =~ ^[0-9]+$ ]] || (( TF_WINDOW < 32 || TF_WINDOW % 32 != 0 )); then
    echo "ERROR: TF_WINDOW=$TF_WINDOW must be a positive multiple of 32" >&2
    exit 1
  fi
  CFLAGS_TF_DEFINES="-DATTN_WIN=$TF_WINDOW"
fi
# TF_WINDOW_MULTS (unset = every vanilla layer at TF_WINDOW; 2026-09-19): per-vanilla-layer window multipliers of a
# checkpoint trained with train_lex.py --window-mults, e.g. "1,1,2" = layers 3 and 7 at the window, layer 11 at 2x
# (cpp_infer/src/attn_window.h ATTN_WIN_MULTS; the .tfwc2 carries them in config.window_mults, FX2_WINDOW_MULTS at
# export -- the loader refuses a mismatch). One entry per vanilla layer in layer order, each in [1, 8].
if [[ -n "${TF_WINDOW_MULTS:-}" ]]; then
  if ! [[ "$TF_WINDOW_MULTS" =~ ^[1-8](,[1-8])*$ ]]; then
    echo "ERROR: TF_WINDOW_MULTS=$TF_WINDOW_MULTS must be a comma-separated list of multipliers in [1, 8]" >&2
    exit 1
  fi
  CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DATTN_WIN_MULTS=$TF_WINDOW_MULTS"
fi
# TF_NL / TF_DMLP (unset = 12 / 768): number of layers and MLP width of the transformer checkpoint (cpp_infer/src/opt/tf_arch.h);
# must equal the .tfwc2's config.ints[2] / [5] -- the loader refuses a mismatch.
if [[ -n "${TF_NL:-}" ]]; then CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DTF_NL=$TF_NL"; fi
if [[ -n "${TF_DMLP:-}" ]]; then CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DTF_DMLP=$TF_DMLP"; fi
# TF_CODEBOOK (unset = plain int4): the weights were exported with FX2_WCODEBOOK=1 (non-uniform 15-level codebooks,
# pysrc/export_weights.py) -> cpp_infer/src/opt/qmat.h QMAT_CODEBOOK; TF_WMAX (default 21) = the largest |codebook value|
# the kernels are widened for (FX2_CODEBOOK_MAX_INT at export; the loader refuses a larger config.codebook_max_int).
if [[ "${TF_CODEBOOK:-0}" == "1" ]]; then CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DQMAT_CODEBOOK=1 -DQMAT_WMAX=${TF_WMAX:-21}"; fi
# TF_SMALL_W8=1: token/prior/unembedding tables exported at 8 bits (FX2_WBITS_SMALL=8) -> int16-widened small matmuls (qmat.h QW8)
if [[ "${TF_SMALL_W8:-0}" == "1" ]]; then CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DQMAT_SMALL_W8=1"; fi
# TF_ACTQ_DYN=1 (2026-09-19): the weights were trained/exported with dynamic per-token activation scales (train_lex.py
# --actq-dynamic-mm, FX2_ACTQ_DYNAMIC_MM=1 at export -> config.actq_dynamic_mm in the .tfwc2) -> cpp_infer/src/opt/tf_arch.h
# TF_ACTQ_DYN; the loader refuses a .tfwc2 whose flag differs from the build.
if [[ "${TF_ACTQ_DYN:-0}" == "1" ]]; then CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DTF_ACTQ_DYN=1"; fi
# TF_AVX512=1 (2026-09-19): compile the AVX-512 VNNI fast path of the transformer matmuls (cpp_infer/src/opt/qmat.h TF_AVX512:
# qmat_dense_avx512.cpp / qmat_sparse_avx512.cpp, the only objects built with -mavx512f/bw/vl/vnni, see the makefile) and select
# it AT RUN TIME on CPUs with AVX-512 F/BW/VL/VNNI (cpuid + xgetbv in qmat_cpu.cpp: the Intel i7-1165G7 test machine, Zen 4);
# every other CPU (the AMD Ryzen 7 Zen 2 test machine) runs the unchanged AVX2 kernels. Both paths are bit-identical, so the
# archive does not depend on the machine (test_avx512 + test_e2e_opt FX2_FORCE_AVX2=0/1 + AMD<->Intel round trips). Weights and
# archive format are unchanged (the packed int4 + LUT arena is an in-memory layout). Default 0 = the AVX2-only binary.
if [[ "${TF_AVX512:-0}" == "1" ]]; then CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES -DTF_AVX512=1"; fi
echo "CFLAGS_TF_DEFINES=$CFLAGS_TF_DEFINES"

# The decompressor verifies the dictionary it recovers from the archive against
# the size and hash hard-coded in src/readalike_prepr/self_extract.h.
EXPECTED_DICT_MD5=b3a9cf9fac570b2dc9a0375534792980
actual_dict_md5=$(md5sum dictionary/english.dic | awk '{print $1}')
if [ "$actual_dict_md5" != "$EXPECTED_DICT_MD5" ]; then
  echo "ERROR: dictionary/english.dic has changed (md5 $actual_dict_md5, expected $EXPECTED_DICT_MD5)." >&2
  echo "Update kExpectedDictSize/kExpectedDictHash in src/readalike_prepr/self_extract.h." >&2
  exit 1
fi

# building with PGO
if [[ "${REUSE_PGO:-0}" == "1" && -s ./pgo_data/default.profdata ]]; then
  echo "Reusing existing PGO profile ./pgo_data/default.profdata"
else
  rm -rf pgo_data
  mkdir -p pgo_data
  make CFLAGS_DEFINES="$CFLAGS_DEFINES" CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES" CM_OPT="${CM_OPT:--O3}" prof_gen -j

  # PGO_INPUT / PGO_INPUT_DICT (2026-09-20, unset = prof_input/input = the authors' 50 KB sample): training inputs of the two
  # profiling runs (raw -c path, and the dictionary path the real -e run takes). A multi-MB dictionary-path input reaches the
  # steady-state branch mix (mixer LR phases, PPMD/KV rings warm) that a 50 KB run never sees; costs build time (instrumented binary).
  ./cmix -c ${PGO_INPUT:-./prof_input/input} ./prof_comp > ./prof_output
  # The real -e run enters compression through the dictionary/preprocessor path;
  # include a small sample of that route so PGO does not overfit to nodict only.
  ./cmix -c ./dictionary/english.dic ${PGO_INPUT_DICT:-./prof_input/input} ./prof_comp_dict > ./prof_output_dict
  rm ./prof_comp ./prof_output ./prof_comp_dict ./prof_output_dict
  llvm-profdata-17 merge -output=default.profdata ./pgo_data/*
  mv default.profdata pgo_data/
fi

make CFLAGS_DEFINES="$CFLAGS_DEFINES" CFLAGS_TF_DEFINES="$CFLAGS_TF_DEFINES" CM_OPT="${CM_OPT:--O3}" prof_use -j

# Guard against a non-portable binary. The Hutter Prize test machines are an
# Intel Core i7-1165G7 (Tiger Lake: AVX-512, but no AVX-VNNI) and an AMD
# Ryzen 7 (Zen 2: no AVX-512 at all), so anything past the AVX2 baseline is an
# illegal instruction on at least one of them. This catches a stray NATIVE=1,
# a stale objects directory, or a compiler that widens the baseline on its own.
# Checked before upx-ucl, which would hide the code from objdump.
check_avx2_only() {
  local bin="$1" dis bad=0
  if ! command -v objdump > /dev/null; then
    echo "WARNING: objdump not found, skipping the AVX2-only check on $bin" >&2
    return 0
  fi
  dis=$(objdump -d --insn-width=16 "$bin")
  # AVX-512: 512-bit registers, mask registers, or an EVEX (0x62) prefix.
  # AVX-VNNI: objdump prints the VEX encoding of an EVEX-capable opcode as
  # "{vex}", and on Tiger Lake only the EVEX form of vpdpwssd is legal.
  for pat in '%zmm' '%k[0-7]' '\{vex\}' $'\t62 [0-9a-f][0-9a-f] '; do
    if grep -qE "$pat" <<< "$dis"; then
      echo "ERROR: $bin uses instructions beyond the AVX2 baseline (matched '$pat'):" >&2
      grep -E "$pat" <<< "$dis" | head -3 >&2
      bad=1
    fi
  done
  if [ "$bad" -ne 0 ]; then
    echo "Build the submission with the default -march=x86-64-v3 (no NATIVE=1)." >&2
    return 1
  fi
  echo "AVX2-only check passed for $bin"
}

# TF_AVX512=1 variant of the gate: the binary now legitimately contains AVX-512 code, but ONLY inside the two
# *_avx512 objects (they are the only ones compiled with the feature flags and, being outside LTO, cannot be
# inlined elsewhere). The linker map (makefile -Wl,-Map=cmix.map) gives the address ranges of every input section
# of tf_qmat_dense_avx512.o / tf_qmat_sparse_avx512.o; every EVEX / zmm / mask-register instruction of the whole
# binary must fall inside those ranges (so a stray NATIVE=1 or a widened baseline is still caught), and the
# AVX-512 code itself must contain no "{vex}" VNNI (AVX-VNNI is illegal on Tiger Lake; only the EVEX forms
# are) and only F/BW/VL/VNNI-class opcodes (no zmm k-masked VBMI/DQ tricks the flags would not permit --
# guaranteed by the compile flags, re-checked by the instruction whitelist below). Runs before upx.
check_avx512_confined() {
  local bin="$1" map="$2"
  if ! command -v objdump > /dev/null || ! command -v python3 > /dev/null; then
    echo "ERROR: objdump and python3 are required for the AVX-512 confinement check on $bin" >&2
    return 1
  fi
  [[ -s "$map" ]] || { echo "ERROR: linker map $map missing (makefile LFLAGS -Wl,-Map)" >&2; return 1; }
  objdump -d --insn-width=16 "$bin" > "$bin.dis" || return 1
  python3 - "$bin.dis" "$map" <<'PY' || return 1
import re, sys
dis, mapf = sys.argv[1], sys.argv[2]
allowed_objs = ("tf_qmat_dense_avx512.o", "tf_qmat_sparse_avx512.o")
ranges = []
for line in open(mapf):
    m = re.match(r"^\s*([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s+(\d+)\s+(\S.*)$", line)
    if not m:
        continue
    tail = m.group(5)
    if any(tail.startswith(o + ":(") or (" " + o + ":(") in (" " + tail) for o in allowed_objs):
        vma, size = int(m.group(1), 16), int(m.group(3), 16)
        if size:
            ranges.append((vma, vma + size))
ranges.sort()
if not ranges:
    print("ERROR: no input sections of", allowed_objs, "found in", mapf); sys.exit(1)
def inside(a):
    import bisect
    i = bisect.bisect_right(ranges, (a, float("inf"))) - 1
    return i >= 0 and ranges[i][0] <= a < ranges[i][1]
evex = re.compile(r"^\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t?(.*)$")
n_in = n_out = n_vex = n_bad = 0
mnem_ok = re.compile(r"^(v[a-z0-9]+|kmov[bwdq]|knot[bwdq]|kand[bwdq]|kor[bwdq]|kxor[bwdq]|kxnor[bwdq]|korte?st[bwdq]|kshift[lr][bwdq]|kunpck[bwdq]+|kadd[bwdq])\b")
bad_examples = []
for line in open(dis, errors="replace"):
    m = evex.match(line)
    if not m:
        continue
    addr, bytes_, text = int(m.group(1), 16), m.group(2), m.group(3).replace("{evex} ", "")
    is512 = ("%zmm" in text) or re.search(r"%k[0-7]", text) is not None or "{vex}" in text or bytes_.startswith("62 ")
    if not is512:
        continue
    if not inside(addr):
        n_out += 1
        if len(bad_examples) < 5: bad_examples.append(line.rstrip())
        continue
    n_in += 1
    if "{vex}" in text:
        n_vex += 1
        if len(bad_examples) < 5: bad_examples.append("VEX-VNNI: " + line.rstrip())
    mn = text.split()[0] if text.split() else ""
    if not mnem_ok.match(mn) and mn not in ("(bad)",):
        n_bad += 1
        if len(bad_examples) < 5: bad_examples.append("unexpected mnemonic: " + line.rstrip())
print(f"AVX-512 confinement: {n_in} EVEX/zmm/mask instructions inside the {len(ranges)} sections of {allowed_objs}, "
      f"{n_out} outside, {n_vex} VEX-encoded VNNI, {n_bad} unexpected mnemonics")
for e in bad_examples: print("  ", e)
sys.exit(0 if (n_out == 0 and n_vex == 0 and n_bad == 0 and n_in > 0) else 1)
PY
  local rc=$?
  rm -f "$bin.dis"
  if [[ $rc -ne 0 ]]; then
    echo "ERROR: $bin has AVX-512 code outside the qmat_*_avx512 objects (or VEX-encoded VNNI); build with the default" >&2
    echo "-march=x86-64-v3 and keep the AVX-512 kernels in their own objects (makefile V512)." >&2
    return 1
  fi
  echo "AVX-512 confinement check passed for $bin (AVX-512 code only in the runtime-dispatched qmat_*_avx512 objects)"
}
if [[ "${TF_AVX512:-0}" == "1" ]]; then
  check_avx512_confined ./cmix ./cmix.map || exit 1
else
  check_avx2_only ./cmix || exit 1
fi

# Guard against a vendor-dependent binary. RCPPS/RCPSS/RSQRTPS/RSQRTSS are
# reciprocal *estimates*: the standards only bound their relative error
# (1.5*2^-12), the bits they return come from a vendor-specific table, and
# Intel and AMD return different ones. A single differing bit anywhere in the
# model changes a prediction and desynchronises the arithmetic coder, so an
# archive built on an AMD machine decodes to garbage on an Intel one (this is
# what broke the July 2026 submission on the prize committee's Intel laptop).
# The makefile passes -mrecip=none and cpp_infer/src/opt/vec_math.h uses true
# divides; this catches a regression in either.
check_no_recip_estimate() {
  local bin="$1" dis
  if ! command -v objdump > /dev/null; then
    echo "WARNING: objdump not found, skipping the reciprocal-estimate check on $bin" >&2
    return 0
  fi
  dis=$(objdump -d "$bin")
  if grep -qE '\b(v?rcpps|v?rcpss|v?rsqrtps|v?rsqrtss)\b' <<< "$dis"; then
    echo "ERROR: $bin uses reciprocal-estimate instructions, whose results" >&2
    echo "differ between Intel and AMD CPUs:" >&2
    grep -E '\b(v?rcpps|v?rcpss|v?rsqrtps|v?rsqrtss)\b' <<< "$dis" | head -3 >&2
    echo "Build with -mrecip=none and do not use _mm256_rcp_ps/_mm256_rsqrt_ps." >&2
    return 1
  fi
  echo "no reciprocal-estimate instructions in $bin"
}
check_no_recip_estimate ./cmix || exit 1

# Drop non-runtime ELF metadata before UPX. The binary is already linked with
# -s; these sections are extra loader/comment notes and do not affect behavior.
llvm-strip-17 --strip-all cmix || true
objcopy --remove-section=.comment \
  --remove-section=.note.gnu.property \
  --remove-section=.note.gnu.build-id \
  --remove-section=.note.ABI-tag \
  cmix 2>/dev/null || true
# LZMA-packed UPX is ~23 KB smaller than the default UCL mode on this binary.
# Use the exact local UPX installed by install_tools/install_upx.sh. Do not let
# a stale UPX_BIN environment variable or PATH entry silently change packaging.
UPX_BIN="./tools/upx"
if [[ ! -x "$UPX_BIN" ]]; then
  echo "Missing executable UPX at $UPX_BIN. Run ./install_tools/install_upx.sh or set UPX_BIN." >&2
  exit 1
fi
UPX_VERSION_TEXT="$("$UPX_BIN" --version | head -n 1)"
echo "Using $UPX_VERSION_TEXT"
if [[ "$UPX_VERSION_TEXT" != "upx 5.1.1" ]]; then
  echo "Refusing UPX version '$UPX_VERSION_TEXT'; expected local UPX 5.1.1." >&2
  exit 1
fi
"$UPX_BIN" --ultra-brute cmix 

# this is a directory where the compressor binary will be placed 
DIR=run
mkdir -p ./$DIR
ROOT=$(pwd)
cp ./cmix $DIR/cmix_orig
# git diff > $DIR/patch
# exit
# building a selfextracting binary 
pushd $DIR
# Reuse the embedded dictionary/order streams by default. PPM mmap/RSS-only
# changes do not alter compression behavior, and recompressing these payloads
# costs time without changing the final self-extract contents. Set
# FORCE_SELFEXTRACT_REBUILD=1 when the dictionary, order, or coder changes.
if [[ "${FORCE_SELFEXTRACT_REBUILD:-0}" == "1" || ! -s ./comp_dict ]]; then
  ./cmix_orig -c $ROOT/dictionary/english.dic ./comp_dict
else
  echo "Reusing cached ./comp_dict ($(wc -c < ./comp_dict) bytes)"
fi
if [[ "${FORCE_SELFEXTRACT_REBUILD:-0}" == "1" || ! -s ./comp_order ]]; then
  ./cmix_orig -c $ROOT/src/readalike_prepr/data/new_article_order ./comp_order
else
  echo "Reusing cached ./comp_order ($(wc -c < ./comp_order) bytes)"
fi
# the transformer weights are already losslessly compressed (FX2TFWC2, made by
# fx2-cmix-transformer's pysrc/weights_compress.py) and are loaded directly in
# that format, so they are appended as-is
TFWEIGHTS="${TFWEIGHTS:-$ROOT/models/6m-q4-fp32.tfwc2}"
cp "$TFWEIGHTS" ./comp_tfweights
# creating a header with size of the above files
./cmix_orig -h $(wc -c < ./comp_dict) $(wc -c < ./comp_order) 0 $(wc -c < ./comp_tfweights)

# merging the above files and setting permissions for the final executable file
cat ./cmix_orig ./comp_dict ./comp_order ./comp_tfweights header.dat > ./cmix
chmod +x ./cmix
