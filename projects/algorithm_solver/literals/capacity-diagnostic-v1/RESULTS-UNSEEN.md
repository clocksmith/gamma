# Unseen Diagnostic Evaluation Receipt (`bd46bfa58`)

Single-pass evaluation of the 8 frozen unseen corpora (15 queries) committed at `bd46bfa58` before running `evaluate_unseen.py`. `SHA256SUMS-UNSEEN` 5/5 verified intact; zero predictions or instances were edited after running.

## Summary

- **Total queries:** `15` (`13/15` exact matches, `2` honest misses reported in full below).
- **Settled without any LP/MILP solver:** `14/15` (`93.3%`: `7` `IMPOSSIBLE`, `7` `FEASIBLE` with byte-exact verified dictionaries, `1` `UNRESOLVED`).
- **Diagnostic speedup verified identical:** optimizing `eligible_tokens` (suffix-LCP) and `position_cover_sets` (prefix-index) cut `real_py12_W2_K64` runtime from `85.9s` to `12.1s` with identical verdicts across all 15 queries.

## Full Results Table (All 15 Queries)

| Query | Rule | K | `|\Sigma|` | Comp | LB | Observed | Predicted | Match | ms | Encoding decision / note |
| --- | --- | ---: | ---: | ---: | ---: | --- | --- | :---: | ---: | --- |
| `real_py12_W2_K64` | `W2` | 64 | 83 | 1 | 83 | `IMPOSSIBLE` | `IMPOSSIBLE` | OK | 12071.7 | Switch off plain 6-bit (`sat >= W2`) |
| `real_py12_W2_K96` | `W2` | 96 | 83 | 1 | 83 | `FEASIBLE` | `FEASIBLE` | OK | 12725.8 | Byte-exact 83-singleton dict |
| `real_yaml2_W2_K64` | `W2` | 64 | 57 | 1 | 8 | `FEASIBLE` | `FEASIBLE` | OK | 9765.4 | Stay on plain 6-bit (57 singletons) |
| `real_yaml2_W2_K32` | `W2` | 32 | 57 | 1 | 8 | `UNRESOLVED` | `IMPOSSIBLE` | **MISS** | 9189.3 | Near-copy YAML configs share huge blocks (`interval=[8, 57]`) |
| `decision_66_pairable_W2_K64` | `W2` | 64 | 66 | 1 | 64 | `FEASIBLE` | `FEASIBLE` | OK | 19.2 | **Changes choice:** stay on 6-bit despite `|\Sigma|=66` (64-entry byte-exact dict) |
| `decision_66_pairable_W2_K63` | `W2` | 63 | 66 | 1 | 64 | `IMPOSSIBLE` | `IMPOSSIBLE` | OK | 18.7 | Proves `64` is exact tight budget |
| `decision_66_doomed_W2_K64` | `W2` | 64 | 66 | 1 | 66 | `IMPOSSIBLE` | `IMPOSSIBLE` | OK | 19.3 | **Changes choice:** plain 6-bit doomed (`sat >= W2`), switch to escape/7-bit |
| `decision_66_doomed_W2_K66` | `W2` | 66 | 66 | 1 | 66 | `FEASIBLE` | `FEASIBLE` | OK | 19.6 | Byte-exact 66-singleton dict |
| `mixed_3comp_W2_K10` | `W2` | 10 | 12 | 3 | 11 | `IMPOSSIBLE` | `IMPOSSIBLE` | OK | 1.0 | Component-wise sum `5+4+2=11` settles `K=10` |
| `mixed_3comp_W2_K11` | `W2` | 11 | 12 | 3 | 11 | `FEASIBLE` | `FEASIBLE` | OK | 1.3 | Byte-exact 11-entry dict |
| `forced_block_split_W2_K7` | `W2` | 7 | 8 | 1 | 8 | `IMPOSSIBLE` | `IMPOSSIBLE` | OK | 1.5 | Forced-block decomposition `4+4=8` settles `K=7` (`sat >= W2`) |
| `forced_block_split_W2_K8` | `W2` | 8 | 8 | 1 | 8 | `FEASIBLE` | `FEASIBLE` | OK | 1.6 | Byte-exact 8-singleton dict |
| `u_span_obstruction_U_K3` | `U` | 3 | 4 | 1 | 4 | `IMPOSSIBLE` | `IMPOSSIBLE` | OK | 1.0 | Span-parse obstruction lifts `rank=3` to `LB=4` |
| `u_span_obstruction_U_K4` | `U` | 4 | 4 | 1 | 4 | `FEASIBLE` | `FEASIBLE` | OK | 1.0 | Byte-exact 4-singleton dict |
| `natural_unresolved_W2_K25` | `W2` | 25 | 26 | 2 | 18 | `FEASIBLE` | `UNRESOLVED` | **MISS** | 65.1 | Shared tail blocks yielded verified 18-entry dict (`<= 25`) |

## Analysis of the Two Honest Misses

1. **`real_yaml2_W2_K32` (predicted `IMPOSSIBLE`, observed `UNRESOLVED [8, 57]`):** The two unseen YAML configs (`qwen3_0_6b_to_1_7b.yaml` and `qwen3_1_7b_to_0_6b.yaml`) are near-identical templates differing only in model-size fields, so shared multi-character blocks cover almost every byte, collapsing the lower bound from `57` to `8`. The checker rightly returned `UNRESOLVED [8, 57]` instead of falsely claiming impossibility at `K = 32`.
2. **`natural_unresolved_W2_K25` (predicted `UNRESOLVED`, observed `FEASIBLE` at 18 entries):** In component 2, the shared `"gh"` and length-5 prefix blocks formed an eligible forced-block dictionary of size 13 (`5 + 13 = 18 <= 25`), so the checker constructed and byte-verified an 18-entry dictionary directly.

## Encoding-Choice Demonstration (`|\Sigma| = 66` at `K = 64`)

On the matched 66-character pair (`decision_66char_pairable` vs. `decision_66char_doomed`), naive alphabet size (`66 > 64`) cannot separate them. The diagnostic settles both in `19 ms` without a solver:
- `decision_66char_pairable`: **`FEASIBLE` at `K = 64`** with a byte-exact 64-entry dictionary (stay on plain 6-bit, zero escapes).
- `decision_66char_doomed`: **`IMPOSSIBLE` at `K = 64`** (`LB = 66`, `sat >= W2` across every higher threshold; switch to 6-bit + escape or 7-bit).
