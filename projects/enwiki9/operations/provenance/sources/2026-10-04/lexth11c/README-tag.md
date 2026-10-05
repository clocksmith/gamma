# cmix-lex-transformer — `lexth11c`

A Hutter Prize / Large Text Compression Benchmark entry for **enwik9** (the first 10^9 bytes of English Wikipedia).

| | bytes | sha256 |
|---|---|---|
| `archive9` (self-extracting decompressor + data) | **95,836,613** | `a5b9c2e3fe000a0299606da20c4915d992ff09d8fd819f8ac6a640aa0eb0d956` |
| `cmix` (the compressor, "comp9") | **3,477,137** | `e77c9a659b31c1358368da0ef49a8683080197b9b14a11b1e6e80a43c94cb463` |
| **S = comp9 + archive9** | **99,313,750** | |

Binaries are attached to the [`lexth11c` release](../../releases/tag/lexth11c). The compressor must be run under the
file name `cmix` and the archive under `archive9` (each program opens itself by that name to read the payload
appended to its UPX-packed stub).

## Run

```sh
chmod +x archive9 && ./archive9      # writes enwik9_uncompressed (1,000,000,000 bytes) in the current directory
./cmix -e enwik9 o                   # compress: writes the cmix stream to o and the self-extracting archive9
```

Single thread, no GPU, Linux x86-64 (any AVX2 CPU; AVX-512 VNNI kernels are cpuid-dispatched and bit-identical).
Peak RSS < 10 GiB (9.77 GB compress, 9.60 GB decompress), ~3 GB temporary disk.

## Verification (see `evidence/lexth11c/`)

* Compression: 55:24:11 wall / 196,733 s CPU on one core of a cloud Intel Xeon (Ice Lake SP) sandbox, peak RSS 9,765,024 kB.
* Clean-room decode on an independent Intel host (fresh container, only `archive9` present): `cmp` byte-exact against
  enwik9 (sha256 `159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`), 59:26:45 wall / 206,376 s CPU,
  peak RSS 9,597,984 kB, exit 0 — `evidence/lexth11c/decode_intel/`.
* Cross-vendor: a 24-hour partial decode on an AMD host without AVX-512 produced a decoder stream byte-identical to the
  Intel run over the first 292,667,392 bytes.
* Speed calibration against the published fx2-cmix-transformer binaries on the same hosts: compress ≈ 1.0× fx2-cmix-transformer,
  decompress 1.06–1.29× faster (`docs/HUTTER_SUBMISSION.md`). fx2-cmix-transformer took 37.2 h on the Hutter Prize
  Ryzen 7 3700 test machine.

## What it is

The compressor is a cmix/PAQ-family context-mixing compressor with a small transformer as one of its models:

* **Lineage.** [cmix-lex](README-cmix-lex.md) by Ibrahim Marcouch (fxcm_v26 context model, `payload_lex` tail transform,
  updated article order), itself derived from [fx2-cmix](https://github.com/kaitz/fx2-cmix) by Kaido Orav and Byron Knoll,
  merged with the int4 transformer byte-mixer of fx2-cmix-transformer-v1 (Orav & Knoll). `changes.md` is the upstream
  cmix-lex algorithm description; `cpp_infer/` is the transformer inference library.
* **What is new here** (details in `docs/`):
  * the transformer (12 layers, MLP 768, 3 sliding-window attention layers W=1024 + 9 KDA layers) was **retrained from
    scratch for 1280 epochs** with quantization-aware training: frozen Lloyd–Max codebook int4 weights (grid 1/4, |int| ≤ 21),
    8-bit embedding/prior/unembedding tables and per-token dynamic int8 activation scales (`models/lex_h1_run11.tfwc2`,
    2,978,039 bytes, FX2TFWC2 container);
  * the context-mixing side re-tuned for the 10 GB limit: PPMd heap 3500 MB in plain RAM with cut-off pruning (no memory
    mapping), fxcm context maps halved, 12 of the 23 layer-0 mixers kept, layer-0/layer-1 learning-rate scaling
    (`-DCMIX_L0_LR_SCALE=0.6 -DCMIX_L1_LR_SCALE=0.25`);
  * build: clang-17 PGO + LTO, `-march=x86-64-v3` baseline with cpuid-dispatched AVX-512 VNNI matmul kernels (verified
    bit-identical to the AVX2 path), UPX 5.1.1 packed stub; the exact knobs are exported at the top of `build.sh`.

## Build (reproduces `cmix`)

Automated-judging form (https://github.com/jabowery/HutterPrizeJudgingAssistant): `entry.env`, `install.sh` (root +
network: clang-17/lld-17 from apt.llvm.org, UPX 5.1.1, make), `build.sh` (offline, unprivileged, cwd `/work` → writes
`/work/cmix`), `comp9.args`. QUALIFICATION_OS = ubuntu-22.04, on which the rebuild reproduces the 3,477,137-byte `cmix`
whose output is bit-identical to the release binary's (`docs/HPJA_PACKAGING_REPORT.md`). By hand:

```sh
export TF_CODEBOOK=1 TF_SMALL_W8=1 TF_ACTQ_DYN=1 CM_OPT=-O2 TF_AVX512=1 PGO_INPUT_DICT=./prof_input/input_4mb \
       PPMD_MEM_MB=3500 FXCM_CM_DIV=2 CMIX_L0_MIXER_MASK=0x42e72du CMIX_L0_LR_SCALE=0.6 CMIX_L1_LR_SCALE=0.25 \
       TFWEIGHTS=models/lex_h1_run11.tfwc2
./build_and_construct_comp.sh        # -> run/cmix
```

See `README-HPJA.md` for the full description of the packaging.

## Documents

* `docs/HUTTER_SUBMISSION.md` — engineering log and the itemized rule checklist (memory, time calibration, judging harness).
* `docs/LTCB_SUBMISSION.md` — LTCB notes and verification checklist.
* `docs/HUTTER_WRITEUP.md`, `docs/HUTTER_BUILD.md` — the ideas and the build recipe.
* `docs/ATTENTION_KERNEL_REPORT.md` — attention KV-layout study (not used by the lexth11c binary; adopted for successors).
* `changes.md`, `cpp_infer/*.md` — upstream algorithm and transformer documentation.

## Authorship, license, disclosure

Submitted by Neel Patel (GitHub: Neel49). This is a derivative work released under the **GNU GPL v3** (`LICENSE`), the
license of cmix-lex / fx2-cmix / cmix; the authorship of the inherited components (Ibrahim Marcouch; Kaido Orav; Byron Knoll;
the cmix, paq8 and PPMd authors) is unchanged. The retraining, tuning, kernel work and verification described above were
carried out with an AI coding agent (OpenAI Codex) under the submitter's direction, using cloud GPUs for training only —
the compressor itself uses no GPU. Prize allocation, if any: to the submitter, subject to the committee's judgement.
