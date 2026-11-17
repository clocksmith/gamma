# B1 Study v3: Key-Verified, Multi-Hop & Engine-Parity SwiGLU Fast-Weight (`query_swiglu_fastweight_v3`)

Charter: [CATSCAN.md](CATSCAN.md) | Runtime Package: [gamma/fastweight/CATSCAN.md](../../../gamma/fastweight/CATSCAN.md)

> **Track B1 Status: NOT MET.** Sealed `.work/` receipts remain untouched for auditability, and all reported headline claims are corrected below to match what the receipts actually support. A 50-line model-free regex lookup scores `92/96` on the MPS task set (`vs 83/96` for `focal_fastweight`) and `46/48` on the WebGPU task set (`vs 12/48, 36/48, 32/48`); the mechanism adds sparse output-token copy logit biases (`ΔW = 0`) combined with two literal string/regex rules (`str.startswith` and a `key => value` delimiter regex); and cross-engine WebGPU gains disappear once the two string-rule domains are excluded (`55/96 vs 51/96`, `+11/-7`, `p = 0.4807`).

## Scope and Audit Corrections Over `v2`

`query_swiglu_fastweight_v3` evaluates `gamma/fastweight/adapter.py`, `PyTorchEngine(fastweight=True)`, and the JavaScript port `gamma/fastweight/doppler_fastweight.mjs` on **`96` tasks generated from a new seed (`seed = 990001`) on re-skinned `v1`/`v2` lookup, bigram-rule, and 2-hop templates** (`R = 3` interleaved latency repeats per task on locally modified `Qwen3-0.6B-NHS`, not stock `Qwen3-0.6B`), followed by Python/JS tensor parity checks and `3`-model Doppler WebGPU `Q4_K_M` runs (`seed = 995001`, `N = 48` tasks per model = `144` pooled rows).

Key implementation behaviors and audit findings:

1. **Output-Logit Copy Kernel + Literal String/Regex Rules (`adapter.py`, `doppler_fastweight.mjs`)**:
   - No model weights are modified (`ΔW = 0`); the adapter adds logit biases toward context tokens that followed matching anchor positions.
   - Two branches bypass neural feature evaluation completely and run literal string rules on raw prompt text: `resolve_bpe_boundary_healed_tokens` (`ln.startswith(q_clean)` prefix lookup, accounting for all `14/16` MPS wins on `env_dotenv_secret_lookup`) and `resolve_hop_continuation_tokens` (`^(.+?)\s*(?:=>|->|=|:)\s*(\S.*)$` regex lookup during decode).
   - `adapter.py` was edited after `tasks_v3.py` was created, and `.protocol.json` files were written by the evaluation scripts at runtime rather than frozen in an ancestor commit.
2. **Latency Reality**:
   - Complete-request latency is **indistinguishable from `base` on MPS** (`2001.22 ms` vs `2042.69 ms`, within repeat variance) and **`2.57%–5.17%` slower than `base` on Doppler WebGPU** (`756.0 vs 718.8 ms` on `Gemma-3-270M-IT`, `5745.3 vs 5537.4 ms` on `Qwen3.5-0.8B`, `12436.5 vs 12125.1 ms` on `Qwen3.5-2B`).
   - Reported WebGPU `setup_ms` (`22.35–137.25 ms`, `1.13%–3.11%`) started the timer *after* `extractFullHiddenStates` (omitting GPU hidden-state extraction and CPU readback) and stopped it *before* an extra `decodeStepLogits` pass.
3. **Harness Violation of the `zero_fastweight` Identity Invariant**:
   - The runtime charter ([gamma/fastweight/CATSCAN.md](../../../gamma/fastweight/CATSCAN.md)) requires zero-scaled adapters to produce `0.0` logit change relative to unmodified decoding. That invariant was **violated by the evaluation harnesses**, not verified: on MPS, logit differences were not recorded in the receipt and `zero_fastweight` emitted a different output from `base` on `1/96` tasks (`env-990001-4`: `'VALU'` vs `'VAL_PE_79F26E'`); on Doppler WebGPU `Gemma-3-270M-IT`, `zero_fastweight` diverged from `base` on **`10/48` tasks** (`9/48` vs `10/48` correct) because `evaluate_doppler_v3.mjs` compared `zero` against `focal` on the split-prefill/snapshot-restore path rather than against `base` (`prefillWithLogits`).

## Artifacts and Hashes

