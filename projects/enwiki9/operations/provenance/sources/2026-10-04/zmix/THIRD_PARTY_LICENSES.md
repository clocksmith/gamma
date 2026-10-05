# Third-party licence inventory

Companion to [`NOTICE.md`](NOTICE.md) (the short statement) and
[`THIRD-PARTY-NOTICES.md`](THIRD-PARTY-NOTICES.md) (the narrative attribution). This file is the
mechanical inventory: every third-party component in the submitted package, its author, its
licence, where the licence text lives here, and — for the vendored C++ — the per-file provenance
and whether zmix modified it.

**Combined-work licence: GPL-3-or-later.** Every incorporated upstream is GPL-3
(`cmix`, `fx2-cmix`/`fxcm`, `fx2-cmix-transformer` ship the identical FSF GPLv3 text,
md5 `1ebbd3e34237af26da5dc08a4e440464`, reproduced here as
[`LICENSES/GPL-3.0.txt`](LICENSES/GPL-3.0.txt)). GPL-3 code cannot be redistributed under GPLv2,
so the whole entry is GPL-3-or-later, and every zmix-authored file is offered on those terms.

---

## 1. `fx2-cmix-transformer` — Vladimir Ivanov — GPL-3

Pending Hutter Prize entry, submitted 2026-07-24. Upstream licence text: its `LICENSE` (GPLv3),
reproduced verbatim at `LICENSES/GPL-3.0.txt`.

### 1a. Trained model weights

Three weight blobs are present in this package. **Only the third is shipped inside `comp9` and
`archive9.exe`**; the other two are kept so the derivation is reviewable end to end.

| file | bytes | sha256 | origin | shipped? |
|---|---:|---|---|---|
| `assets/6m-q4-fp32.tfwc2` | 2,930,652 | `7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860` | **verbatim** copy of their `models/6m-q4-fp32.tfwc2` | no |
| `assets/6m-q4-fp32.tfwc3` | 2,840,417 | `c8919e6e1a7d4ce1d70330f8f88dff4436958282de2d1958c2c260751da5166f` | **the same trained values**, re-containered by zmix (`FX2TFWC3`); the 88 raw f32 tensors are carried as bfloat16 | no |
| **`assets/6m-q4-fp32-t1lambda1.tfwc3`** | **2,815,630** | **`8e8ef3acacfb84437868035923bf9987f9adc826d2c833fb828204d2ab9c807d`** | **RETRAINED derivative** of `fx2-cmix-transformer` — see the chain below | **YES — this is the blob in `comp9` and `archive9.exe`** |

**The trained parameters of the first two blobs are Ivanov's work**, produced on 8×RTX 5090 for
~26 h (their `writeup.md`). The container format of `.tfwc3` is zmix's; the values are theirs.

#### The shipped blob's provenance chain, with a digest at every link

`assets/6m-q4-fp32-t1lambda1.tfwc3` is a **derived work of `fx2-cmix-transformer` (GPL-3)**. It
carries **retrained** parameters, not Ivanov's trained parameters — but it derives from that
project at every step: its architecture, its training code and recipes, its training corpus
pipeline, its quantizer and its container writer are all that project's.

| # | link | bytes | sha256 |
|---|---|---:|---|
| 0 | upstream reference blob, for orientation: their `models/6m-q4-fp32.tfwc2` | 2,930,652 | `7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860` |
| 1 | the entrant's fp32 retraining checkpoint `t1-lambda1-fp32.tch` — the same 12-layer / 5,923,228-parameter architecture, trained with the upstream project's own GPL-3 training code (`src/pysrc/`, `src/training_recipes/`) on the same post-WRT token stream, with a weight-entropy penalty added to the loss (the `λ*` arm) | 23,871,037 | `61f1d703eb11ba69df98ea0a605f84686b96055da494a49bc0756a26f7701b47` |
| 2 | exported through the upstream project's own quantizer and `FX2TFWC2` container writer (`pysrc/weights_compress.py`) as `models/t1-lambda1.tfwc2` | 2,900,961 | `4fab46d5bcf51551c802f8d0a4776ec3c90574f202dab5c576d07e84df650406` |
| 3 | **re-containered by zmix** into the `FX2TFWC3` container as `assets/6m-q4-fp32-t1lambda1.tfwc3` — a lossless recoding of the int4 weights and bf16 row-scales, with the raw trained f32 tensors carried as bfloat16 | **2,815,630** | **`8e8ef3acacfb84437868035923bf9987f9adc826d2c833fb828204d2ab9c807d`** |

