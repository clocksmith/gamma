# Closed-Form Reversible Per-Layer MLP LoRA Reconfiguration Study v4 (`query_swiglu_fastweight_v4`)

Charter: [CATSCAN.md](CATSCAN.md) | Core Protocol Lock (`Commit 1`: `a2d9988e8`): [protocol_v4.json](protocol_v4.json) | Receipts: [doppler_gemma3_270m_v4.json](../../../.work/query-swiglu-fastweight-v4/doppler_gemma3_270m_v4.json), [doppler_qwen35_08b_v4.json](../../../.work/query-swiglu-fastweight-v4/doppler_qwen35_08b_v4.json)

> **Track B1 Verdict (`N = 96` Non-Copy Tasks/Model, Unpooled Exact Two-Sided McNemar): Globally NOT MET (Model- and Target-Width-Dependent).**
>
> Under the pre-registered unpooled per-model protocol (`seed = 1040001`, `enable_string_heuristics = false`, `0/96` standalone lexical/regex lookup accuracy):
> 1. **`Gemma-3-270M-IT` (`Q4_K_M`, `postFeedforwardNorm = true`) — FAILS Both Gates; Significant Harm in Regime B (`p = 4.65e-6`):**
>    - **Regime A (Prompt-Removed Skill Retention):** `closed_form_layer_lora_no_prompt` (`alpha = 1.0`) scores **`1/96` (`1.0%`)** vs `0/96` on all four controls (`+1` win / `0` losses, exact McNemar `p = 1.0`; `alpha` curve `0, 2, 2, 3, 1` of `96` across `alpha in {0.0, 0.25, 0.50, 0.75, 1.0}`). The single-specialty development check (`0/8 -> 4/8` bare-query hits) **did not transfer** to the `6`-domain unseen confirmation suite.
>    - **Regime B (Prompt-Present Matched Compute):** `closed_form_layer_lora_in_context` (`4/96 = 4.2%`, emitting empty string `""` on `85/96` rows) **significantly harms** in-context decoding relative to `base_in_context` (`29/96 = 30.2%`, `3` wins / `28` losses, exact McNemar `p = 4.65e-6`). On `Gemma-3-270M-IT`, `base_plus_string_lookup` (`96/96` identical outputs to `base_in_context`), `continuous_cache_knn` (`96/96` identical outputs), and `context_aware_decoding` (`87/96` identical outputs) were largely or wholly inert, all scoring `29/96` with the identical `3/28` split.
> 2. **`Qwen3.5-0.8B` (`Q4_K_M`, Standard Pre-Norm Residual Stream, `postFeedforwardNorm = false`) — PASSES Regime A (`p = 2.38e-7`), FAILS Regime B (`30/96` vs `44/96` `knn`/`CAD`, `p <= 0.034`):**
>    - **Regime A (Prompt-Removed Skill Retention — PASSED):** When the `12`-line support table is completely removed at query time, `closed_form_layer_lora_no_prompt` (`alpha = 1.0`, layers `[22, 23]`) scores **`23/96` (`24.0%`, peaking at `25/96 = 26.0%` at `alpha = 0.75`)** against **`0/96` (`0.0%`)** on `base_no_prompt`, `zero_lora_no_prompt`, `wrong_specialty_lora_no_prompt`, and `random_lora_no_prompt` (`+23` wins / `0` losses vs every control, exact McNemar **`p = 2.38e-7`**), with a clean monotonic dial curve (`0 -> 2 -> 14 -> 25 -> 23` of `96`).
>    - **Regime B (Prompt-Present Matched Compute — NOT MET):** Across all `96` tasks, `closed_form_layer_lora_in_context` scores **`30/96` (`31.3%`)**, trailing `base_in_context` (`41/96 = 42.7%`, `15W/26L`, `p = 0.117`), `base_plus_string_lookup` (`41/96`, inert `96/96` fallback to `base_in_context`), and losing significantly to **`continuous_cache_knn` (`44/96 = 45.8%`, `11W/25L`, `p = 0.0288`)** and **`context_aware_decoding` (`44/96 = 45.8%`, `12W/26L`, `p = 0.0336`)**, while leading `base_chat` (`22/96 = 22.9%`, `26W/18L`, `p = 0.291`).
> 3. **Quantized WebGPU Bit-Exact Reversibility & Diagnostic Scope Boundary:**
>    - On both quantized `Q4_K_M` models (`192/192` total task rows), `zero_lora_no_prompt` (`scale = 0.0`) and `reverted_after_hotswap_no_prompt` (after `Specialty A -> Specialty B -> detach`) achieve **`max_abs_logit_diff = 0.0`** bit-for-bit against unmodified `base_no_prompt`.
>    - Post-hoc diagnostic split on `Qwen3.5-0.8B` (explanatory, not a primary gate): all `23` Regime A wins (`23/64 = 35.9%` vs `0/64`) and all `30` Regime B hits (`30/64 = 46.9%` vs `22/64 = 34.4%` `base_in_context`, `25/64` `knn`, `23/64` `CAD`) occur on the **four single-token code domains**, whereas on the **two multi-token code domains (`32` tasks: `red-1`, `north/1`)**, static position-blind `down_proj` LoRA collapses to **`0/32`** (`""` on `32/32` rows) because a single static `(A_l, B_l)` cannot separate step-0 target emission from step-1+ stop/continuation dynamics.

