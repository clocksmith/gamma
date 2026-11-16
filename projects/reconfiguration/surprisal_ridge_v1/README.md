# Training-Free Surprisal-Ridge & Shared-Hyperbasis Prompt Transformations (`surprisal_ridge_v1`)

## Status and Summary

- **Track:** Gamma Track B1 — Prompt-conditioned weight transformation (**strictly training-free**; base weights untouched; zero continual pretraining).
- **Capability:** Evaluates four genuinely distinct training-free prompt-conditioned low-rank weight operators across three multi-token domains (`kv_registry`, `cipher_codebook`, `state_trace`) and three model scales / runtimes (`Qwen2.5-0.5B-Instruct` on PyTorch MPS, `Qwen3-0.6B` frozen backbone on PyTorch MPS, and hybrid linear-attention `Qwen3.5-2B` Q4K on Doppler WebGPU), deriving every adapter strictly from `context_text` (`query_text` and answers never enter fast-weight derivation):
  1. `unembed_surprisal_ridge` ([`transforms.py`](transforms.py)): Single-forward GPU-resident derivation at the final FFN `down_proj` using frozen LM-head next-token surprisal residuals on the top-$r$ novel context positions ($r = 24$) via closed-form dual kernel ridge.
  2. `shared_hyperbasis_lora` ([`transforms.py`](transforms.py)): Shared GPU basis operator that computes **one** orthonormal output basis $U_{\text{shared}} \in \mathbb{R}^{d \times r}$ on GPU (`gpu_thin_qr`) from prompt surprisal residuals and pairs it by reference with lightweight per-layer input keys $V_\ell$ across the final four FFN layers (`43%` smaller multi-layer footprint than independent rank-$r$ adapters).
  3. `prompt_nll_ridge_lora` ([`transforms.py`](transforms.py)): Context-only causal NLL gradient pass (with `requires_grad_(False)` on all base parameters) fitting closed-form dual-ridge rank-$r$ adapters across four evenly spaced FFN `down_proj` layers.
  4. `contextual_ridge_r8` ([`evaluate_doppler_2b.mjs`](evaluate_doppler_2b.mjs)): Cross-runtime 2B Doppler WebGPU transfer rule fitting multi-position rank-8 dual kernel ridge over top-8 hidden-state transition positions via `prefillForLoRATraining` + `finalizeLoRAAdapter`.
- **Current Status (Multi-Domain & Cross-Model-Size Evaluation on Uncontended Mars Hardware):**
  - **[✓] Base immutability & zero-adapter parity (`PASS`):** `0.0` base-weight canary norm drift across all PyTorch MPS runs; `zero_adapter` matched `base` first-token logits to `< 10^{-4}` on MPS and `< 0.01` on Q4K WebGPU (`100%` exact decoded parity).
  - **[✗] Quality improvement over frozen `base` (`FAIL / NO GAIN ESTABLISHED`):** Across **four complete multi-arm runs (`64` discriminative cases, `480` transform/control evaluations)** spanning `0.5B` (`seed=729301`, `seed=739401`), `0.6B` (`seed=759601`), and `2B` (`seed=839501`), every training-free weight transform matched `base` net accuracy (`12/24` vs `12/24` on `0.5B` `seed=729301`; `12/24` vs `12/24` on `0.5B` `seed=739401`; `11/24` vs `11/24` on `0.6B` `seed=759601`; `14/16` vs `14/16` on `2B` `seed=839501`), nor did any transform separate from `wrong_context` (`12/24`, `12/24`, `11/24`, `14/16`) or `random_low_rank` (`12/24`, `12/24`, `11/24`, `14/16`).
  - **[✗] Cost-adjusted latency vs `base` and `matched_compute_base` (`SLOWER`):** Setup overhead increased total per-request latency by **`2.07x–3.47x`** (`0.503s -> 1.070..1.640s` on `0.5B`; `0.812s -> 1.756..2.815s` on `0.6B`; `8.781s -> 17.998s` on `2B`). On `2B` `cipher_codebook`, two-pass half-context `matched_compute_base` scored **`8 / 8`** (`13.76s`, `0` update bytes), beating both `base` (`7 / 8`) and `contextual_ridge_r8` (`7 / 8`, `24.39s`).
  - **Conditional Fusion Decision:** Although `unembed_surprisal_ridge` and `shared_hyperbasis_lora` already derive `(U, V)` entirely on-device (`gpu_thin_qr` + GPU `linalg.solve`), deeper single-prefill kernel/KV-reuse fusion was **not** pursued because zero quality improvement was observed on any domain or model size (honoring the contract: *"Investigate GPU-resident derivation and fusion only where evidence supports it"*).

