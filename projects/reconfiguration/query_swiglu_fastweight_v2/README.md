# B1 Study v2: Standardized & LOO-Calibrated SwiGLU Fast-Weight (`query_swiglu_fastweight_v2`)

Charter: [CATSCAN.md](CATSCAN.md)

## Summary

`query_swiglu_fastweight_v2` tested the frozen `C5_v2_unitvar_loonll` candidate (`Vc / v_std` standardization + relative SNR noise floor + leave-one-out context NLL `eta*` selection + support coverage gating) on `96` unseen tasks across `6` new domains (`seed=970001`, `R = 3` interleaved latency repeats per task).

The sealed confirmation receipt is preserved at `.work/query-swiglu-fastweight-v2/v2_unseen_confirmation.json`.

## Confirmation Results (`seed=970001`, `N = 96`, `R = 3` Repeats)

| Arm | Correct / Total | Accuracy | Setup `ms` (`% base`) | Total `ms` (`vs base`) | Paired vs Focal (`+W/-L`, McNemar `p`) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `base` | `55/96` | `57.3%` | `0.0` (`0.00%`) | `1458.1` (`+0.00%`) | `+26/-14` (`p = 0.0807`) |
| `zero_fastweight` | `55/96` | `57.3%` | `63.7` (`4.37%`) | `1497.1` (`+2.67%`) | `0.0` logit diff vs `base` |
| **`focal_fastweight` (`v2`)** | **`67/96`** | **`69.8%`** | **`73.7` (`5.06%`)** | **`1539.2` (`+5.56%`)** | — |
| `wrong_context_fastweight` | `49/96` | `51.0%` | `16.4` (`1.12%`) | `2497.8` (`+71.3%`) | `+31/-13` (`p = 0.00956`) |
| `random_fastweight` | `22/96` | `22.9%` | `80.8` (`5.54%`) | `1536.5` (`+5.38%`) | `+49/-4` (`p = 7.05e-11`) |
| `matched_compute_split2pass` | `50/96` | `52.1%` | `0.0` (`0.00%`) | `1574.0` (`+7.95%`) | `+25/-8` (`p = 0.00455`) |
| `matched_compute_full2pass` | `55/96` | `57.3%` | `0.0` (`0.00%`) | `2289.8` (`+57.0%`) | `+25/-13` (`p = 0.0730`) |

### Per-Domain Breakdown and Causal Diagnosis Driving `v3`

| Domain | `base` | `focal_fastweight` (`v2`) | Paired `+W/-L` | Mean Setup (`ms`) | Outcome |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `artifact_checksum_registry` | `12/16` | **`16/16`** | `+4/-0` | `41.5` | Clean 1-hop win |
| `biography_affiliation_memo` | `6/16` | **`16/16`** | `+10/-0` | `45.5` | Clean prose 1-hop win |
| `warehouse_tariff_schedule` | `5/16` | **`10/16`** | `+6/-1` | `103.3` | Dosage-twin subword rule doubled (`+5`) |
| `firewall_rule_synthesis` | `8/16` | **`11/16`** | `+5/-2` | `108.3` | Subword rule synthesis win (`+3`) |
| `feature_flag_rollout` | `12/16` | `11/16` | `+1/-2` | `82.7` | Near-ceiling neutral (`-1`) |
| `chained_alias_resolution` | `12/16` | `3/16` | `+0/-9` | `60.9` | **Root cause of missed `p < 0.05` gate** |

Two concrete mechanisms explained the missed pre-registered gates (`p = 0.0807` vs `< 0.05`, and `setup = 5.06%` vs `< 5.0%`) and drove the substantial `v3` (`gamma.fastweight`) redesign:
1. **Unverified lookup routing on multi-hop composition (`chained_alias_resolution`: `12/16 -> 3/16`, `9/14` of all losses)**: Because every `ALIAS`/`ENDPOINT`/`CONNECT` row had a distinct value (`u_ratio > 0.65`), `v2` routed `chained_alias_resolution` to `window` mode with `best_eta = 12.0` (bypassing the LOO NLL gate) even though **no context line matched `CONNECT alias_k =>`**, copying `CONNECT alias_0`'s answer onto `alias_k`. `v3` (`gamma/fastweight/`) introduces shift-invariant rare-token key verification (`window` vs `multihop_bridge`) plus dynamic decode-time second-hop resolution (`a -> r`, `r -> p` => `r/p`).
2. **Per-offset MPS `.item()` synchronization stalls (`103–108 ms` on `clause_bigram`)**: Evaluating `F.cross_entropy(...).item()` `5` times per offset on MPS forced ~`40` Metal command-buffer sync barriers per prompt. `v3` batches all offsets into a single GPU matmul + single CPU transfer, eliminating per-offset GPU syncs.
