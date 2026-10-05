# assets/ — binary assets shipped WITH THE SOURCE

⭐ **WHICH WEIGHTS BLOB THE ARTIFACTS CARRY.** Three transformer weight blobs are present in this
package and **exactly one is built into `comp9` and `archive9.exe`**:

| file | bytes | shipped? |
|---|---:|---|
| `6m-q4-fp32.tfwc2` | 2,930,652 | no — the upstream reference blob, kept for provenance |
| `6m-q4-fp32.tfwc3` | 2,840,417 | no — the same upstream values in zmix's v3 container |
| **`6m-q4-fp32-t1lambda1.tfwc3`** | **2,815,630** | ⭐ **YES** — see the last section of this file |

The authority is `SHIP_RECIPE.env`'s `ZMIX_TFWEIGHTS` / `ZMIX_TFWEIGHTS_SHA256`, asserted by
`construct_ship.sh` before anything builds and re-checked by `build.sh` against `ARTIFACT_PIN.env`'s
`EXPECT_TFW` in the judge's own container.

## `6m-q4-fp32.tfwc2` — gen-7 frozen transformer weights, upstream (NOT shipped)

| | |
|---|---|
| size | 2,930,652 B |
| sha256 | `7f4db6c8c843a7e6264b6a48ed4805e9e431f543df7a9a0ecb37a35a5e4b8860` |
| magic | `FX2TFWC2` (`pysrc/weights_compress.py:47,192`) |
| origin | `fx2-cmix-transformer` (Vladimir Ivanov), `models/6m-q4-fp32.tfwc2`, **verbatim** |
| licence | GPL-3, with attribution. Building on a prior entry's published work is permitted by its licence, and zmix is open-sourced with the submission. |

**Why it lives in the source tree.** It is handled exactly as
`src/models/fxcm26/goldens/english.dic` (412 KB) and `src/prepr/new_article_order_asset`
(1.09 MB) are: an asset the build and the construct need, committed so that a
**rebuild from source reproduces the artifact on any machine**. The committee rebuilds
comp9 from source and books S off *its* rebuild, so an asset resolved from a path
outside the tree is a submission blocker, not a convenience.

⛔ **Never re-introduce an absolute default for this path.** `build.zig`'s
`-Dtransformer-weights` default is the CWD-relative `assets/6m-q4-fp32.tfwc2`. Its
absolute predecessor was a path on the build machine, baked into `decomp_bin`
(which Form-1 charges **twice**), and it aborted the hermetic-path gate.

Resolution order at run time (`src/predictor_lex.zig`):
1. `Transformer.embedded_blob` — the artifact's own tail. **Every judged op takes this.**
2. `Transformer.weights_path_override` — the explicit 4th argv of `zmix_ship -c/-d`,
   which `construct_ship.sh` passes at asset-compression time (a bare engine has no tail).
3. the `-Dtransformer-weights` string — dev builds and the bench CLI only.

## `6m-q4-fp32.tfwc3` — the same upstream weights in the v3 container (NOT shipped)

| | |
|---|---|
| size | 2,840,417 B (**−90,235 B** vs the `.tfwc2` above; Form-1 charges it **2×**) |
| sha256 | `c8919e6e1a7d4ce1d70330f8f88dff4436958282de2d1958c2c260751da5166f` |
| magic | `FX2TFWC3` (`experiments/gen7-weights-v3/wcode3.py`) |
| origin | re-encoded from `6m-q4-fp32.tfwc2` by `experiments/gen7-weights-v3/build_blobs.py` |
| needs | `-Dtf-weights-v3=true` (else the loader dies `bad magic`) |
| licence | as above — same weights, a different container |

**It is not bit-identical to the v2 blob's tensors.** The 111 int4 weight tensors, the
230 bf16 row-scales, `rope.*` and `config.*` are unchanged; the **88 raw trained f32
tensors (28,281 values) are carried as bfloat16** and expanded `bits << 16` at load —
**+0.00004 nats/token** on the reference's own eval window
(measured one-variable, arm `bf16raw`). Everything else
in the −90,235 B is lossless recoding.

Regenerate and re-verify (needs numpy and the decoded `weights.bin`):

    cd experiments/gen7-weights-v3 && python3 build_blobs.py     # writes the blob
    g++ -O2 -std=c++17 -DFX2_WEIGHTS_V3=1 -I../../third_party/fx2_transformer \
        -o wtest wtest_v3.cpp ../../third_party/fx2_transformer/weights_io.cpp \
        ../../third_party/fx2_transformer/weights_io_compressed.cpp
    ./wtest ../../assets/6m-q4-fp32.tfwc3 6m-q4-fp32.bf16rounded.tfwc2   # must print PASS

## `6m-q4-fp32-t1lambda1.tfwc3` — **THE SHIPPED WEIGHTS BLOB** (gen-7 RETRAINED transformer weights)

⭐ **This is the blob the submitted artifacts carry.** `SHIP_RECIPE.env` names it
(`ZMIX_TFWEIGHTS="assets/6m-q4-fp32-t1lambda1.tfwc3"`) and pins its sha
(`ZMIX_TFWEIGHTS_SHA256`); `construct_ship.sh` section 0-pin-b asserts the pin before anything
builds; `submission/hpja/artifact_pin.env` records the resulting `comp_tfweights` segment as
`EXPECT_TFW=2815630`; and `build.sh` re-checks it inside the judge's build container. The two
blobs above are **not** shipped — they are kept so the derivation below is reviewable end to end.

