# BITS Paired-Switch Experiment Protocol (`paired-switch-v1`)

**Status:** Separate study (kept strictly separate from Six-Bit and Three Objectives).
Holdout remains **SEALED** and Rung 4 remains **LOCKED (`LOCKED_PENDING_RUNG3_WIN`)**.

## Staged Gate Order (Make the Helper Matter First)

Do not scale up the alias comparison before passing Stage 1 and Stage 2 on development data:

### Stage 1 — Qualify the Ordinary Helper (`qualify-helper`)
- Compare `ordinary_named_fn` against `no_helper` (the same solver without helper exposure or binding) at equal elapsed-time budgets on development problems spanning multiple families, including one-use (`useful_once`), repeated-use (`repeatedly_useful`), and decoy (`irrelevant_decoy`) helpers.
- Require verified solves that **actually execute the helper at runtime** (`passing_runtime_helper_calls > 0`, recorded separately from syntactic mentions across generated code) across at least two distinct families, with a strictly positive solve-rate gain over `no_helper`.
- **Fail-closed rule:** If the ordinary helper cannot beat `no_helper`, the fixture cannot test the alias (`HELPER_NOT_QUALIFIED`). Stop and improve the fixture before testing `<H0>`.

### Stage 2 — Earn Rung 2 with a Prediction (`eval-rung2`)
- Freeze a helper-agnostic switch-time rule (`predictor.py`) using only pre-switch transcript and switch-time contract features (no family-name lookup tables, no oracle labels).
- Predict when the remaining search will reuse the helper enough to repay installation—including **losses** (decoys / unamortized setup) as well as **wins**.
- Test the frozen rule on **separate development families** (`DEV_VAL_PROBLEMS`: `string_parsing`, `window_aggregation`, `grid_flood`, distinct from the `DEV_PROBLEMS` families `duplicate_handling`, `interval_processing`, `graph_traversal`, while keeping the sealed holdout untouched) against three baselines:
  1. `always_install`
  2. `never_install`
  3. `simple_helper_length`
- Require strictly higher realized net utility than all three baselines plus both `win_recall >= 0.6` and `loss_recall >= 0.6`.

### Stage 3 — Rung 3 Development Gate on an Exclusive GPU (`run-live --require-exclusive-gpu` + `gate-rung3-dev`)
- Run only after Stage 1 and Stage 2 pass, on an **exclusive GPU** (verified free of competing compute processes).
- Give every arm the exact same helper, transcript, and equal wall-clock budget (charging shared prefill, setup, generation, retries, and verification).
- Give `score_only_alias` and `score_and_input_alias` the **exact same training examples and loss positions** (`sel_mask` + `post_mask`); only whether `E_in[<H0>]` (`delta_in`) is trainable differs.
- Judge verified solves by **problem family** against BOTH controls (`score_only_alias` and `ordinary_named_fn`) under the pre-frozen minimum meaningful win (`>= +5 pp`, 95% family-clustered CI strictly `> 0`, executed helper solves across `>= 2` families, `100%` forced-call gate pass with `pre_call_max_abs_diff == 0.0`).
- **Stopping rule:** If joint adaptation cannot beat both controls on development, **stop** (`STOP_ON_DEV`). If it passes, that earns **only a decision about whether to authorize one untouched sealed run** (`ELIGIBLE_FOR_SEALED_DECISION_ONLY`), not a Rung 3 claim yet.

## Mechanical & Cache-Reuse Invariants

- **Reproducible switch point:** Saved after two verified failed attempts; captures `prefix_token_ids`, contiguous `positions`, `verifier_feedback`, `search_frontier`, `remaining_budget`, exact `rng_state`, and tested helper boundary cases. `<H0>` must appear nowhere in the saved prefix (`assert_helper_token_absent`), must encode to one exact token ID and decode back to an executable call (`HelperAliasTokenizer` + `verify_helper_token_roundtrip`), and binds once (`SingleBindRegistry`).
- **Non-invasive single-row split (`PairedSwitchAdapter`):** Decouples `delta_out` and `delta_in` even when `tie_word_embeddings=True`, keeping backbone weights and all non-`<H0>` rows bit-exact (`max_abs_diff == 0.0` by SHA-256).
- **Cache reuse & forced-call isolation:** Historical prefix K/V cache remains bit-exact (`historical_kv_max_abs_diff == 0.0`), switch-boundary rescoring uses fresh `W_out[<H0>]`, and forced-call isolation enforces `pre_call_max_abs_diff == 0.0` while verifying nonzero post-call sensitivity.

## Rung 4 Gate (Locked)

- Status: `LOCKED_PENDING_RUNG3_WIN`. Do not begin cache-invalidation or live-edit replay engineering unless an authorized sealed Rung 3 evaluation establishes a verified search benefit worth preserving.
