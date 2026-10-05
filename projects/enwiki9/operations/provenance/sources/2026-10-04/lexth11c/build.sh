#!/bin/bash
# build.sh -- HPJA offline build phase for the lexth11c (cmix-lex transformer) entry.
#
# Contract (HutterPrizeJudgingAssistant ENTRANT_INSTRUCTIONS.md section 5): runs offline as
# UID/GID 65532 in a fresh container derived from install.sh's image; the unpacked source
# tree is mounted read-only at /entry, the cwd /work is the only writable location, and the
# executable declared as COMPRESSOR in entry.env -- here `cmix` -- must be written into /work.
# Only that file is returned to the orchestrator.
#
# Why the compressor is named `cmix` and not `comp9`: the program opens ITSELF by the literal
# name "cmix" in its working directory to read the appended dictionary / article-order /
# transformer-weight payloads (src/readalike_prepr/self_extract.h OpenSelf("cmix")), and the
# archive it writes opens itself as "archive9". entry.env therefore declares COMPRESSOR=cmix,
# ARCHIVE=archive9 and DECOMPRESSED_OUTPUT=enwik9_uncompressed.
#
# The build is the tree's own recipe, ./build_and_construct_comp.sh, with the lexth11c knobs
# exported as environment variables (they become -D defines; see the comments in that script):
#   PGO (clang-17 -fprofile-generate / llvm-profdata-17 merge / -fprofile-use -flto via lld-17)
#   on prof_input/input (raw path) + prof_input/input_4mb (dictionary path), portability gates
#   (AVX-512 only in the cpuid-dispatched qmat_*_avx512 objects, no RCPPS/RSQRTPS), strip,
#   UPX 5.1.1 --ultra-brute, then run/cmix = packed stub + comp_dict + comp_order + tfweights
#   + 16-byte header. That script writes into its own tree, so the tree is copied to /work first.
set -euo pipefail

say() { printf '\n=== %s ===\n' "$*"; }

# UID 65532 has no home directory and the judging image's /tmp is a symlink into /work/run;
# keep every implicit write under the one writable mount.
export HOME=/work/home
export TMPDIR=/work/tmp
mkdir -p "$HOME" "$TMPDIR"
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export LC_ALL=C
umask 022

SRC=/entry
[[ -f "$SRC/build_and_construct_comp.sh" && -f "$SRC/makefile" ]] || {
  echo "build.sh: $SRC does not look like the lexth11c source tree" >&2; exit 1; }

say "toolchain"
for t in clang++-17 ld.lld-17 llvm-profdata-17 llvm-strip-17 make objdump objcopy python3 md5sum awk; do
  command -v "$t" >/dev/null || { echo "build.sh: missing $t (install.sh should have installed it)" >&2; exit 1; }
done
UPX_SRC=/usr/local/bin/upx
[[ -x "$UPX_SRC" ]] || UPX_SRC=/opt/upx/upx-5.1.1-amd64_linux/upx
[[ -x "$UPX_SRC" ]] || { echo "build.sh: UPX 5.1.1 not found (install.sh installs /usr/local/bin/upx)" >&2; exit 1; }
clang++-17 --version | head -1; ld.lld-17 --version | head -1; "$UPX_SRC" --version | head -1
nproc; grep -m1 'model name' /proc/cpuinfo || true

