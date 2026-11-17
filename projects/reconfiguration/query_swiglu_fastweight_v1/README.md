# B1 Study v1: Prompt-Conditioned SwiGLU Fast-Weight Transformation (`query_swiglu_fastweight_v1`)

Charter: [CATSCAN.md](CATSCAN.md)

## Overview

`query_swiglu_fastweight_v1` evaluates whether a frozen causal language model can derive a compact, temporary SwiGLU fast-weight transformation from a single prompt prefill (`embed_tokens` + final hidden states `h_last`) and improve generation quality across unrelated task families, model architectures, and model scales at `< 5%` setup overhead without modifying base weights.

All original Stage 1, Stage 2, and Doppler WebGPU receipts are preserved unmodified alongside the independent symmetric canonical scorer ([score_receipts.py](score_receipts.py)) and unit tests ([test_query_swiglu_fastweight.py](test_query_swiglu_fastweight.py)).

## Sealed Artifacts and Provenance

| Artifact | Path | SHA-256 Prefix | Role |
| :--- | :--- | :--- | :--- |
| Stage 1 selection (`seed=810001`, `N=48`) | `.work/query-swiglu-fastweight-v1/stage1_selection.json` | `preserved` | Candidate screen (`C1..C5`) on 4 dev families; froze `C5_portable_et_hl_logitres` |
| Stage 2 confirmation (`seeds=920001/930001`, `N=128`) | `.work/query-swiglu-fastweight-v1/stage2_confirmation.json` | `971e40ba1cb2` | Frozen `v1` confirmation on `Qwen3-0.6B-NHS` (PyTorch MPS `bfloat16`) |
| Gemma-3-270M-IT WebGPU transfer (`N=48`) | `.work/query-swiglu-fastweight-v1/doppler_gemma3_270m_transfer.json` | `b1e6be7393ba` | Cross-architecture Doppler WebGPU Q4K transfer (`seeds=940001/940002`) |
| Qwen3.5-0.8B WebGPU transfer (`N=48`) | `.work/query-swiglu-fastweight-v1/doppler_qwen35_08b_transfer.json` | `2c19c8a9eaa1` | Cross-scale Doppler WebGPU Q4K transfer (`seeds=940001/940002`) |
| Qwen3.5-2B WebGPU transfer (`N=48`) | `.work/query-swiglu-fastweight-v1/doppler_qwen35_2b_transfer.json` | `82b42db2a046` | Cross-scale Doppler WebGPU Q4K transfer (`seeds=940001/940002`) |
| Symmetric cross-model bundle | `.work/query-swiglu-fastweight-v1/scored_summary_bundle.json` | `reproducible` | Side-by-side `raw_original` + `symmetric_canonical` scores across all receipts |
| Dosage diagnostic trace (`seed=777001`, `N=32x4`) | `.work/query-swiglu-fastweight-v1/dosage_root_cause_trace_seed777001.json` | `reproducible` | Controlled 4-variant root-cause ablation (never touching `seed=930001`) |

> **Backbone Provenance Note**: Local MPS Stage 1/2 used `/Users/xyz/deco/gamma/.work/models/Qwen3-0.6B-NHS-786708b3` loaded via standard `AutoModelForCausalLM` (`Qwen3ForCausalLM`), leaving any `ttt_proj` checkpoint tensors unused. Doppler WebGPU transfer runs used unmodified stock Q4K artifacts (`Gemma-3-270M-IT`, `Qwen3.5-0.8B`, `Qwen3.5-2B`).

## Symmetric Scorer Audit (Item 1)

In the original `v1` Stage 2 runner ([evaluate_mps.py](evaluate_mps.py)), `normalize_line(output)` stripped trailing periods `.` from model outputs while comparing against unnormalized `expected` strings. On `prose_fact_registry`, `tasks.py` defined `expected = f"{target_owner}."` (with a trailing period), causing exact predictions such as `"lead_tu89."` -> `"lead_tu89"` to score `0/16` (`raw_original`) across every arm.

[score_receipts.py](score_receipts.py) applies `canonicalize_answer` symmetrically to **both** `output` and `expected` without regenerating any model outputs, restoring `prose_fact_registry` on `Qwen3-0.6B-NHS` from `0/16` (`raw`) to `base = 5/16` vs **`focal_fastweight = 16/16` (`100%`)**.

## Stage 2 Confirmation Results (`Qwen3-0.6B-NHS`, `N = 128`, PyTorch MPS)