## Literature Positioning

`v4` makes no claim of inventing continuous caches, test-time logit adjustment, or closed-form fast weights. It evaluates a specific engineering variant—forward-only ridge-compiled MLP `down_proj` LoRA (`W_l(alpha) = W_l + alpha * B_l A_l`) over quantized `Q4_K_M` WebGPU weights—against established prior mechanisms:
- **Continuous Cache & Prompt `kNN-LM`**: `Grave et al. (2017)` (*Improving Neural Language Models with a Continuous Cache*, `arXiv:1612.04426`) and `Khandelwal et al. (2020)` (*Generalization through Memorization: Nearest Neighbor Language Models*, `arXiv:1911.00172`), implemented directly as the `continuous_cache_knn` Regime B baseline (`DeltaW_l = 0`).
- **Context-Aware Decoding (`CAD`)**: `Shi et al. (2024)` (*Trusting Your Evidence: Hallucinate Less with Context-aware Decoding*, `arXiv:2305.14739`), implemented as an independent 2-pass `(1 + beta) * l_ctx - beta * l_bare` (`beta = 0.5`) matched-compute baseline.
- **Implicit Contextual MLP Updates & Closed-Form Fast Weights**: `Dherin et al. (2025)` (*Learning without training: The implicit dynamics of in-context learning*, `arXiv:2507.16003`) and `FAAST (2026)` (*Forward-Only Associative Learning via Closed-Form Fast Weights*, `arXiv:2605.04651`).

## Pre-Registration & Provenance Timeline