Separate trained-checkpoint evaluation (`Qwen3-0.6B-NHS`, `209,715,200` nominal continual-pretraining tokens + seven trained `ttt_proj` matrices) is isolated in [`../ttt_ntp_baseline/`](../ttt_ntp_baseline/README.md) and is never grouped with these training-free transforms.

---

## Domains, Controls, and Preserved Gate Receipts

### Three Fresh Multi-Token Executable Domains ([`tasks.py`](tasks.py))

1. `kv_registry`: `110` random `id_xxxxxxxx = tok_xxxxxx-xxxxxx` records (`~2,650` tokens), balanced early/middle/late needle depths, free completion stopping at `\n`.
2. `cipher_codebook`: `48` session-specific nonce lexicon rules (`term_xxxx maps to <syl>-<syl><d>`), outputting `CIPHER=<syl>-<syl><d>` (synthesized string verified absent from `context_text`).
3. `state_trace`: `22` mutable registers (`SET REG_xx = <syl><dd>`) followed by `20` ordered state overrides (`UPDATE REG_xx = <syl><dd>`), outputting `STATE=<syl><dd>` (synthesized string verified absent from `context_text`).

### All Executed Receipts and Discrimination Gates

Every run was executed sequentially on Mars (`mac`) with `ps` verified clear of Track A GPU jobs:

| Receipt | Model & Runtime | Seed | Domain Gates (`kv` / `cipher` / `state`) | Outcome & Notes |
| :--- | :--- | ---: | :--- | :--- |
| [`.work/surprisal-ridge-qwen05b-01.json`](../../../.work/surprisal-ridge-qwen05b-01.json) (`57d19984...`) | `Qwen2.5-0.5B-Instruct` (MPS `fp16`, chat) | `718201` | `0/12`, `0/12`, `0/12` | Halted before transform arms per non-floor gate (chat-template preambles truncated `tok_` at 24 tokens). Preserved untouched. |
| [`.work/surprisal-ridge-qwen05b-raw-01.json`](../../../.work/surprisal-ridge-qwen05b-raw-01.json) (`6785c355...`) | `Qwen2.5-0.5B-Instruct` (MPS `fp16`, raw) | `729301` | `0/12` (`fp16` NaN at `2.6k`), **`8/12`**, **`4/12`** | Completed all 8 arms across `24` qualified cases (`204` rows). |
| [`.work/surprisal-ridge-qwen05b-bf16-01.json`](../../../.work/surprisal-ridge-qwen05b-bf16-01.json) (`dbb6c19a...`) | `Qwen2.5-0.5B-Instruct` (MPS `bf16`, raw) | `739401` | `0/12` (`sdpa` pre-norm bug), **`6/12`**, **`6/12`** | Completed all 8 arms across `24` qualified cases (`204` rows). |
| [`.work/surprisal-ridge-qwen05b-eager-01.json`](../../../.work/surprisal-ridge-qwen05b-eager-01.json) (`bd758e9b...`) | `Qwen2.5-0.5B-Instruct` (MPS `bf16` `eager`) | `749501` | **`8/12`**, **`8/12`**, **`3/12`** | Proved all 3 domains discriminative on `0.5B`; `eager` backward hit MPS `30.19 GiB` ceiling on `2,670`-token `prompt_nll_ridge_lora` (`sdpa` + `empty_cache()` fixed memory to `4.07 GB`). |
| [`.work/surprisal-ridge-qwen06b-sdpa-01.json`](../../../.work/surprisal-ridge-qwen06b-sdpa-01.json) (`7da8e109...`) | `Qwen3-0.6B` frozen backbone (MPS `bf16` `sdpa`)* | `759601` | `0/12`, **`10/12`**, **`1/12`** | Completed all 8 arms across `24` qualified cases (`204` rows, peak MPS `4,069.6 MB`). *Note: `Qwen3-0.6B-NHS` backbone loaded without `ttt_proj`; CPT provenance noted.* |
| [`.work/surprisal-ridge-doppler-2b-01.json`](../../../.work/surprisal-ridge-doppler-2b-01.json) (`c9413909...`) | `Qwen3.5-2B` Q4K (Doppler WebGPU `f32`) | `839501` | `8/8` (ceiling), **`7/8`**, **`7/8`** | Completed all 6 arms across `16` non-ceiling `2B` transfer cases (`104` rows, peak RSS `2,111.5 MB`). |