Link 1→2 is verified rather than asserted: all **5,868,864** int4 weights in the `.tfwc2` reproduce
from the `.tch` through the upstream project's own `quantize_weight_rows`, **0 mismatches**. Link
2→3 is verified by decoding the `FX2TFWC3` container and comparing tensor by tensor. Both checks,
and the measurement that adopting this blob costs **no** change to the decoder, are recorded in
`assets/PROVENANCE.md`.

**Licence.** The retrained parameters and both containers are distributed under **GPL-3**, as a
derivative of `fx2-cmix-transformer`, with attribution to Vladimir Ivanov for the architecture,
the training code and the container format that the derivation runs through.

Detail and the regeneration procedure for all three blobs: `assets/PROVENANCE.md`.

### 1b. Inference kernels — `third_party/fx2_transformer/` (24 files)

All 23 derive from their `cpp_infer/src/` (mostly `cpp_infer/src/opt/`). Classification measured
by `cmp` against the upstream tree, and re-checked after the notices below were added —
**12 verbatim, 9 modified, 3 zmix-authored around verbatim excerpts**.

**GPL-3 §5(a): every one of the 9 modified files carries a modification notice as the FIRST
comment block in the file**, naming the upstream path, the dates and the change; the 2
zmix-authored files carry an equivalent notice naming the verbatim excerpts they incorporate. The
notices are self-contained — nothing outside this package is needed to date the changes. The
`what changed` column below is the same information in one place, with the diff size measured
against upstream.

| file in this package | upstream file | status | dates | what changed (lines vs upstream) |
|---|---|---|---|---|
| `arena_build.cpp` | `cpp_infer/src/opt/arena_build.cpp` | **modified** | 2026-08-31, 09-01 | `<sys/mman.h>` removed — the `mmap`+`MADV_HUGEPAGE` weight pool becomes a portable 2 MiB-aligned `malloc` block; include path flattened; packed int4 arena under `FX2_PACKED_DENSE`. **+30 / −8** |
| `arena_build.h` | `cpp_infer/src/opt/arena_build.h` | **modified** | 2026-08-31, 09-01 | `WeightPool::raw` added for the portable allocator; `QPacked` arena member under `FX2_PACKED_DENSE`. **+12 / −1** |
| `attn.cpp` | `cpp_infer/src/opt/attn.cpp` | verbatim | — | — |
| `attn.h` | `cpp_infer/src/opt/attn.h` | verbatim | — | — |
| `fx2_shim.cpp` | zmix-authored; contains verbatim excerpts of `cpp_infer/src/predictor.cpp:26-101,546-588` | **derived** | 2026-08-31 … 09-01 | the `extern "C"` boundary between zmix (Zig) and the vendored kernels |
| `fx2_shim.h` | zmix-authored; contains verbatim excerpts of `cpp_infer/src/predictor.cpp:26-101` | **derived** | 2026-08-31 … 09-01 | as above |
| `glue.cpp` | `cpp_infer/src/opt/glue.cpp` | verbatim | — | — |
| `glue.h` | `cpp_infer/src/opt/glue.h` | verbatim | — | — |
| `kda.cpp` | `cpp_infer/src/opt/kda.cpp` | **modified** | 2026-08-31 | `g_sweep`/`g_pf_mode` frozen to `const` and the exported setters DELETED — a run-time arithmetic-variant switch is an arithmetic-coder desync hazard between the two programs. **+15 / −4** |
| `kda.h` | `cpp_infer/src/opt/kda.h` | **modified** | 2026-08-31 | the two setter declarations deleted, matching `kda.cpp`. **+3 / −2** |
| `kda_math.h` | `cpp_infer/src/opt/kda_math.h` | verbatim | — | — |
| `model_opt.cpp` | `cpp_infer/src/opt/model_opt.cpp` | **modified** | 2026-08-31, 09-01, 09-06 | (1) packed-arena code path under `FX2_PACKED_DENSE` (`s8_corr7()` + packed GEMV call sites); additive only. **+87 / −0**. (2) 09-06: the RoPE beyond-table fallback calls `rope_trig::sincosf_cuda` instead of `std::sin`/`std::cos`, so the binary imports no libm math symbol. **+12 / −3** |
| `model_opt.h` | `cpp_infer/src/opt/model_opt.h` | verbatim | — | — |
| `qmat_dense.cpp` | `cpp_infer/src/opt/qmat_dense.cpp` | **modified** | 2026-08-31, 09-01 | packed-arena epilogues `qgemv_packed_add`/`_relu2q`/`_quant_bias` under `FX2_PACKED_DENSE`; additive only. **+97 / −0** |
| `qmat_dense.h` | `cpp_infer/src/opt/qmat_dense.h` | **modified** | 2026-08-31, 09-01 | declarations for the three packed epilogues; additive only. **+12 / −0** |
| `qmat.h` | `cpp_infer/src/opt/qmat.h` | verbatim | — | — |
| `rope_trig.h` | zmix-authored; contains a verbatim excerpt of `cpp_infer/src/weights_io_compressed.cpp:167-255` | **derived** | 2026-09-06 | the bit-exact CUDA-libdevice `__nv_sinf`/`__nv_cosf` port re-published as a header so `model_opt.cpp`'s RoPE fallback can use it instead of libm `sincosf`; only namespace + `inline` linkage added |
| `qmat_sparse.cpp` | `cpp_infer/src/opt/qmat_sparse.cpp` | verbatim | — | — |
| `qmat_sparse.h` | `cpp_infer/src/opt/qmat_sparse.h` | verbatim | — | — |
| `sparse_acts.h` | `cpp_infer/src/opt/sparse_acts.h` | verbatim | — | — |
| `vec_math.h` | `cpp_infer/src/opt/vec_math.h` | verbatim | — | — |
| `weights_io_compressed.cpp` | `cpp_infer/src/weights_io_compressed.cpp` | **modified** | 2026-08-31, 09-03 | a reader for the zmix `FX2TFWC3` container added under `-DFX2_WEIGHTS_V3=1`; the `FX2TFWC1`/`FX2TFWC2` paths are upstream's. **+257 / −0** |
| `weights_io.cpp` | `cpp_infer/src/weights_io.cpp` | verbatim | — | — |
| `weights_io.h` | `cpp_infer/src/weights_io.h` | **modified** | 2026-08-31, 09-03 | the `load_compressed()` doc comment updated to describe `FX2TFWC3`; no declaration changed. **+5 / −3** |

