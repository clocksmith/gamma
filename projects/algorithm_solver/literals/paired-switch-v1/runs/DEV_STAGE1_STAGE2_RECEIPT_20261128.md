# BITS `paired-switch-v1` Development Receipt (2026-11-28)

**Model:** `/home/x/models/hf/Qwen/Qwen3-4B-Instruct-2507-cdbee75f` (`bfloat16`, ROCm 7.2, `Radeon 8060S Graphics` on `jupiter`, reserved slot `--reserved-token-id 151670`)  
**GPU Reservation:** `agent-bus` leases `jupiter-gpu` + `jupiter` (`s_mwyyzsok8f0089028b83`) + whole-run `ExclusiveGpuLease` (`fcntl.flock` + `0.5s` continuous `rocm-smi --showpids` watchdog, **0 mid-run intrusions** across all runs)  
**Holdout Status:** `SEALED` (untouched)  
**Rung 4 Status:** `LOCKED_PENDING_RUNG3_WIN`  

## Executive Outcome

- **Stage 1 (Original 3-line textbook fixture):** `HELPER_NOT_QUALIFIED` (`ordinary_named_fn` `11/18` = `61.1%` vs. `no_helper` `14/18` = `77.8%`, `-16.7 pp`). `Qwen3-4B` already solved the memorized LeetCode problems without any helper.
- **Stage 1 (Upgraded 6-family domain-helper fixture):** **`HELPER_QUALIFIED_FOR_STAGE2`** (`ordinary_named_fn` **`16/24` = `66.7%`** vs. `no_helper` **`4/24` = `16.7%`**, **`+50.0 pp`**, 95% family CI **`[+25.0 pp, +75.0 pp]`**, `12` verified solves executing the helper across **all 3 train families**, `0` spurious helper calls on passing decoys).
- **Stage 2 (Paired installation on disjoint validation families `DEV_VAL_PROBLEMS`):** **`RUNG2_NOT_EARNED`**. Under identical helper, transcript, adaptation examples/loss positions, and `45s` total wall-clock budget:
  - `score_only_alias` (`W_out[<H0>]` only, `~5.3s` setup): **`22/24` (`91.7%`)**, `16/18` useful units solved with **`216` passing runtime `<H0>` calls**, `6/6` decoy solves with `0` `<H0>` calls.
  - `score_and_input_alias` (`W_out[<H0>]` + `E_in[<H0>]`, `~11.6s` setup): **`16/24` (`66.7%`)**, `10/18` useful units solved with `120` passing runtime `<H0>` calls (`-25.0 pp`, 95% family CI `[-50.0 pp, 0.0 pp]`).
  - `eval-rung2`: `realized_wins = 1`, `realized_losses_or_ties = 23`; `never_install` (`0.0000`) beat `frozen_transcript_predictor` (`-6.4541`), `always_install` (`-6.5508`), and `simple_helper_length` (`-6.5508`).
- **Stage 3 Decision:** Stopped honestly on development data (`RUNG2_NOT_EARNED`). **No Rung 2 or Rung 3 claim is made; holdout stays SEALED and Rung 4 stays LOCKED.**

## Run Receipts & GPU Lease Telemetry

| Stage / Run | Split | Units | Key Result | GPU Lease Audit | Artifact |
| :--- | :--- | ---: | :--- | :--- | :--- |
| Stage 1a (original textbook fixture) | `train` (`3` fam x `3` prob x `2` cap) | 18 | `ordinary` 11/18 vs `no_helper` 14/18 (`-16.7 pp`, **NOT QUALIFIED**) | `1,223` polls @ `0.5s`, `0` intrusions, `762.8s` | `stage1_qwen3_4b_batched_20261128/stage1_receipt.json` |
| Stage 1b (domain-helper fixture) | `train` (`3` fam x `4` prob x `2` cap) | 24 | `ordinary` 16/24 (`12` exec-helper) vs `no_helper` 4/24 (`+50.0 pp`, **QUALIFIED**) | `1,907` polls @ `0.5s`, `0` intrusions, `1191.6s` | `stage1_domain6_qwen3_4b_20261128/stage1_receipt.json` |
| Stage 2a + 2b (paired installation) | `val` (`3` disjoint fam x `4` prob x `2` cap) | 24 | `score_and_input` 16/24 vs `score_only` 22/24 (`-25.0 pp`, **RUNG2_NOT_EARNED**) | `1,776` polls @ `0.5s`, `0` intrusions, `1189.2s` | `stage2_val_domain6_qwen3_4b_20261128/stage2_receipt.json` |