---

## Quality, Latency, and Memory Results

### 1. PyTorch MPS `0.5B` (`Qwen2.5-0.5B-Instruct`, Untouched Off-the-Shelf) & `0.6B` (`Qwen3-0.6B` Frozen Backbone)

| Model & Seed | Arm | Accuracy (`cipher` / `state` / Total) | Mean Setup (s) | Mean First Token (s) | Mean Decode (s) | Mean Total (s) | Update Bytes | Peak MPS / RSS (MB) |
| :--- | :--- | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0.5B` (`729301`, `fp16`) | `base` | `8/12` + `4/12` = **`12/24`** (`50.0%`) | `0.000` | `0.341` | `0.144` | **`0.486`** | `0` | `5,110.9` / `2,497.0` |
| `0.5B` (`729301`, `fp16`) | `zero_adapter` | `8/12` + `4/12` = `12/24` (`50.0%`) | `0.502` | `0.871` | `0.163` | `1.035` | `276,480` | `11,438.2` / `2,501.8` |
| `0.5B` (`729301`, `fp16`) | `unembed_surprisal_ridge` | `8/12` + `4/12` = `12/24` (`50.0%`) | `0.494` | `0.860` | `0.160` | `1.020` | `276,480` | `11,119.1` / `2,501.8` |
| `0.5B` (`729301`, `fp16`) | `shared_hyperbasis_lora` | `8/12` + `4/12` = `12/24` (`50.0%`) | `0.505` | `0.864` | `0.162` | `1.026` | **`651,264`** | `11,119.1` / `2,501.8` |
| `0.5B` (`729301`, `fp16`) | `prompt_nll_ridge_lora` | `8/12` + `4/12` = `12/24` (`50.0%`) | `1.080` | `1.443` | `0.171` | `1.615` | `737,280` | `11,446.0` / `2,501.8` |
| `0.5B` (`729301`, `fp16`) | `wrong_context_surprisal` | `8/12` + `4/12` = `12/24` (`50.0%`) | `1.085` | `1.456` | `0.158` | `1.614` | `276,480` | `11,401.9` / `2,501.8` |
| `0.5B` (`729301`, `fp16`) | `random_low_rank` | `8/12` + `4/12` = `12/24` (`50.0%`) | `0.498` | `0.863` | `0.163` | `1.026` | `276,480` | `11,401.9` / `2,501.8` |
| `0.5B` (`729301`, `fp16`) | `matched_compute_base` | `8/12` + `3/12` = `11/24` (`45.8%`) | `0.000` | `0.211` | `0.474` | `0.685` | `0` | `11,446.6` / `2,501.8` |
| `0.5B` (`739401`, `bf16`) | `base` | `6/12` + `6/12` = **`12/24`** (`50.0%`) | `0.000` | `0.350` | `0.153` | **`0.503`** | `0` | `5,112.0` / `1,167.9` |
| `0.5B` (`739401`, `bf16`) | `unembed_surprisal_ridge` | `6/12` + `6/12` = `12/24` (`50.0%`) | `0.509` | `0.891` | `0.179` | `1.070` | `276,480` | `13,545.3` / `1,167.9` |
| `0.5B` (`739401`, `bf16`) | `shared_hyperbasis_lora` | `6/12` + `6/12` = `12/24` (`50.0%`) | `0.536` | `0.919` | `0.198` | `1.117` | **`651,264`** | `13,545.3` / `1,167.9` |
| `0.5B` (`739401`, `bf16`) | `prompt_nll_ridge_lora` | `6/12` + `6/12` = `12/24` (`50.0%`) | `1.051` | `1.427` | `0.213` | `1.640` | `737,280` | `13,545.3` / `1,167.9` |
| `0.5B` (`739401`, `bf16`) | `matched_compute_base` | `6/12` + `3/12` = `9/24` (`37.5%`) | `0.000` | `0.230` | `0.542` | `0.772` | `0` | `13,545.3` / `1,167.9` |
| `0.6B` (`759601`, `bf16`) | `base` | `10/12` + `1/12` = **`11/24`** (`45.8%`) | `0.000` | `0.553` | `0.259` | **`0.812`** | `0` | `4,069.6` / `1,699.8` |
| `0.6B` (`759601`, `bf16`) | `unembed_surprisal_ridge` | `10/12` + `1/12` = `11/24` (`45.8%`) | `0.804` | `1.473` | `0.303` | `1.775` | `196,608` | `4,069.6` / `1,699.8` |
| `0.6B` (`759601`, `bf16`) | `shared_hyperbasis_lora` | `10/12` + `1/12` = `11/24` (`45.8%`) | `0.810` | `1.464` | `0.293` | `1.756` | **`425,984`** | `4,069.6` / `1,699.8` |
| `0.6B` (`759601`, `bf16`) | `prompt_nll_ridge_lora` | `10/12` + `1/12` = `11/24` (`45.8%`) | `1.844` | `2.518` | `0.298` | `2.815` | `524,288` | `4,069.6` / `1,699.8` |

Note on `shared_hyperbasis_lora` memory compactness: across 4 layers on `0.6B` (`d_hidden = 1024`, `d_inter = 3072`, `r = 16`), sharing one $U_{\text{shared}} \in \mathbb{R}^{1024 \times 16}$ across all 4 layers uses `425,984` bytes vs `524,288` bytes for 4 independent rank-16 adapters (`589,824` -> `651,264` vs `1,105,920` at equal layer width on `0.5B`).

### 2. Cross-Model-Size & Cross-Runtime Transfer on `2B` (`Qwen3.5-2B` Q4K, Doppler WebGPU, `seed=839501`)

On `2B`, `kv_registry` hit `8/8` base ceiling (`discriminative = false`, skipped per gate), while `cipher_codebook` (`7/8` base) and `state_trace` (`7/8` base) qualified (`16` discriminative tasks):

| Arm | `cipher_codebook` | `state_trace` | Total Accuracy | Mean Setup (s) | Mean First Token (s) | Mean Decode (s) | Mean Total (s) | Logical Update Bytes | Peak RSS (MB) |
| :--- | :---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `base` | `7 / 8` | **`7 / 8`** | **`14 / 16`** (`87.5%`) | `0.000` | `8.433` | `0.348` | **`8.781`** | `0` | `2,111.5` |
| `zero_adapter` | `7 / 8` | `7 / 8` | `14 / 16` (`87.5%`) | `8.483` | `17.361` | `0.356` | `17.717` | `262,144` | `2,111.5` |
| `contextual_ridge_r8` | `7 / 8` | `7 / 8` | `14 / 16` (`87.5%`) | `8.483` | `17.610` | `0.388` | `17.998` | `262,144` | `2,111.5` |
| `wrong_context_r8` | `7 / 8` | `7 / 8` | `14 / 16` (`87.5%`) | `16.966` | `25.975` | `0.360` | `26.335` | `262,144` | `2,111.5` |
| `random_r8` | `7 / 8` | `7 / 8` | `14 / 16` (`87.5%`) | `8.484` | `17.610` | `0.380` | `17.990` | `262,144` | `2,111.5` |
| `matched_compute_base` | **`8 / 8`** | `5 / 8` | `13 / 16` (`81.2%`) | `0.000` | `5.404` | `6.187` | `11.592` | `0` | `2,111.5` |

---

## Mechanistic Diagnosis: Why Training-Free Context-Only Fast Weights Yield Zero Gain

1. **Mismatch between context-token keys and query-time keys:** All three training-free operators (`unembed_surprisal_ridge`, `shared_hyperbasis_lora`, `prompt_nll_ridge_lora`) map context FFN activations $a_t$ at high-surprisal context positions $t \in \text{context}$ toward local next-token prediction directions. During query decode (`Encode term_xxxx =>` or `READ REG_xx =>`), the FFN activation $a_{\text{query}}$ lives in the *query-continuation* subspace rather than repeating the raw context token prefix $a_t$, so $V a_{\text{query}}$ has near-zero cosine overlap with the fitted ridge keys under safe perturbation caps ($\eta_{\max} \in [0.025, 0.08]$), while larger $\eta_{\max}$ corrupts general token emission without continual pretraining of a dedicated key/value alignment projection.
2. **Attention/context partitioning (`matched_compute_base`) directly addresses distractor interference when rules are independent:** On `2B` `cipher_codebook`, splitting 48 lexicon rules into two 24-rule passes (`matched_compute_base`) lifted accuracy from `7/8` to `8/8` at `13.76s` (`1.77x` faster than `contextual_ridge_r8` at `24.39s`), whereas on sequential `state_trace` splitting `UPDATE` logs degraded accuracy (`7/8 -> 5/8`) because state transitions are order-dependent.

---

## Reproduction Commands

### Query-aware state context controls

Both runners accept `--context-only` to compare full context, the existing
blind two-window baseline and a query-directed dependency slice. The shared
compiler lives in [`src/core/state_context.py`](../../../src/core/state_context.py);
Doppler consumes the same Python-generated prompts and source references,
rather than implementing a second parser. The compiler never receives expected
answers. This is a symbolic preprocessing capability, separate from all
weight-transform and heredity claims above. Every state case runs; the original
weight-transform discrimination gates and default task inputs remain unchanged.

```bash
.venv/bin/python projects/reconfiguration/surprisal_ridge_v1/evaluate_mps.py \
  <LOCAL_HF_MODEL_DIR> .work/state-context-new.json --context-only \
  --device cpu --seed 174619 --cases-per-domain 4 --state-updates 512

