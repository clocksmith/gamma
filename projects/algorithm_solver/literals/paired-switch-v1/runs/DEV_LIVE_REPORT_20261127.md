# BITS Paired-Switch Development Live Run Receipt (2026-11-27)

- **Receipt JSON:** [dev_qwen25_05b_instruct_cap2_32_30s.json](dev_qwen25_05b_instruct_cap2_32_30s.json)
- **Model (offline local weights):** `Qwen/Qwen2.5-0.5B-Instruct` (`rev 7ae557604adf67be50417f59c2c2f167def9a775`, `Qwen2ForCausalLM`, `tie_word_embeddings=True`, `vocab_size=151936`, `tok_len=151665`, no literal `<H0>` in tokenizer)
- **Hardware & runtime:** `jupiter` AMD Radeon 8060S (`gfx1151`), `torch 2.12.1+rocm7.2`, `transformers 5.13.1`, `dtype=bfloat16`, `device=cuda`
- **Run contract:** `--split dev --reserved-token-id 151665 --attempt-caps 2,32 --setup-steps 16 --arm-budget-seconds 30` (18 paired problem-cap units per arm across 9 development problems in 3 families; identical 30.0 s synchronized wall clock per arm covering shared prefix prefill, adaptation setup, generation, retries, and verification)
- **Verdict:** **DO NOT freeze for sealed Rung 3 holdouts; keep Rung 4 strictly LOCKED (`LOCKED_PENDING_RUNG3_WIN`).** `ordinary_named_fn` beat `score_and_input_alias` (`2/18` vs. `1/18`), `frozen_alias` tied it (`1/18`), and every paired family-clustered 95% CI includes `0`.

## 1. Mechanical & Isolation Gate Verification

- **Reserved `<H0>` round-trip (tokenizer lacking literal `<H0>`):**
  - `encode("<H0>") == [151665]` (exact single token ID, vs. 3 subwords `[73585, 15, 29]` before fix).
  - `decode([151665]) == "<H0>"`; encoded probe function lowered and executed bound `skip_equal` with `probe_executable_passed=True`, `probe_runtime_helper_calls=1`.
- **Forced-call isolation gate (`18/18` pairs):**
  - `fixture_passed = 18/18`, `pre_call_max_abs_diff = 0.0` on all 18 pairs.
  - `input_effect_isolated = 18/18`, `post_h0_max_abs_diff` in `[324.0, 480.0]`, `post_verifier_max_abs_diff >= 0.633`, mean post-verifier KL `0.0215`, `top1_changed = 2/18`.

## 2. Verified Solves & Equal-Clock Work Accounting

| Arm | Narrow (`cap=2`) | Wide (`cap=32`) | Total Solved (`n=18`) | Helper Calls | Setup (s) | Gen (s) | Ver (s) | Total Work (s) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ordinary_named_fn` | `0/9` | **`2/9`** | **`2/18` (11.1%)** | `13` | `11.3` | `360.1` | `5.5` | `377.9` |
| `frozen_alias` | `0/9` | `1/9` | `1/18` (5.6%) | `0` | `11.5` | `356.7` | `13.3` | `382.5` |
| `score_and_input_alias` | `0/9` | `1/9` | `1/18` (5.6%) | `103` | `96.6` | `324.9` | `1.3` | `423.8` |
| `score_only_alias` | `0/9` | `0/9` | `0/18` (0.0%) | `0` | `52.2` | `440.9` | `1.0` | `495.0` |

**Solved instances (all at `cap=32`):**
- `int_01_merge_overlapping`: `frozen_alias` (3 att, 0h, 18.19 s), `score_and_input_alias` (4 att, 0h, 27.82 s), `ordinary_named_fn` (5 att, 4h, 27.39 s).
- `graph_01_shortest_path_unweighted`: `ordinary_named_fn` (3 att, 0h, 18.66 s).

### Breakdown by Family & Utility Regime (both caps, 6 units/cell)

| Slice | `frozen_alias` | `score_only_alias` | `score_and_input_alias` | `ordinary_named_fn` |
| --- | ---: | ---: | ---: | ---: |
| `duplicate_handling` | `0/6` (0h) | `0/6` (0h) | `0/6` (5h) | `0/6` (0h) |
| `interval_processing` | `1/6` (0h) | `0/6` (0h) | `1/6` (30h) | `1/6` (9h) |
| `graph_traversal` | `0/6` (0h) | `0/6` (0h) | `0/6` (68h) | `1/6` (4h) |
| `useful_once` | `1/6` (0h) | `0/6` (0h) | `1/6` (21h) | `2/6` (4h) |
| `repeatedly_useful` | `0/6` (0h) | `0/6` (0h) | `0/6` (43h) | `0/6` (4h) |
| `irrelevant_decoy` | `0/6` (0h) | `0/6` (0h) | `0/6` (39h) | `0/6` (5h) |

### Paired Contrasts (Family-Clustered 95% Bootstrap CI, 2000 resamples)

| Contrast | Diff (`a - b`) | 95% Family CI | Attribution |
| --- | ---: | ---: | --- |
| `score_only_alias` vs. `frozen_alias` | `-5.56 pp` | `[-16.67, 0.00] pp` | No selection win (`score_only` collapsed) |
| `score_and_input_alias` vs. `score_only_alias` | `+5.56 pp` | `[0.00, +16.67] pp` | CI touches 0; confounded by `score_only` collapse |
| `score_and_input_alias` vs. `ordinary_named_fn` | `-5.56 pp` | `[-16.67, 0.00] pp` | Loses to ordinary named helper |
| `score_only_alias` vs. `ordinary_named_fn` | `-11.11 pp` | `[-16.67, 0.00] pp` | Loses to ordinary named helper |

## 3. Diagnostic Findings for Next Development Iteration

1. **Why `score_only_alias` failed `36/36` verifications with `syntax_or_load_error`:** In `adapt_arm_equal_budget`, `score_only_alias` computes cross-entropy strictly on `sel_mask = (tgt == h0)` (positive `<H0>` target positions only) with `lr=0.05` for 16 steps and zero negative-position regularization. That pushes the `<H0>` output logit too high globally without adapting `E_in[151665]`, derailing syntax whenever `<H0>` fires. Adding full-sequence cross-entropy (including non-`<H0>` positions) or KL regularization on `delta_out` is needed so `score_only_alias` is a strong, non-collapsed comparator.
2. **Joint adaptation induced `<H0>` usage (`103` calls vs. `0` frozen) but did not yet translate into verified solves:** `score_and_input_alias` emitted well-formed `<H0>(...)` calls across all 3 families (`25` runnable `fail`s + `1` `pass` vs. `36/36` syntax errors on `score_only`), confirming that adapting `E_in[<H0>]` prevents syntactic derailment — yet it also over-called `<H0>` on `irrelevant_decoy` problems (`39` calls) and lost to `ordinary_named_fn` (`2/18` vs. `1/18`).
3. **0.5B base model floor effect:** `Qwen2.5-0.5B-Instruct` solved at most `2/18` (`0/9` at `cap=2`, `2/9` at `cap=32`), leaving little dynamic range. Next dev step before freezing any Rung 3 protocol: fix `score_only_alias` selection loss regularization, gate adaptation with `predict_switch_benefit` on decoys, and evaluate a stronger provisioned standard-attention code LM (e.g., 3B–7B class) where baseline solve rate sits in the `30–70%` range.