| | |
|---|---|
| size | **2,815,630 B** |
| sha256 | `8e8ef3acacfb84437868035923bf9987f9adc826d2c833fb828204d2ab9c807d` |
| magic | `FX2TFWC3` — the same container as `6m-q4-fp32.tfwc3`, so **the decoder is untouched and there is no decoder fee** |
| where it appears | `comp9`'s fifth segment (`comp_tfweights`, copied verbatim) **and** `archive9.exe`'s — Form-1 charges it **2×**, i.e. 5,631,260 B of `S`, 89.5 % of the fixed cost |
| licence | **GPL-3**, as a derived work of `fx2-cmix-transformer` (Vladimir Ivanov) — see `NOTICE.md` and `THIRD_PARTY_LICENSES.md` section 1a |

### Provenance chain — a digest at every link

It carries **retrained** parameters, not Ivanov's trained parameters, but it derives from his
GPL-3 project at every step: the architecture, the training code and recipes, the corpus
pipeline, the quantizer and the `FX2TFWC2` container writer are all his.

| # | link | bytes | sha256 |
|---|---|---:|---|
| 1 | `t1-lambda1-fp32.tch` — the entrant's fp32 retraining checkpoint. Same 12-layer / 5,923,228-parameter architecture; trained with the upstream project's own GPL-3 training code (`src/pysrc/`, `src/training_recipes/`) on the same post-WRT token stream; the `λ*` arm adds a weight-entropy penalty to the loss (`L_train = CE + multiplier·λ*·soft_bits_per_weight`) so the *container* gets cheaper at equal cross-entropy | 23,871,037 | `61f1d703eb11ba69df98ea0a605f84686b96055da494a49bc0756a26f7701b47` |
| 2 | `models/t1-lambda1.tfwc2` — exported through the upstream project's own quantizer and container writer (`pysrc/weights_compress.py`), magic `FX2TFWC2` | 2,900,961 | `4fab46d5bcf51551c802f8d0a4776ec3c90574f202dab5c576d07e84df650406` |
| 3 | **`assets/6m-q4-fp32-t1lambda1.tfwc3`** — re-containered by zmix with `experiments/gen7-weights-v3/wcode3.py`, magic `FX2TFWC3`: a lossless recoding of the 111 int4 weight tensors and the bf16 row-scales, with the 88 raw trained f32 tensors carried as bfloat16 and expanded `bits << 16` at load | **2,815,630** | **`8e8ef3ac…c807d`** |

Origin of link 1 and link 2: the entrant's own GPU training lane, copied out read-only and
sha256'd on arrival.

**Link 1→2 is verified, not asserted.** Every one of the **5,868,864** int4 weights in the
`.tfwc2` reproduces from the `.tch` through the upstream project's own
`pysrc.export_weights.quantize_weight_rows`: **0 mismatches of 5,868,864**. So the container is
that checkpoint's quantization and there is no container/checkpoint mix-up.

**Link 2→3 is a container change only.** The trained values are the same; `armc_prefix`, the
packed decoder, is **byte-identical** whether the build is handed this blob or the shipped-entry
one — which is the measurement, not the argument, that the blob is a runtime asset rather than a
compiler input. That reading was **160,772 B, sha `1b217ccd…`** on the v5-1…v5-4 engine and is
**160,884 B, sha `8cf9e8c1…`** on the libm-hardened engine (the RoPE libm-fallback change:
`+112 B` of packed decoder, `+224 B` of S). ⚠ **The prefix moves with the
ENGINE, never with the blob** — that is the whole point of the statement, so quote the reading for
the candidate you are building, not the one you last read.

### Why it is the ship blob, measured

It was measured one-variable against the
shipped-entry blob on the same engine: **−10,318 B at the 20 MB dict tier** (pre-registered bar
−3,000), −705 at 1 MB, −51 at 50 kB, S1 windows −0.0038/−0.0045 nats on our own stream, roundtrips
lossless. The container is **24,787 B smaller per copy**, which Form-1 charges **twice** ⇒
**−49,574 B of fixed `S`** on top of the payload gain. The sibling candidate `t1-base` was measured
too and is **dominated** — same payload, container +6,848 B of `S` — so its blob is deliberately
not committed; it is regenerable from the training checkpoint in ~25 s.

### Regenerate and re-verify

    # link 2 -> link 3, from the .tfwc2 (needs numpy)
    cd experiments/gen7-weights-v3 && python3 wcode3.py <path>/t1-lambda1.tfwc2 \
        ../../assets/6m-q4-fp32-t1lambda1.tfwc3
    sha256sum ../../assets/6m-q4-fp32-t1lambda1.tfwc3   # 8e8ef3ac…c807d

    # decode-side check, same as for the .tfwc3 above
    g++ -O2 -std=c++17 -DFX2_WEIGHTS_V3=1 -I../../third_party/fx2_transformer \
        -o wtest wtest_v3.cpp ../../third_party/fx2_transformer/weights_io.cpp \
        ../../third_party/fx2_transformer/weights_io_compressed.cpp
    ./wtest ../../assets/6m-q4-fp32-t1lambda1.tfwc3 <the matching bf16-rounded .tfwc2>