node projects/reconfiguration/surprisal_ridge_v1/evaluate_doppler_2b.mjs \
  <DOPPLER_ROOT> <LOCAL_2B_MODEL> .work/state-context-doppler-new.json --context-only
```

Add `--prepare-only` to the Doppler command to exercise the real compiler bridge
and write prepared prompts without importing WebGPU or running a model. This
does not establish runtime parity or model quality. The Python runner supports
either CPU or a separately reserved MPS device. No command downloads weights.
`--state-updates` explicitly changes the history length; its default of 20 keeps
historical inputs unchanged. Tokenization and compaction are charged in request
latency. Blind selection requires both decoded windows, so its selected first
token becomes available only at selection, not at the first window's first token.

#### Bounded CPU implementation check, 2026-11-16

Existing local `Qwen3-0.6B-NHS` backbone, FP32 CPU, four threads, raw prompts,
24-token greedy cap; arm order rotated per case. The unused trained `ttt_proj`
weights were not applied. These are generated structured-log engineering cases,
not evidence for B1 adaptation, B2 heredity or general model improvement.

| History | Cases | Full correct | Blind correct | Slice correct | Total prompt tokens: full / blind / slice |
| --- | ---: | ---: | ---: | ---: | ---: |
| [20 updates](context_preprocessing_cpu_20261116.json), seed 164203 | 8 | 3/8 | 3/8 | 7/8 | 3,536 / 5,472 / 496 |
| [512 updates](context_preprocessing_cpu_20261116.json), seed 174619 | 4 | 0/4 | 0/4 | 3/4 | 21,448 / 22,416 / 248 |

In the long-history check, mean resident-request time including tokenization and
compaction was **10.713s full, 10.665s blind and 0.393s slice**. Model loading is
reported separately. The short check's initial timer summed decoder intervals
and setup rather than measuring the complete wrapper; its latency is not used
for this comparison. These small runs are not isolated-machine qualification.

Independent full replay verifies the requested state in every retained context;
the two model misses copied an unrelated `READ` example despite retaining the
correct state. `--read-state` answers the supported grammar exactly without an
LLM. CPU regression checks also cover 640 queried states across randomized
500-event histories with overwrites, copies and arithmetic, and unchanged
fallback for unknown syntax. The Doppler consumer's real `--prepare-only` bridge
ran, but its WebGPU/model execution was not exercised in this implementation
check. Existing default task inputs and weight-transform acceptance rules remain
unchanged.

### Weight-transform reproduction

```bash
# 1. Unit tests (task answer-isolation oracles, shared-hyperbasis pointer sharing, zero-adapter identity, base weight immutability)
.venv/bin/python -m unittest projects/reconfiguration/surprisal_ridge_v1/test_surprisal_ridge.py

# 2. Multi-domain PyTorch MPS evaluation (exclusive output path)
.venv/bin/python projects/reconfiguration/surprisal_ridge_v1/evaluate_mps.py \
  <LOCAL_HF_MODEL_DIR> .work/surprisal-ridge-repro.json --seed 759601 --device mps

# 3. Cross-domain & 2B model-size Doppler WebGPU transfer evaluation (exclusive output path)
node projects/reconfiguration/surprisal_ridge_v1/evaluate_doppler_2b.mjs \
  /Users/xyz/deco/doppler /Users/xyz/.reploid/weights/qwen-3-5-2b-q4k-ehaf16 \
  .work/surprisal-ridge-doppler-2b-repro.json
```