- **Commit 1 (`a2d9988e8`)**: Committed locally on `/Users/xyz/deco/gamma` `main` at `16:26 EST` on `2026-11-17`—freezing [adapter.py](../../../gamma/fastweight/adapter.py), [doppler_fastweight.mjs](../../../gamma/fastweight/doppler_fastweight.mjs), [pytorch_engine.py](../../../gamma/engines/native/pytorch_engine.py), [regex_baseline_v4.py](regex_baseline_v4.py), [evaluate_doppler_v4.mjs](evaluate_doppler_v4.mjs), [evaluate_v4_mps.py](evaluate_v4_mps.py), and [protocol_v4.json](protocol_v4.json) **before** [tasks_v4.py](tasks_v4.py) was created (`16:29 EST`) and before the confirmation pass (`task-881`) started (`~16:30 EST`).
- **GitHub Push Timing Caveat**: `a2d9988e8` was pushed unchanged to `origin/main` by the backup reviewer session at `16:34:40 EST`, in the same minute `doppler_gemma3_270m_v4.json` finished writing (`16:34 EST`) and ~22 minutes before `doppler_qwen35_08b_v4.json` finished (`16:56 EST`). Thus `a2d9988e8` strictly predates the run locally and predates the `Qwen3.5-0.8B` receipt on `origin/main`, while reaching GitHub concurrently with the `Gemma-3-270M-IT` receipt write. An automated workspace sync (`aaee1d8a2` at `16:36 EST`) also recorded `tasks_v4.py`, `test_v4.py`, and `doppler_gemma3_270m_v4.json` mid-run without modifying any locked file (`test_v4.py` verifies all six Commit 1 SHA-256 digests).
- **Harness Repairs Verified**:
  1. Single-pass `_prefillToHidden` + `computeLogits` across every arm (`max_abs_logit_diff(zero_lora, base) == 0.0` on all `96/96` tasks per model).
  2. Wall-clock `setup_ms` starts prior to GPU `ffn_act` / hidden-state capture and buffer readback (`1,212.5 ms`/specialty = `151.6 ms`/query amortized on `Gemma-3-270M-IT`; `3,722.8 ms`/specialty = `465.3 ms`/query amortized on `Qwen3.5-0.8B`).
  3. Zero string/regex shortcuts (`enable_string_heuristics = false`; standalone [regex_baseline_v4.py](regex_baseline_v4.py) scores `0/96 = 0.0% <= 50%`).
  4. Apple MPS `PyTorchEngine` fix: `gamma/engines/native/pytorch_engine.py` defaults to `attn_implementation="eager"` when `fastweight=True` on MPS to prevent PyTorch `sdpa` `bfloat16` `q_len=1` token-`0` corruption. (Stock `Qwen/Qwen3-0.6B` PyTorch weights are not locally provisioned on this host; per [GEMINI.md](../../../GEMINI.md), weights are not auto-downloaded.)

## Primary Per-Model Results (`N = 96` Unseen Non-Copy Tasks Each, `seed = 1040001`)

Inference is strictly unpooled per model (`exactMcNemarTwoSidedP`).

### 1. Stock `Gemma-3-270M-IT` (`Q4_K_M` WebGPU, Layers `8..17`, `postFeedforwardNorm = true`) — FAILED

| Regime & Arm (`N = 96`) | Hits / Total | Accuracy | Mean Latency (`ms`) | LoRA vs Arm (`+W / -L`, Exact 2-Sided McNemar `p`) |
| :--- | :---: | :---: | :---: | :--- |
| **Regime A: `closed_form_layer_lora_no_prompt` (`alpha = 1.0`)** | **`1 / 96`** | **`1.0%`** | `78.6` decode (`+151.6` amort. setup) | *(Primary focal arm — **GATE FAILED**)* |
| Regime A: `base_no_prompt` | `0 / 96` | `0.0%` | `136.1` | `+1 / -0` (`p = 1.000`) |
| Regime A: `zero_lora_no_prompt` (`diff = 0.0`) | `0 / 96` | `0.0%` | `136.0` | `+1 / -0` (`p = 1.000`) |
| Regime A: `wrong_specialty_lora_no_prompt` | `0 / 96` | `0.0%` | `76.9` | `+1 / -0` (`p = 1.000`) |
| Regime A: `random_lora_no_prompt` | `0 / 96` | `0.0%` | `134.8` | `+1 / -0` (`p = 1.000`) |
| Regime A: `reverted_after_hotswap_no_prompt` (`diff = 0.0`) | `0 / 96` | `0.0%` | `136.0` | Bit-exact base restoration (`0.0` max logit diff) |
| **Regime B: `closed_form_layer_lora_in_context` (`alpha = 1.0`)** | **`4 / 96`** | **`4.2%`** | `191.6` decode (`343.2` amort. total) | *(Primary focal arm — **SIGNIFICANT HARM**)* |
| Regime B: `base_in_context` | `29 / 96` | `30.2%` | `205.1` | `+3 / -28` (**`p = 4.65e-6`**, `base` wins) |
| Regime B: `base_chat` | `0 / 96` | `0.0%` | `261.2` | `+4 / -0` (`p = 0.125`) |
| Regime B: `standalone_string_lookup` | `0 / 96` | `0.0%` | `< 0.1` | Non-copy check (`0.0% <= 50%`) |
| Regime B: `base_plus_string_lookup` *(inert: `96/96 == base`)* | `29 / 96` | `30.2%` | `205.1` | `+3 / -28` (`p = 4.65e-6`, identical to `base`) |
| Regime B: `continuous_cache_knn` *(inert: `96/96 == base`)* | `29 / 96` | `30.2%` | `210.8` | `+3 / -28` (`p = 4.65e-6`, identical to `base`) |
| Regime B: `context_aware_decoding` *(2-pass; `87/96 == base`)* | `29 / 96` | `30.2%` | `658.3` | `+3 / -28` (`p = 4.65e-6`, `CAD` wins) |

