# B1 Study v3: Key-Verified, Multi-Hop & Engine-Parity SwiGLU Fast-Weight (`query_swiglu_fastweight_v3`)

Charter: [CATSCAN.md](CATSCAN.md) | Runtime Package: [gamma/fastweight/CATSCAN.md](../../../gamma/fastweight/CATSCAN.md)

## Overview and Causal Repairs Over `v2`

`query_swiglu_fastweight_v3` evaluates the production `gamma.fastweight` runtime (`gamma/fastweight/adapter.py` + `PyTorchEngine(fastweight=True)` and equation-for-equation JavaScript WebGPU port `gamma/fastweight/doppler_fastweight.mjs`) on `96` unseen tasks across `6` new application and reasoning domains (`seed = 990001`, `R = 3` interleaved latency repeats per task), followed by real-tensor Python/JavaScript parity verification and `3`-model Doppler WebGPU `Q4_K_M` cross-architecture/cross-scale replication (`seed = 995001`, `N = 48` tasks per model = `144` WebGPU evaluations).

`v2` (`67/96` vs `55/96` `base`) missed its registered gates (`p = 0.0807`, `setup = 5.055%`) for two specific reasons: unverified `window` lookup routing overwrote `2`-hop composition (`chained_alias_resolution` `12/16 -> 3/16`), and per-offset MPS `.item()` calls caused `40+` Metal command-buffer sync stalls per prompt (`73.71 ms`). `v3` resolves both mechanisms and fixes `v1`'s untied `Q4_K_M` `lm_head` WebGPU discrepancy:

1. **Shift-Invariant Rare-Token Key Verification (`window` vs `multihop_bridge`) + BPE Boundary Healing**:
   - Computes rare-token key recall between the query prefix and candidate context anchor lines (`> 0.85` -> verified `window` lookup; `<= 0.85` -> `multihop_bridge`, preventing unverified overwrite of `base` reasoning on multi-hop chains) and heals no-space `.env` `KEY=val` BPE delimiter merges (`=val` single token vs `=` query suffix).
2. **Decode-Time Dynamic Second-Hop Resolution**:
   - In `multihop_bridge` mode (`PyTorchEngine` and `doppler_fastweight.mjs`), once hop-1 emits an intermediate identifier (`a -> r`), the adapter resolves hop-2 (`r -> p`) from context and injects bounded candidate logit deltas on the continuation suffix (`r/p`).
3. **Single-Transfer Batched CPU Leave-One-Out `eta*` Calibration**:
   - Computes `hl_f32 @ W_all_u.T` in one batched GPU matmul and transfers the small `(m * K, U_tot)` matrix to CPU once, cutting mean setup latency from `73.71 ms` (`5.055%`) to **`43.15 ms` (`2.11%`)**.
4. **Engine-Faithful Doppler WebGPU `Q4_K_M` `lm_head` Dequantization & Full `[0 .. T-1]` State Extraction**:
   - Dequantizes untied `Q4_K_M` `lm_head.weight` rows (`dequantizeQ4KRow` matching `fused_matmul_q4.wgsl`) on `Qwen3.5-0.8B` and `Qwen3.5-2B` (verified exact `0.0000` difference vs WebGPU `firstLogits` on runtime parity probes) and extracts full `h_last[0 .. T-1]` with deterministic KV and linear-attention snapshot restoration.

## Artifacts and Hashes

- Frozen MPS Confirmation (`N = 96`, `R = 3` repeats, **all pre-registered gates passed**): `.work/query-swiglu-fastweight-v3/v3_unseen_confirmation.json` (`.protocol.json`)
- Real-Model Python vs Node.js Parity Receipt (`max_abs_logit_delta_diff = 5.03e-5`): `.work/query-swiglu-fastweight-v3/python_js_real_tensor_parity.json`
- Doppler WebGPU `Q4_K_M` Cross-Model Receipts (`seed = 995001`, `N = 48` each):
  - `Gemma-3-270M-IT` (`tied=true`, `f16` `lm_head`): `.work/query-swiglu-fastweight-v3/doppler_gemma3_270m_v3.json`
  - `Qwen3.5-0.8B` (`tied=false`, `q4k` `lm_head`): `.work/query-swiglu-fastweight-v3/doppler_qwen35_08b_v3.json`
  - `Qwen3.5-2B` (`tied=false`, `q4k` `lm_head`): `.work/query-swiglu-fastweight-v3/doppler_qwen35_2b_v3.json`
- Confirmation code `sha256`:
  - `gamma/fastweight/adapter.py`: `b3d231a08c869e5f136fb5204eb14b8719c2aa3d0b081b321b0d3e9af2042b47`
  - `tasks_v3.py`: `d55567e1c8e6208dffac6b628dcbd7f3c542c0913ca787f3b1d3bc8144ecfeb4`
  - `score_receipts.py`: `6929c0db00e262b483ce6e748999e388da876c7f4924cc76ba485755f2f86a22`
  - `evaluate_v3_mps.py`: `b86be19e6e761b8575451d7ebf7cd6b45f409ddfe4b8b411b3d25e205873bbb1`