⚠ The line counts above exclude each file's own modification-notice block (10 lines for a modified
file, 9 for a derived one), which is a comment and emits no code.

---

## 2. `cmix` — Byron Knoll — GPL-3

zmix is a Zig **port** of cmix. The C++ sources this port follows are shipped for correspondence
review at `reference/cmix-src/` (coder, contexts, mixer, models, preprocess, states). The accepted
record `cmix-lex` (Ibrahim Marcouch, Kaido Orav, Byron Knoll) is the lineage whose Form-1
packaging and temporary-file usage this entry follows as precedent.

## 3. `fxcm` / `fx2-cmix` — Kaido Orav (`kaitz`) — GPL-3

The `fxcm_v26` text model. Ported at `src/models/fxcm26/`; the reference C++ is shipped at
`reference/fxcmv1_v26.cpp`, `reference/fxcmv1_v26.h`, `reference/fxcm_v26_standalone.cpp` with its
own readme at `reference/fxcmv1_v26_readme.txt`.

## 4. Components reached through the cmix/fxcm lineage

These are not separately vendored by zmix — they are re-implementations of models that cmix and
fxcm already carry, and they are covered by the same GPL-3 combined licence. Named because
attribution is owed to their authors, not because a separate licence applies.

| component | in this package | author |
|---|---|---|
| PPMd variant H / `mod_ppmd_v2` | `src/models/ppmd.zig` | Dmitry Shkarin, adapted by Eugene Shelwien |
| PAQ8 model set | `src/models/paq8/` | Matt Mahoney and the PAQ8 contributors |
| `phda9` preprocessor | `src/prepr/phda9.zig` | Alexander Rhatushnyak |
| WRT dictionary transform | `src/prepr/` | Przemysław Skibiński (WRT/PAsQDa lineage), as carried by cmix/fxcm |

## 5. Build tools — not distributed here, fetched by the build

Neither is part of this package or of the scored bytes; both are named because the build resolves
them and their versions are pinned exactly (`SHIP_RECIPE.env`).

| tool | version | licence | how obtained |
|---|---|---|---|
| Zig compiler | 0.15.1 (exact) | MIT | upstream release tarball, sha256-pinned in `tools/provision_zig.sh` |
| UPX packer | 5.2.0 (exact) | GPL-2-or-later with the UPX stub exception | built from source, sha256-pinned in `tools/build_upx.sh` |

## 6. zmix

Everything not listed above. **GPL-3-or-later**, see `LICENSES/GPL-3.0.txt` and `LICENSE`.