| Arm | Raw Pooled (`128`) | Sym Pooled (`128`) | Sym Unseen Holdout (`64`) | Setup `ms` (`% base`) | Total `ms` (`vs base`) | Sym Paired vs Focal (`+W/-L`, McNemar `p`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `base` | `59/128` (`46.1%`) | `64/128` (`50.0%`) | `26/64` (`40.6%`) | `0.0` (`0.00%`) | `1835.6` (`+0.00%`) | `+40/-17` (`p = 0.00320`) |
| `zero_fastweight` | `59/128` (`46.1%`) | `64/128` (`50.0%`) | `26/64` (`40.6%`) | `65.2` (`3.55%`) | `1818.6` (`-0.93%`) | exact `0.0` logit diff vs `base` |
| **`focal_fastweight` (`C5`)** | **`71/128` (`55.5%`)** | **`87/128` (`68.0%`)** | **`46/64` (`71.9%`)** | **`44.4` (`2.42%`)** | **`1795.5` (`-2.18%`)** | — |
| `wrong_context_fastweight` | `40/128` (`31.2%`) | `46/128` (`35.9%`) | `21/64` (`32.8%`) | `20.0` (`1.09%`) | `3038.1` (`+65.51%`) | `+50/-9` (`p = 5.26e-8`) |
| `random_fastweight` | `14/128` (`10.9%`) | `14/128` (`10.9%`) | `9/64` (`14.1%`) | `54.7` (`2.98%`) | `1803.8` (`-1.73%`) | `+76/-3` (`p = 2.72e-19`) |
| `matched_compute_split2pass` | `44/128` (`34.4%`) | `54/128` (`42.2%`) | `28/64` (`43.8%`) | `0.0` (`0.00%`) | `1911.1` (`+4.11%`) | `+38/-5` (`p = 2.50e-7`) |
| `matched_compute_full2pass` | `54/128` (`42.2%`) | `64/128` (`50.0%`) | `28/64` (`43.8%`) | `0.0` (`0.00%`) | `2819.8` (`+53.62%`) | `+36/-13` (`p = 0.00140`) |

### Per-Domain Symmetric Breakdown (`Qwen3-0.6B-NHS`, `16` tasks/domain)

| Domain | Group | `base` | `focal_fastweight` | `wrong_ctx` | `random` | `split2pass` | `full2pass` | Net (`focal - base`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `rule_induction` | Dev | `8/16` | **`11/16`** | `4/16` | `0/16` | `8/16` | `8/16` | `+3` |
| `sibling_kv` | Dev | `12/16` | **`16/16`** | `11/16` | `0/16` | `12/16` | `11/16` | `+4` |
| `compositional_records` | Dev | `10/16` | `4/16` | `7/16` | `4/16` | `2/16` | `10/16` | `-6` (regression) |
| `schema_triage` | Dev | `8/16` | **`10/16`** | `3/16` | `1/16` | `4/16` | `7/16` | `+2` |
| `access_acl_matrix` | Unseen Holdout | `8/16` | **`10/16`** | `3/16` | `3/16` | `4/16` | `6/16` | `+2` |
| `config_override_ledger` | Unseen Holdout | `6/16` | **`16/16`** | `8/16` | `2/16` | `9/16` | `8/16` | `+10` |
| `medical_dosage_tier` | Unseen Holdout | `7/16` | `4/16` | `4/16` | `4/16` | `5/16` | `4/16` | `-3` (regression) |
| `prose_fact_registry` | Unseen Holdout | `5/16` | **`16/16`** | `6/16` | `0/16` | `10/16` | `10/16` | `+11` |

## Cross-Architecture and Cross-Scale Doppler WebGPU Transfer (Item 2)

Using the identical frozen `C5_portable_et_hl_logitres` hyperparameters (`seeds=940001/940002`, `6` tasks/domain = `48` tasks/model) on Doppler WebGPU Q4K:

| Model (`Q4_K_M` WebGPU) | `base` (Sym) | `focal` (Sym) | `wrong_ctx` | `random` | `split2pass` | `full2pass` | Setup `ms` (`% base`) | Total `ms` (`vs base`) | Unseen Holdout (`base -> focal`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Gemma-3-270M-IT`** | `5/48` (`10.4%`) | **`12/48` (`25.0%`)** | `3/48` | `2/48` | `5/48` (`+43.1%` ms) | `7/48` (`+74.3%` ms) | `21.0` (**`3.00%`**) | `717.8` (**`+2.53%`**) | `2/24 -> 6/24` (`+4/-0`) |
| **`Qwen3.5-0.8B`** | `30/48` (`62.5%`) | **`33/48` (`68.8%`)** | `25/48` | `15/48` | `25/48` (`+4.25%` ms) | `29/48` (`+54.3%` ms) | `58.4` (**`1.26%`**) | `4699.9` (**`+1.31%`**) | `11/24 -> 16/24` (`+5/-0`) |
| **`Qwen3.5-2B`** | `30/48` (`62.5%`) | **`34/48` (`70.8%`)** | `25/48` | `11/48` | `31/48` (`+3.27%` ms) | `33/48` (`+52.6%` ms) | `78.7` (**`0.72%`**) | `11031.9` (**`+0.45%`**) | `9/24 -> 14/24` (`+5/-0`) |
| **Pooled WebGPU (`144`)** | `65/144` (`45.1%`) | **`79/144` (`54.9%`)** | `53/144` | `28/144` | `61/144` | `69/144` | `0.72%–3.00%` | `+0.45%–2.53%` | **`22/72 -> 36/72` (`+14/-0`)** |

### Per-Domain WebGPU Transfer Observations
- **Consistent holdout gains across all three models**: Across the `72` unseen holdout tasks on WebGPU, `focal_fastweight` improved from `22/72` (`30.6%`) to `36/72` (`50.0%`) with **zero holdout domain regressions** (`config_override_ledger`: `0->1` on `270M`, `3->6` on `0.8B`, `2->6` on `2B`; `medical_dosage_tier`: `0->2` on `270M`, `1->2` on `0.8B`, `1->1` on `2B`; `prose_fact_registry`: `2->2`, `6->6`, `5->6`).
- **Setup overhead scales sublinearly with model size**: Because `C5` touches only `(embed_tokens, h_last, lm_head)` once after prefill, setup cost dropped from `3.00%` on `270M` to `1.26%` on `0.8B` and **`0.72%`** on `2B` (`+0.45%` end-to-end latency vs `+52.59%` for `full2pass`).
- **Honest per-model limitation on `schema_triage`**: While `Gemma-3-270M-IT` passed individual McNemar significance (`+7/-0`, `p = 0.0156`), `Qwen3.5-0.8B` (`+6/-3`, `p = 0.508`) and `Qwen3.5-2B` (`+9/-5`, `p = 0.424`) had positive net gains diluted by `schema_triage` (`4/6 -> 2/6` on `0.8B`; `6/6 -> 3/6` on `2B`), where `base` was already strong and `v1`'s uncalibrated fixed `gate_scale = 12.0` overwrote low-NLL base predictions. This directly motivates `v2`'s leave-one-out NLL step gate (`eta* in {0, 3, 6, 9, 12}`).

## Causal Root-Cause Trace of `medical_dosage_tier` (Item 3)

Read-only inspection of `seed=930001` combined with a controlled `32`-task, `4`-variant ablation on fresh diagnostic `seed=777001` ([trace_dosage_diagnostic.py](trace_dosage_diagnostic.py) -> `dosage_root_cause_trace_seed777001.json`) established three exact findings:

1. **Task semantics (`in_ctx=True` observed pair vs `in_ctx=False` conjunctive extrapolation) + `Top-16` distractor leakage (primary cause)**:
   - Sampling `20` rows from `4 x 4 x 4 = 64` `(enzyme, renal, chart)` triples leaves ~`31%–50%` of queries with an `(enzyme, renal)` combination that never appeared in the context (`in_ctx=False`).
   - On `seed=930001` (`8/16` `in_ctx=True`, `8/16` `in_ctx=False`), `v1` **improved** on `in_ctx=True` (`1/8 -> 3/8`), while losing `0/-5` on `in_ctx=False` (`6/8 -> 1/8`): because `enzyme` + `renal` span only `8` causal prototypes, `v1`'s hard `Top-16` slice admitted `8` spurious `chart` symptom tokens and applied `gate_scale = 12.0` to symptom-colliding wrong rows.
   - On the larger `32`-task diagnostic `seed=777001` (`22` `in_ctx=True`, `10` `in_ctx=False`), `v1_frozen` actually beat `base` overall (`15/32` vs `8/32`; `13/22` vs `7/22` on `in_ctx=True`).
2. **Input subword stem sharing (`bandA..D` / `stage1..4`) and Qwen BPE `'='` merges (secondary cause)**:
   - Replacing shared subword stems (`['band','A']`) with distinct words (`distinct_input_words`) lifted `in_ctx=True` accuracy from `13/22 -> 17/22`.
   - Qwen BPE merges `'=re'` and `'=no'` into 7-token answers (`[' DO','SE','=re','-','1','5','mg']`) and `'=tu'` into `[' DO','SE','=t','u',...]`, shifting token offsets within the same table when those syllables are drawn (`dose-930001-14`).
   - Answer digit overlap (`15/45/10/30mg` vs `12/34/56/78mg`) had negligible effect (`15/32` vs `16/32`).
3. **Update rule verification (`v2_gated` on `seed=777001`)**:
   - Standardizing prototype columns (`Vc / v_std`), enforcing a relative SNR noise floor (`w_snr >= 0.28 * max`), calibrating `eta*` by leave-one-out context NLL, and gating query application by support coverage `clamp((max_q_sim - 0.58) / 0.27, 0, 1)` improved `original` (`bandA..D`, `DOSE=`) on `seed=777001` from `8/32` (`base`) and `15/32` (`v1_frozen`) to **`18/32` (`56.2%`)** (`15/22` on `in_ctx=True`, `3/10` vs `1/10` `base` on `in_ctx=False`).

## Reproduction

```bash
cd /Users/xyz/deco/gamma
.venv/bin/python -m unittest projects/reconfiguration/query_swiglu_fastweight_v1/test_query_swiglu_fastweight.py -v
.venv/bin/python projects/reconfiguration/query_swiglu_fastweight_v1/score_receipts.py \
  .work/query-swiglu-fastweight-v1/stage2_confirmation.json \
  .work/query-swiglu-fastweight-v1/doppler_gemma3_270m_transfer.json \
  .work/query-swiglu-fastweight-v1/doppler_qwen35_08b_transfer.json \
  .work/query-swiglu-fastweight-v1/doppler_qwen35_2b_transfer.json
```