- Sealed MPS Receipt (`N = 96`, `R = 3` repeats): `.work/query-swiglu-fastweight-v3/v3_unseen_confirmation.json` (`.protocol.json`)
- Real-Model Python vs Node.js Parity Receipt (`max_abs_logit_delta_diff = 5.03e-5`): `.work/query-swiglu-fastweight-v3/python_js_real_tensor_parity.json`
- Doppler WebGPU `Q4_K_M` Receipts (`seed = 995001`, `N = 48` each):
  - `Gemma-3-270M-IT` (`tied=true`, `f16` `lm_head`): `.work/query-swiglu-fastweight-v3/doppler_gemma3_270m_v3.json`
  - `Qwen3.5-0.8B` (`tied=false`, `q4k` `lm_head`): `.work/query-swiglu-fastweight-v3/doppler_qwen35_08b_v3.json`
  - `Qwen3.5-2B` (`tied=false`, `q4k` `lm_head`): `.work/query-swiglu-fastweight-v3/doppler_qwen35_2b_v3.json`
- Recorded code `sha256`:
  - `gamma/fastweight/adapter.py`: `b3d231a08c869e5f136fb5204eb14b8719c2aa3d0b081b321b0d3e9af2042b47`
  - `tasks_v3.py`: `d55567e1c8e6208dffac6b628dcbd7f3c542c0913ca787f3b1d3bc8144ecfeb4`
  - `score_receipts.py`: `6929c0db00e262b483ce6e748999e388da876c7f4924cc76ba485755f2f86a22`
  - `evaluate_v3_mps.py`: `b86be19e6e761b8575451d7ebf7cd6b45f409ddfe4b8b411b3d25e205873bbb1`

## MPS Evaluation (`Qwen3-0.6B-NHS` Local Checkpoint, New Seed `990001` on `v1`/`v2` Templates, `N = 96`)

Note: `Qwen3-0.6B-NHS-786708b3` is a locally modified checkpoint, not stock `Qwen3-0.6B`. Complete-request latency is indistinguishable from `base` on MPS. Note also that `matched_compute_split2pass` and `matched_compute_full2pass` split the context in half (dropping the target key from `half_b`) and select by uncalibrated `mean_logprob`, scoring below `base`.