- **Regime A `alpha` dial curve (`Gemma-3-270M-IT`)**: `alpha = 0.00: 0/96 (0.0%)`, `0.25: 2/96 (2.1%)`, `0.50: 2/96 (2.1%)`, `0.75: 3/96 (3.1%)`, `1.00: 1/96 (1.0%)`. Because `postFeedforwardNorm(u_0 + du)` normalizes the combined FFN vector onto an RMS sphere at every adapted layer (`8..17`), the static `stopCol` perturbation over-triggers `\n` (`85/96` empty outputs in Regime B).

### 2. Stock `Qwen3.5-0.8B` (`Q4_K_M` WebGPU, Layers `[22, 23]`, `postFeedforwardNorm = false`) — Regime A PASSED (`p = 2.38e-7`), Regime B NOT MET

| Regime & Arm (`N = 96`) | Hits / Total | Accuracy | Mean Latency (`ms`) | LoRA vs Arm (`+W / -L`, Exact 2-Sided McNemar `p`) |
| :--- | :---: | :---: | :---: | :--- |
| **Regime A: `closed_form_layer_lora_no_prompt` (`alpha = 1.0`)** | **`23 / 96`** | **`24.0%`** | `198.9` decode (`+465.3` amort. setup) | *(Primary focal arm — **REGIME A PASSED**)* |
| Regime A: `base_no_prompt` | `0 / 96` | `0.0%` | `335.5` | **`+23 / -0` (`p = 2.38e-7`)** |
| Regime A: `zero_lora_no_prompt` (`diff = 0.0`) | `0 / 96` | `0.0%` | `335.1` | **`+23 / -0` (`p = 2.38e-7`)** |
| Regime A: `wrong_specialty_lora_no_prompt` | `0 / 96` | `0.0%` | `204.2` | **`+23 / -0` (`p = 2.38e-7`)** |
| Regime A: `random_lora_no_prompt` | `0 / 96` | `0.0%` | `328.4` | **`+23 / -0` (`p = 2.38e-7`)** |
| Regime A: `reverted_after_hotswap_no_prompt` (`diff = 0.0`) | `0 / 96` | `0.0%` | `334.9` | Bit-exact base restoration (`0.0` max logit diff) |
| **Regime B: `closed_form_layer_lora_in_context` (`alpha = 1.0`)** | **`30 / 96`** | **`31.3%`** | `1,449.4` decode (`1,914.7` amort. total) | *(Primary focal arm — **REGIME B NOT MET**)* |
| Regime B: `base_in_context` | `41 / 96` | `42.7%` | `1,877.3` | `+15 / -26` (`p = 0.117`, NS) |
| Regime B: `base_chat` | `22 / 96` | `22.9%` | `1,912.6` | `+26 / -18` (`p = 0.291`, NS) |
| Regime B: `standalone_string_lookup` | `0 / 96` | `0.0%` | `< 0.1` | Non-copy check (`0.0% <= 50%`) |
| Regime B: `base_plus_string_lookup` *(inert: `96/96 == base`)* | `41 / 96` | `42.7%` | `1,877.3` | `+15 / -26` (`p = 0.117`, identical to `base`) |
| Regime B: `continuous_cache_knn` (`84/96 == base`) | **`44 / 96`** | **`45.8%`** | `1,418.3` | `+11 / -25` (**`p = 0.0288`**, `knn` wins) |
| Regime B: `context_aware_decoding` (2-pass; `71/96 == base`) | **`44 / 96`** | **`45.8%`** | `4,581.4` | `+12 / -26` (**`p = 0.0336`**, `CAD` wins) |

