# BITS Paired-Switch Controlled Development Rerun Receipt (2026-11-28)

- **Receipt JSON:** [dev_qwen25_05b_instruct_cap2_32_30s_matched_obj.json](dev_qwen25_05b_instruct_cap2_32_30s_matched_obj.json)
- **Prior confounded receipt (for comparison):** [DEV_LIVE_REPORT_20261127.md](DEV_LIVE_REPORT_20261127.md)
- **Code revision:** `clocksmith/gamma@7b1d76f7d`
- **Model (unchanged):** `Qwen/Qwen2.5-0.5B-Instruct` (`rev 7ae557604adf67be50417f59c2c2f167def9a775`, local offline weights, `Qwen2ForCausalLM`, `tie_word_embeddings=True`, `--reserved-token-id 151665`, `bfloat16`, `jupiter` AMD Radeon 8060S `rocm7.2`)
- **Controlled design:** Identical training examples, identical loss positions (`sel_mask` + `post_mask`), identical `setup_steps=16` (`lr=0.05`), and identical `30.0 s` synchronized wall clock per arm across all 9 development problems at `cap=2` and `cap=32` (`18` paired units/arm). The **only** experimental difference between `score_only_alias` and `score_and_input_alias` is whether the `<H0>` input embedding row (`delta_in`) is trainable.
- **Verdict:** **DO NOT advance to sealed families; keep Rung 4 strictly LOCKED (`LOCKED_PENDING_RUNG3_WIN`).** Matching the training objective completely resolved the prior `score_only_alias` 36/36 syntax collapse, and under the controlled comparison `score_and_input_alias` (`0/18`) lost to `score_only_alias` (`1/18`), `frozen_alias` (`1/18`), and `ordinary_named_fn` (`1/18`), with **zero executed helper calls on any passing candidate across all four arms**.

## 1. Matched-Objective & Isolation Gate Audits

- **Helper round-trip:** `encode("<H0>") == [151665]`, `decode([151665]) == "<H0>"`, `probe_executable_passed = True`, `probe_runtime_helper_calls = 1`.
- **Matched training objective (`score_only_alias` vs. `score_and_input_alias`):**
  - `loss_positions_exact = 18/18` (`sel_mask` and `post_mask` counts identical on every switch point)
  - `setup_tokens_exact = 18/18`
  - Step-0 `setup_initial_loss` max abs diff = **`0.00e+00`** (mean `8.061` for both arms)
  - Mean final setup loss: `1.076` (`score_only_alias`) vs. `1.014` (`score_and_input_alias`)
- **Forced-call isolation gate:** **`18/18` passed** (`pre_call_max_abs_diff = 0.0` on all 18; `input_effect_isolated = 18/18`; `post_h0_max_abs_diff` in `[324.0, 480.0]`; `post_verifier_max_abs_diff >= 0.633`; mean KL `0.0215`; `top1_changed = 2/18`).

## 2. Verified Solves & Separated Helper-Call Accounting