| Arm | Correct / Total | Accuracy | Adapter-Only Setup `ms` (`p50` / `p95` / `% base`) | First-Token / Decode `ms` | Complete-Request `ms` (`p50` / `p95` / `vs base`) | Paired vs Focal (`+W/-L`, McNemar `p`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `base` | `40/96` | `41.67%` | `0.00` (`0.0` / `0.0` / `0.00%`) | `1346.6` / `696.1` | `2042.69` (`1652.9` / `3427.3` / `+0.00%`) | `+44/-1` (`p = 2.61e-12`, includes string rules) |
| `zero_fastweight` | `40/96` | `41.67%` | `43.31` (`25.3` / `113.9` / `2.12%`) | `1373.3` / `651.6` | `2024.92` (`1782.3` / `3457.7` / `-0.87%`) | `1/96` output mismatch vs `base` (`env-990001-4`) |
| `focal_fastweight` (`v3` hybrid) | `83/96` | `86.46%` | `43.15` (`32.0` / `103.5` / `2.11%`) | `1358.1` / `643.1` | `2001.22` (`1797.7` / `3325.9` / `-2.03%`) | — (trails 50-line regex baseline `92/96`) |
| `ablation_no_key_gate` | `64/96` | `66.67%` | `43.16` (`25.5` / `149.7` / `2.11%`) | `1342.7` / `662.3` | `2005.01` (`1761.7` / `3356.3` / `-1.84%`) | `+19/-0` (`p = 3.81e-6`, `14/19` from `startswith`) |
| `ablation_no_dynamic_hop` | `82/96` | `85.42%` | `36.99` (`24.6` / `96.3` / `1.81%`) | `1338.2` / `687.6` | `2025.80` (`1952.6` / `3416.1` / `-0.83%`) | `+1/-0` (`p = 1.0`, unsupported) |
| `ablation_no_loo_gate` | `82/96` | `85.42%` | `39.48` (`26.8` / `105.2` / `1.93%`) | `1354.1` / `645.5` | `1999.64` (`1923.9` / `3392.4` / `-2.11%`) | `+1/-0` (`p = 1.0`, unsupported) |
| `wrong_context_fastweight` | `23/96` | `23.96%` | `31.28` (`22.8` / `71.9` / `1.53%`) | `1313.2` / `643.7` | `3366.27` (`3340.9` / `5529.2` / `+64.80%`) | `+61/-1` (`p = 2.73e-17`) |
| `random_fastweight` | `15/96` | `15.62%` | `46.26` (`34.3` / `143.2` / `2.26%`) | `1319.4` / `639.9` | `1959.29` (`1600.9` / `3396.4` / `-4.08%`) | `+69/-1` (`p = 1.20e-19`) |
| `matched_compute_split2pass` | `33/96` | `34.38%` | `0.00` (`0.00%`) | `1126.0` / `915.0` | `2040.97` (`2057.4` / `3339.9` / `-0.08%`) | `+52/-2` (`p = 1.65e-13`) |
| `matched_compute_full2pass` | `38/96` | `39.58%` | `0.00` (`0.00%`) | `1925.5` / `1161.0` | `3086.53` (`2748.2` / `5153.0` / `+51.10%`) | `+46/-1` (`p = 6.82e-13`) |

### Per-Domain Breakdown and Mechanism Attribution (`N = 16` per Domain)

Excluding the two string-rule domains (`env_dotenv_secret_lookup` and `service_dependency_twohop`), the anchor-copy logit path on the remaining `4` MPS domains (`N = 64`) is `58/64` vs `29/64` (`+29/-0`, `p = 3.73e-9`; `+29/-1` if retaining the `1` `twohop` loss while excluding `twohop` wins) at `~43.2 ms` setup cost. Neither `dynamic_hop` (`+1/-0`, `p = 1.0`) nor `loo_gate` (`+1/-0`, `p = 1.0`) has statistical support for a causal ablation claim.

| Domain | `base` | `focal` (`v3`) | `no_key_gate` | `no_dynamic_hop` | `no_loo_gate` | `full2pass` | Mechanism / Audit Note |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `env_dotenv_secret_lookup` | `0/16` | `14/16` | `0/16` | `14/16` | `14/16` | `0/16` | Literal `str.startswith` string lookup (`14/14` wins; `0/16` without rule) |
| `service_dependency_twohop` | `11/16` | `11/16` | `6/16` | `10/16` | `11/16` | `11/16` | Key-recall abstention avoids `11 -> 6` overwrite; dynamic regex hop `+1/-0` (`p = 1.0`, unsupported) |
| `incident_postmortem_prose` | `6/16` | `16/16` | `16/16` | `16/16` | `16/16` | `6/16` | Anchor-window logit copy (`+10/-0`) |
| `openapi_endpoint_rate_ledger` | `10/16` | `16/16` | `16/16` | `16/16` | `16/16` | `10/16` | Anchor-window logit copy (`+6/-0`) |
| `sql_shard_policy_matrix` | `6/16` | `14/16` | `14/16` | `14/16` | `13/16` | `5/16` | Clause-bigram logit copy (`+8/-0`); LOO gate `+1/-0` (`p = 1.0`, unsupported) |
| `git_codeowners_routing` | `7/16` | `12/16` | `12/16` | `12/16` | `12/16` | `6/16` | Clause-bigram logit copy (`+5/-0`) |

## Cross-Engine Python/JS Parity and Doppler WebGPU `Q4_K_M` Results (`seed = 995001`)

1. **Python vs JavaScript Operator Parity (`verify_real_model_parity.py`)**:
   - Given identical exported tensors and precomputed `startswith` suffix tokens, Python `derive_fastweight` and Node.js `doppler_fastweight.mjs` agreed on `mode`, `anchors_count`, `step_etas`, and `u_t` (`global_max_abs_logit_delta_diff = 5.03e-5`), and `dequantizeQ4KRow` matched WebGPU `firstLogits` probes to four decimal places (`0.5731`, `4.3383`, `5.7721`).
2. **3-Model Doppler WebGPU `Q4_K_M` Results (`N = 48` Tasks/Model; New Seed on `v1`/`v2` Templates)**:
   - **No single model beats `base` significantly** (`p = 0.6250`, `p = 0.1185`, `p = 0.2891`), whereas a 50-line regex baseline scores `46/48`.
   - **Cross-engine pooled significance was carried by the two string-rule domains**: excluding `env_dotenv_secret_lookup` and `service_dependency_twohop` (`N = 96` across the 3 models), `focal` vs `base` is **`55/96` vs `51/96` (`+11/-7`, `p = 0.4807`)** and `focal` vs `full2pass` is **`55/96` vs `52/96` (`+10/-7`, `p = 0.6291`)**, with domain regressions on `git_codeowners_routing` (`5/8 -> 2/8` on `Qwen3.5-0.8B`; `5/8 -> 4/8` on `Qwen3.5-2B`).
   - On `Gemma-3-270M-IT`, `zero_fastweight` diverged from `base` on `10/48` tasks (`9/48` vs `10/48`), and the dynamic-hop regex path emitted malformed output on all `6/8` `service_dependency_twohop` tasks where it fired (`0/8 -> 0/8`).
   - Complete-request WebGPU latency is **`2.57%–5.17%` slower than `base`**, and `full2pass` latency was synthetically summed (`rb.totalMs + rb2.totalMs`) rather than executed as an independent 2-pass run.

| Model (`Q4_K_M` WebGPU) | `base` | `zero` | `focal` (`v3`) | Per-Model `focal` vs `base` (`+W/-L`, `p`) | `wrong_ctx` | `random` | `split2pass` | `full2pass` | Partial CPU Setup `ms` (omits GPU readback) | Complete-Request `ms` (`focal` vs `base`, `% slower`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Gemma-3-270M-IT` | `10/48` (`20.8%`) | `9/48` (`10/48 != base`) | `12/48` (`25.0%`) | `+3/-1` (`p = 0.6250`, NS) | `8/48` | `8/48` | `11/48` | `12/48` | `22.35 ms` (`3.11%`) | `756.0` vs `718.8` (`+5.17%` slower) |
| `Qwen3.5-0.8B` | `29/48` (`60.4%`) | `29/48` | `36/48` (`75.0%`) | `+11/-4` (`p = 0.1185`, NS) | `24/48` | `11/48` | `25/48` | `30/48` | `87.13 ms` (`1.57%`) | `5745.3` vs `5537.4` (`+3.76%` slower) |
| `Qwen3.5-2B` | `28/48` (`58.3%`) | `28/48` | `32/48` (`66.7%`) | `+6/-2` (`p = 0.2891`, NS) | `25/48` | `21/48` | `24/48` | `27/48` | `137.25 ms` (`1.13%`) | `12436.5` vs `12125.1` (`+2.57%` slower) |
| **Pooled All 6 Domains (`N = 144`)** | `67/144` (`46.5%`) | `66/144` | `80/144` (`55.6%`) | `+20/-7` (`p = 0.0192`, string-driven) | `57/144` | `40/144` | `60/144` | `69/144` | `1.13%–3.11%` (partial) | `+2.57%` to `+5.17%` slower |
| **Pooled Excl. String Domains (`N = 96`)** | `51/96` (`53.1%`) | `51/96` | `55/96` (`57.3%`) | **`+11/-7` (`p = 0.4807`, NS)** | — | — | — | `52/96` (`+10/-7`, `p = 0.6291`) | — | — |

## Requirements for `query_swiglu_fastweight_v4`

Track B1 is met only when **`focal_neural_only`** (strictly neural primary, with zero string/regex heuristics) beats **both `base` and `base_plus_string_lookup`** on genuinely new domains across **at least two stock model sizes**, with setup fully charged:

1. **Commit-ordered pre-registration**: Freeze `adapter.py`, commit its SHA-256 and `protocol.json` first, and generate confirmation tasks in a subsequent commit.
2. **Required arms**: Report `focal_neural_only` (without `resolve_bpe_boundary_healed_tokens` or `resolve_hop_continuation_tokens`), `focal_hybrid`, and `base_plus_string_lookup`.
3. **Non-copy task design & stock models**: Build new domains where a regex/string lookup baseline scores `<= 50%` (vs `92/96` in `v3`), evaluate on stock `Qwen3-0.6B` (plus a second stock scale), and include a chat-formatted prompt baseline.
4. **Powered per-model WebGPU tests**: Run `N >= 96` tasks per WebGPU model with pre-registered per-model McNemar gates; do not pool insignificant models.
5. **Harness & invariant fixes**: Assert exact `zero == base` logits on the identical execution path (restoring the [gamma/fastweight/CATSCAN.md](../../../gamma/fastweight/CATSCAN.md) invariant on `Gemma-3-270M-IT` and MPS), start the setup timer before hidden-state extraction/readback, execute `full2pass` as an independent run, and diagnose/fix the `!` (token ID `0`) generation runs.

## Reproduction

```bash
.venv/bin/python -m unittest tests/test_fastweight_parity.py projects/reconfiguration/query_swiglu_fastweight_v3/test_v3.py -v
.venv/bin/python projects/reconfiguration/query_swiglu_fastweight_v3/verify_real_model_parity.py
.venv/bin/python projects/reconfiguration/query_swiglu_fastweight_v3/evaluate_v3_mps.py \
  --output-json .work/query-swiglu-fastweight-v3/v3_unseen_confirmation.json --seed 990001 --count-per-domain 16 --latency-repeats 3
node projects/reconfiguration/query_swiglu_fastweight_v3/evaluate_doppler_v3.mjs \
  /Users/xyz/deco/doppler /Users/xyz/deco/doppler/.cache/qwen08-sha256-repair \
  .work/query-swiglu-fastweight-v3/doppler_qwen35_08b_v3.json 8 995001
```