## Stage 1b Family Breakdown (Qualified)

| Train Family | Helper | `no_helper` Solved | `ordinary_named_fn` Solved | `ordinary` Solved w/ Executed Helper |
| :--- | :--- | ---: | ---: | ---: |
| `run_codec` | `advance_rle_block` | 2 / 8 | 4 / 8 | 2 / 8 (`19` runtime calls each on `rle_02`) |
| `interval_algebra` | `apply_weighted_span` | 0 / 8 | 6 / 8 | 6 / 8 (`9–17` runtime calls per solve) |
| `protocol_fsm` | `step_frame_parser` | 2 / 8 | 6 / 8 | 4 / 8 (`37–45` runtime calls per solve) |
| **Total** | | **4 / 24 (16.7%)** | **16 / 24 (66.7%)** | **12 / 24 (all 3 families)** |

## Stage 2 Disjoint Validation Breakdown (`DEV_VAL_PROBLEMS`, `45s`/arm)

| Validation Family | Helper | `score_only_alias` Solved (Exec `<H0>`) | `score_and_input_alias` Solved (Exec `<H0>`) | Mean Time (`score_only` vs `score_and_input`) |
| :--- | :--- | ---: | ---: | ---: |
| `version_semver` | `parse_semver_key` | 6 / 8 (`4` exec, `58` calls) | 4 / 8 (`2` exec, `26` calls) | `24.8s` vs `33.3s` |
| `calendar_business` | `shift_business_day` | 8 / 8 (`6` exec, `52` calls) | 8 / 8 (`6` exec, `52` calls) | `16.0s` vs `23.5s` |
| `expr_rpn_vm` | `eval_safe_op` | 8 / 8 (`6` exec, `106` calls) | 4 / 8 (`2` exec, `42` calls) | `18.2s` vs `33.0s` |
| **Total** | | **22 / 24 (91.7%, 216 calls)** | **16 / 24 (66.7%, 120 calls)** | **`19.1s` vs `29.4s`** |

## Mechanistic & Attribution Findings

1. **Unused-slot induction collision & exposure-aligned code masking:** On `Qwen3-4B-Instruct-2507`, unused vocabulary slots (`151669..151935`) share the same embedding scale/direction as `<tool_call>`, causing `frozen_alias` to emit `<tool_call>` instead of `<H0>`. Keeping `<H0>` in a compact `[SYSTEM_SWITCH]` adaptation header while masking `sel_mask` and negative non-`<H0>` tokens strictly to the `[ASSISTANT]` code block eliminated `<H0>` spam and lifted `score_only_alias` from `0%` to `91.7%` (`22/24`, `216` executed `<H0>` calls). Under `rung3_contract.json`, this supports **action selection only** (`score_only_beats_frozen`).
2. **Separating optimizer scaling from `E_in[<H0>]` concept:** In Stage 2a (`lr=0.012`), `delta_in` grew to L2 norm `~2.76` (`7.4x` Qwen3-4B's `0.37` base embedding norm), disrupting attention on `sem_01`, `vm_02`, and `vm_03`. A controlled follow-up lowering `lr_in` to `0.002` (`delta_in` norm `~0.44`) recovered `sem_01` (`PASS`, `16` runtime calls) and `vm_02` (`PASS`, `19` runtime calls), showing optimizer overscaling explained 4/6 regressions.
3. **Why `score_and_input_alias` still did not beat `score_only_alias` or `ordinary_named_fn`:** Even at natural embedding scale (`lr_in=0.002`), `score_and_input_alias` paid `~6s` extra wall-clock setup for 36-layer backprop without surpassing `score_only_alias`'s `91.7%` (`22/24`) validation ceiling, and on `rle_01` + `rle_02` (`DEV_PROBLEMS`), zero-setup `ordinary_named_fn` (`2/2`, `15–19` runtime calls) beat both `<H0>` alias arms (`0/2`). When the full helper manual is present in-context at generation time on a 4B model, attention to the prompt already supplies helper semantics once `W_out[<H0>]` makes `<H0>` selectable.
4. **Next falsifiable hypothesis (not started):** Testing `E_in[<H0>]` in a context-compression regime where the full helper manual is NOT repeated verbatim at generation time (or on a smaller model after adding `SlidingWindowCache` support for Gemma-3 1B so `score_only_alias` does not saturate at `91.7%`).