| Arm | `cap=2` | `cap=32` | Total Solved (`n=18`) | Solved w/ Executed Helper | Passing Executed Calls | All-Attempt Syntactic Mentions | All-Attempt Runtime Calls | Setup (s) | Total Work (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `score_only_alias` | `1/9` | `0/9` | **`1/18` (5.6%)** | `0` | `0` | `495` | `238` | `54.2` | `419.1` |
| `frozen_alias` | `0/9` | `1/9` | **`1/18` (5.6%)** | `0` | `0` | `0` | `0` | `11.7` | `389.5` |
| `ordinary_named_fn` | `0/9` | `1/9` | **`1/18` (5.6%)** | `0` | `0` | `16` | `8` | `11.6` | `376.9` |
| `score_and_input_alias` | `0/9` | `0/9` | **`0/18` (0.0%)** | `0` | `0` | `113` | `0` | `99.8` | `431.7` |

**All verified solves (`0` executed helper calls in every passing program):**
- `int_01_merge_overlapping cap=2`, `score_only_alias` (2 att, `pass_syn=0`, `pass_run=0`, `14.09 s`)
- `int_01_merge_overlapping cap=32`, `frozen_alias` (3 att, `pass_syn=0`, `pass_run=0`, `19.17 s`)
- `int_01_merge_overlapping cap=32`, `ordinary_named_fn` (2 att, `pass_syn=0`, `pass_run=0`, `11.46 s`)

### Verifier Status Breakdown (Across All Verified Attempts)

| Arm | `pass` | `fail` | `syntax_or_load_error` | `missing_entrypoint` | `timeout` | Total Verifier Calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `frozen_alias` | `1` | `34` | `6` | `2` | `6` | `49` |
| `score_only_alias` | `1` | `34` | **`9`** *(was 36/36)* | `4` | `0` | `48` |
| `score_and_input_alias` | `0` | `24` | `13` | `9` | `0` | `46` |
| `ordinary_named_fn` | `1` | `41` | `6` | `0` | `0` | `48` |

### Breakdown by Family & Utility Regime (6 units/cell)

| Slice | `frozen_alias` | `score_only_alias` | `score_and_input_alias` | `ordinary_named_fn` |
| --- | ---: | ---: | ---: | ---: |
| `duplicate_handling` | `0/6` (0 syn, 0 run) | `0/6` (47 syn, 238 run) | `0/6` (7 syn, 0 run) | `0/6` (0 syn, 0 run) |
| `interval_processing` | `1/6` (0 syn, 0 run) | `1/6` (410 syn, 0 run) | `0/6` (43 syn, 0 run) | `1/6` (15 syn, 8 run) |
| `graph_traversal` | `0/6` (0 syn, 0 run) | `0/6` (38 syn, 0 run) | `0/6` (63 syn, 0 run) | `0/6` (1 syn, 0 run) |
| `useful_once` | `1/6` (0 syn, 0 run) | `1/6` (12 syn, 27 run) | `0/6` (16 syn, 0 run) | `1/6` (0 syn, 8 run) |
| `repeatedly_useful` | `0/6` (0 syn, 0 run) | `0/6` (56 syn, 191 run) | `0/6` (45 syn, 0 run) | `0/6` (4 syn, 0 run) |
| `irrelevant_decoy` | `0/6` (0 syn, 0 run) | `0/6` (427 syn, 20 run) | `0/6` (52 syn, 0 run) | `0/6` (12 syn, 0 run) |

### Paired Contrasts (Family-Clustered 95% Bootstrap CI, 2000 resamples)

| Contrast | Diff (`a - b`) | 95% Family CI | Outcome |
| --- | ---: | ---: | --- |
| `score_only_alias` vs. `frozen_alias` | `0.00 pp` | `[0.00, 0.00] pp` | Tie |
| `score_and_input_alias` vs. `score_only_alias` | `-5.56 pp` | `[-16.67, 0.00] pp` | Joint arm loses |
| `score_and_input_alias` vs. `ordinary_named_fn` | `-5.56 pp` | `[-16.67, 0.00] pp` | Joint arm loses |
| `score_only_alias` vs. `ordinary_named_fn` | `0.00 pp` | `[0.00, 0.00] pp` | Tie |

## 3. Conclusion

1. **Prior syntax-collapse confound resolved:** Matching the loss positions (`sel_mask` + `post_mask`) eliminated the `36/36` syntax collapse in `score_only_alias` (syntax errors fell from `36/36` to `9/48`, fewer than `score_and_input_alias`'s `13/46`, with `238` runtime helper executions on failed attempts and `1` verified solve). The earlier collapse came from omitting `post_mask` negative gradients on `W_out[<H0>]`, not from freezing `E_in[<H0>]`.
2. **No development gain from adapting `E_in[<H0>]`:** With the objective matched and trainable `delta_in` as the sole difference, `score_and_input_alias` solved `0/18`, recorded `0` runtime helper executions across all 46 verifications (all 113 mentions occurred in non-executing/syntax-error/missing-entrypoint code), spent `99.8 s` on setup vs. `54.2 s` (`score_only`) and `11.6 s` (`ordinary_named_fn`), and trailed both comparators.
3. **Gate status:** Remain on development data; do not touch sealed families; keep Rung 4 locked.