## Stage-2 Unseen Confirmation (`Qwen3-0.6B-NHS` MPS, `seed = 990001`, `N = 96`, `R = 3` Repeats)

Note: `Qwen3-0.6B-NHS-786708b3` is loaded via standard `Qwen3ForCausalLM` (`ttt_proj` weights unused; CPT backbone provenance explicitly disclosed). `PyTorchEngine(fastweight=True)` integration smoke check scored **`6/6` (`100%`)** across all `6` domains (`window`, `clause_bigram`, `multihop_bridge`).

Setup overhead (`< 5.0%` registered gate) and complete-request latency (unthresholded in protocol; reported explicitly with `mean`, `p50`, `p95`, `first_token`, and `decode`):

| Arm | Correct / Total | Accuracy | Setup `ms` (`p50` / `p95` / `% base`) | First-Token / Decode `ms` | Complete-Request `ms` (`p50` / `p95` / `vs base`) | Paired vs Focal (`+W/-L`, McNemar `p`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `base` | `40/96` | `41.67%` | `0.00` (`0.0` / `0.0` / `0.00%`) | `1346.6` / `696.1` | `2042.69` (`1652.9` / `3427.3` / `+0.00%`) | `+44/-1` (**`p = 2.61e-12`**) |
| `zero_fastweight` | `40/96` | `41.67%` | `43.31` (`25.3` / `113.9` / `2.12%`) | `1373.3` / `651.6` | `2024.92` (`1782.3` / `3457.7` / `-0.87%`) | Exact `0.0` logit diff vs `base` |
| **`focal_fastweight` (`v3`)** | **`83/96`** | **`86.46%`** | **`43.15` (`32.0` / `103.5` / `2.11%`)** | **`1358.1` / `643.1`** | **`2001.22` (`1797.7` / `3325.9` / `-2.03%`)** | — (`ALL GATES MET`) |
| `ablation_no_key_gate` | `64/96` | `66.67%` | `43.16` (`25.5` / `149.7` / `2.11%`) | `1342.7` / `662.3` | `2005.01` (`1761.7` / `3356.3` / `-1.84%`) | `+19/-0` (**`p = 3.81e-6`**) |
| `ablation_no_dynamic_hop` | `82/96` | `85.42%` | `36.99` (`24.6` / `96.3` / `1.81%`) | `1338.2` / `687.6` | `2025.80` (`1952.6` / `3416.1` / `-0.83%`) | `+1/-0` (`p = 1.0`) |
| `ablation_no_loo_gate` | `82/96` | `85.42%` | `39.48` (`26.8` / `105.2` / `1.93%`) | `1354.1` / `645.5` | `1999.64` (`1923.9` / `3392.4` / `-2.11%`) | `+1/-0` (`p = 1.0`) |
| `wrong_context_fastweight` | `23/96` | `23.96%` | `31.28` (`22.8` / `71.9` / `1.53%`) | `1313.2` / `643.7` | `3366.27` (`3340.9` / `5529.2` / `+64.80%`) | `+61/-1` (**`p = 2.73e-17`**) |
| `random_fastweight` | `15/96` | `15.62%` | `46.26` (`34.3` / `143.2` / `2.26%`) | `1319.4` / `639.9` | `1959.29` (`1600.9` / `3396.4` / `-4.08%`) | `+69/-1` (**`p = 1.20e-19`**) |
| `matched_compute_split2pass` | `33/96` | `34.38%` | `0.00` (`0.00%`) | `1126.0` / `915.0` | `2040.97` (`2057.4` / `3339.9` / `-0.08%`) | `+52/-2` (**`p = 1.65e-13`**) |
| `matched_compute_full2pass` | `38/96` | `39.58%` | `0.00` (`0.00%`) | `1925.5` / `1161.0` | `3086.53` (`2748.2` / `5153.0` / `+51.10%`) | `+46/-1` (**`p = 6.82e-13`**) |

### Per-Domain Breakdown and Causal Ablation Attribution (`N = 16` per Domain)

| Domain | `base` | **`focal` (`v3`)** | `no_key_gate` | `no_dynamic_hop` | `no_loo_gate` | `full2pass` | Causal Role Verified |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `env_dotenv_secret_lookup` | `0/16` | **`14/16`** | `0/16` | `14/16` | `14/16` | `0/16` | Rare-key + BPE boundary healing (`0 -> 14`) |
| `service_dependency_twohop` | `11/16` | **`11/16`** | `6/16` | `10/16` | `11/16` | `11/16` | Key gate eliminates 2-hop regression (`6 -> 11`); hop adds `+1` |
| `incident_postmortem_prose` | `6/16` | **`16/16`** | `16/16` | `16/16` | `16/16` | `6/16` | Window fast-weight (`+10` to ceiling) |
| `openapi_endpoint_rate_ledger` | `10/16` | **`16/16`** | `16/16` | `16/16` | `16/16` | `10/16` | Window fast-weight (`+6` to ceiling) |
| `sql_shard_policy_matrix` | `6/16` | **`14/16`** | `14/16` | `14/16` | `13/16` | `5/16` | Standardized `2*d` bigram + LOO NLL gate (`+8`) |
| `git_codeowners_routing` | `7/16` | **`12/16`** | `12/16` | `12/16` | `12/16` | `6/16` | Standardized `2*d` bigram (`+5`) |

## Cross-Engine Python/JS Parity and Doppler WebGPU `Q4_K_M` Replication (`seed = 995001`)

1. **Real-Model Python vs JavaScript Parity (`verify_real_model_parity.py`)**:
   - Across all `6` domains (`window`, `clause_bigram`, `multihop_bridge`) on real `Qwen3-0.6B` hidden states, `embed_tokens`, and `lm_head` tensors, Python `gamma.fastweight.derive_fastweight` and Node.js `doppler_fastweight.mjs` matched identically on `mode`, `anchors_count`, `step_etas`, and candidate `u_t`, with **`global_max_abs_logit_delta_diff = 5.03e-5`**.
2. **Runtime `lm_head` Kernel Parity on Doppler WebGPU**:
   - `Gemma-3-270M-IT` (`tied=true`, `f16`): JS dot product `0.5731` vs WebGPU `firstLogits` `0.5731`.
   - `Qwen3.5-0.8B` (`tied=false`, `q4k`): JS `dequantizeQ4KRow` dot product `4.3383` vs WebGPU `firstLogits` `4.3383`.
   - `Qwen3.5-2B` (`tied=false`, `q4k`): JS `dequantizeQ4KRow` dot product `5.7721` vs WebGPU `firstLogits` `5.7721`.

### 3-Model Doppler WebGPU `Q4_K_M` Results (`N = 48` Unseen Tasks/Model = `144` Pooled)

Cold per-request setup caches (`embedNormCache`, `lmHeadRowCache`) are cleared before every single arm evaluation so `setup_ms` and `total_ms` include full GPU weight-row gather and `Q4_K_M`/`F16` decoding costs:

| Model (`Q4_K_M` WebGPU) | `base` | `zero` | **`focal` (`v3`)** | `wrong_ctx` | `random` | `split2pass` | `full2pass` | Cold Setup `ms` (`% base`) | Complete-Request `ms` (`focal` vs `base` / `full2pass`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Gemma-3-270M-IT` | `10/48` (`20.8%`) | `9/48` | **`12/48` (`25.0%`)** | `8/48` | `8/48` | `11/48` | `12/48` | `22.35 ms` (**`3.11%`**) | `756.0` vs `718.8` (`+5.17%`) / `1252.1` (`+74.19%`) |
| `Qwen3.5-0.8B` | `29/48` (`60.4%`) | `29/48` | **`36/48` (`75.0%`)** | `24/48` | `11/48` | `25/48` | `30/48` | `87.13 ms` (**`1.57%`**) | `5745.3` vs `5537.4` (`+3.76%`) / `8274.2` (`+49.42%`) |
| `Qwen3.5-2B` | `28/48` (`58.3%`) | `28/48` | **`32/48` (`66.7%`)** | `25/48` | `21/48` | `24/48` | `27/48` | `137.25 ms` (**`1.13%`**) | `12436.5` vs `12125.1` (`+2.57%`) / `18682.0` (`+54.08%`) |
| **Pooled (`N = 144`)** | **`67/144` (`46.5%`)** | `66/144` | **`80/144` (`55.6%`)** | `57/144` | `40/144` | `60/144` | `69/144` | **`1.13%–3.11%`** (`< 5%`) | **`+2.57%` to `+5.17%`** vs **`+49.4%` to `+74.2%`** |

Pooled 3-model Doppler WebGPU paired exact two-sided McNemar tests (`N = 144`):
- `focal` (`80/144`) vs `base` (`67/144`): **`+20` wins / `-7` losses** (`+13` net, **`p = 0.0192`**).
- `focal` (`80/144`) vs `matched_compute_split2pass` (`60/144`): **`+31` wins / `-11` losses** (`+20` net, **`p = 0.00289`**).
- `focal` (`80/144`) vs `matched_compute_full2pass` (`69/144`): **`+19` wins / `-8` losses** (`+11` net, `p = 0.0522`, while cutting complete-request latency by `30%–40%`).
- `focal` (`80/144`) vs `wrong_context_fastweight` (`57/144`): **`+27` wins / `-4` losses** (`+23` net, **`p = 3.40e-5`**).
- `focal` (`80/144`) vs `random_fastweight` (`40/144`): **`+47` wins / `-7` losses** (`+40` net, **`p = 2.29e-8`**).
- Notably, on `service_dependency_twohop` (`2`-hop composition), `focal_fastweight` achieved **`0/8 -> 0/8`** (`270M`), **`6/8 -> 8/8`** (`0.8B`, `8` dynamic hops triggered), and **`8/8 -> 8/8`** (`2B`, `6` dynamic hops triggered) — **zero 2-hop regressions on any model**.

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