- **Regime A `alpha` dial curve (`Qwen3.5-0.8B`)**: `alpha = 0.00: 0/96 (0.0%)`, `0.25: 2/96 (2.1%)`, `0.50: 14/96 (14.6%)`, `0.75: 25/96 (26.0%)`, `1.00: 23/96 (24.0%)`.

## Per-Domain Breakdown (`16` Tasks / Domain = `2` Specialties x `8` Unseen Queries)

| Unseen Domain (`seed = 1040001`) | Target Format | `Gemma-3` RegA (`Base` / `LoRA`) | `Gemma-3` RegB (`Base` / `kNN` / `CAD` / `LoRA`) | `Qwen3.5` RegA (`Base` / `LoRA`) | `Qwen3.5` RegB (`Base` / `kNN` / `CAD` / `LoRA`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `semantic_clinical_specialty_triage` | 1-token (`amber`..) | `0` / `0` | `4` / `4` / `5` / `0` | `0` / **`8`** (`50%`) | `5` / `7` / `6` / **`8`** |
| `paraphrased_cloud_incident_routing` | 1-token (`maple`..) | `0` / `0` | `4` / `4` / `5` / `0` | `0` / **`6`** (`38%`) | `6` / `8` / `8` / **`9`** |
| `latent_financial_compliance_desk` | 1-token (`north`..) | `0` / `1` | `6` / `6` / `5` / `4` | `0` / **`5`** (`31%`) | `4` / `4` / `4` / **`7`** |
| `scientific_instrument_calibration` | 1-token (`harbor`..) | `0` / `0` | `5` / `5` / `5` / `0` | `0` / **`4`** (`25%`) | `7` / `6` / `5` / `6` |
| `compositional_supply_hazard_codes` | Multi-tok (`red-1`..) | `0` / `0` | `5` / `5` / `4` / `0` | `0` / `0` (`0%`) | `11` / `11` / `12` / `0` |
| `multilingual_civic_service_dispatch` | Multi-tok (`north/1`..) | `0` / `0` | `5` / `5` / `5` / `0` | `0` / `0` (`0%`) | `8` / `8` / `9` / `0` |
| **Single-Token Subtotal (`64` tasks, diagnostic)** | 1-token | `0` / `1` | `19` / `19` / `20` / `4` | `0` / **`23` (`35.9%`)** | `22` / `25` / `23` / **`30` (`46.9%`)** |
| **Multi-Token Subtotal (`32` tasks, diagnostic)** | Multi-tok | `0` / `0` | `10` / `10` / `9` / `0` | `0` / `0` (`0.0%`) | `19` / `19` / `21` / `0` (`0.0%`) |

## Reproduction

```bash
.venv/bin/python -m unittest tests/test_fastweight_parity.py projects/reconfiguration/query_swiglu_fastweight_v4/test_v4.py -v
node projects/reconfiguration/query_swiglu_fastweight_v4/evaluate_doppler_v4.mjs \
  /Users/xyz/deco/doppler-wt/a2 \
  /Users/xyz/fawn-bench-stock/assets/models/gemma-3-270m-it-q4k-ehf16-af32 \
  .work/query-swiglu-fastweight-v4/doppler_gemma3_270m_v4.json 8 1040001
node projects/reconfiguration/query_swiglu_fastweight_v4/evaluate_doppler_v4.mjs \
  /Users/xyz/deco/doppler-wt/a2 \
  /Users/xyz/deco/doppler/.cache/qwen08-sha256-repair \
  .work/query-swiglu-fastweight-v4/doppler_qwen35_08b_v4.json 8 1040001
```