say "copying the read-only source tree to /work/src"
rm -rf /work/src
mkdir -p /work/src
# cp -a would try to preserve the root ownership of /entry; copy contents and reset modes.
cp -R "$SRC/." /work/src/
chmod -R u+w /work/src
cd /work/src
rm -rf run pgo_data tools ./*.o cmix cmix.map
mkdir -p tools
cp "$UPX_SRC" tools/upx            # build_and_construct_comp.sh insists on ./tools/upx == "upx 5.1.1"
chmod 0755 tools/upx

TFWEIGHTS_FILE=/work/src/models/lex_h1_run11.tfwc2
[[ -s "$TFWEIGHTS_FILE" ]] || { echo "build.sh: missing $TFWEIGHTS_FILE" >&2; exit 1; }
echo "tfweights: $(wc -c < "$TFWEIGHTS_FILE") bytes sha256 $(sha256sum "$TFWEIGHTS_FILE" | cut -c1-64)"

say "PGO build (build_and_construct_comp.sh with the lexth11c knobs)"
# The lexth11c knob set (work/sota/modal_big.py VARIANTS["lexth11c"], build of record
# 2026-09-2x). CFLAGS_DEFINES of record:
#   -DSEED=923 -DUPDATE_LIMIT=3000 -DPPMD_MEM_MB=3500 -DCMIX_L0_LR_SCALE=0.6 -DCMIX_L1_LR_SCALE=0.25
#   -DCMIX_L0_MIXER_MASK=0x42e72du -DFXCM_CM_DIV=2
export PPMD_MEM_MB=3500 FXCM_CM_DIV=2 CMIX_L0_MIXER_MASK=0x42e72du CMIX_L0_LR_SCALE=0.6 CMIX_L1_LR_SCALE=0.25
export TF_CODEBOOK=1 TF_SMALL_W8=1 TF_ACTQ_DYN=1 TF_AVX512=1
export CM_OPT=-O2
export PGO_INPUT_DICT=./prof_input/input_4mb
export TFWEIGHTS="$TFWEIGHTS_FILE"
export FORCE_SELFEXTRACT_REBUILD=1
unset REUSE_PGO NATIVE COREI7 ZEN2 TF_WINDOW TF_WINDOW_MULTS TF_NL TF_DMLP UPX_BIN
# Everything the recipe depends on is in the tree; the knobs are the only inputs from here.
env | grep -E '^(PPMD_MEM_MB|FXCM_CM_DIV|CMIX_L0_MIXER_MASK|CMIX_L0_LR_SCALE|CMIX_L1_LR_SCALE|TF_CODEBOOK|TF_SMALL_W8|TF_ACTQ_DYN|TF_AVX512|CM_OPT|PGO_INPUT_DICT|TFWEIGHTS)=' | sort

bash ./build_and_construct_comp.sh

[[ -s run/cmix ]] || { echo "build.sh: build_and_construct_comp.sh did not produce run/cmix" >&2; exit 1; }

say "SCORED COMPRESSOR"
for f in cmix_orig comp_dict comp_order comp_tfweights header.dat cmix; do
  printf '  %-15s %9d bytes  sha256 %s\n' "$f" "$(wc -c < "run/$f")" "$(sha256sum "run/$f" | cut -c1-64)"
done
# Artifact of record (outputs/artifacts/hutter_lexth11c/comp9, 2026-09-24):
#   cmix_orig 198236  comp_dict 100866  comp_order 199980  comp_tfweights 2978039  header 16
#   cmix 3477137  sha256 e77c9a659b31c1358368da0ef49a8683080197b9b14a11b1e6e80a43c94cb463
RECORD_SHA=e77c9a659b31c1358368da0ef49a8683080197b9b14a11b1e6e80a43c94cb463
RECORD_BYTES=3477137
got_sha="$(sha256sum run/cmix | cut -c1-64)"; got_bytes="$(wc -c < run/cmix)"
if [[ "$got_sha" == "$RECORD_SHA" && "$got_bytes" == "$RECORD_BYTES" ]]; then
  echo "REBUILD IS BYTE-IDENTICAL to the artifact of record (comp9 $RECORD_BYTES bytes)."
else
  # A warning, not a failure: the harness scores the compressor IT rebuilt and re-verifies
  # its archive by a second decompression, so a valid rebuild that differs in the packed
  # stub (toolchain/libstdc++ headers of the qualification OS) is still a scored entry.
  echo "WARNING: rebuild differs from the artifact of record: $got_bytes bytes (record $RECORD_BYTES), sha256 $got_sha" >&2
fi

cp run/cmix /work/cmix
chmod 0755 /work/cmix
say "build.sh complete: /work/cmix ($(wc -c < /work/cmix) bytes)"
