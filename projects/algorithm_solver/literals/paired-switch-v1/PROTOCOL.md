# BITS Paired-Switch Experiment Protocol (`paired-switch-v1`)

**Status:** Separate study (kept strictly separate from Six-Bit and Three Objectives); harness review-ready, no experiment started.
Holdout remains **SEALED** and Rung 4 remains **LOCKED (`LOCKED_PENDING_RUNG3_WIN`)**.

## Whole-Run GPU Reservation (`ExclusiveGpuLease`)

A point-in-time foreign-PID check only proves the GPU was idle at startup. Every live GPU stage (`qualify-helper`, `run-stage2-val`, `run-live`) therefore reserves the GPU for the **entire run**:
- Acquires an OS-level non-blocking exclusive lock (`fcntl.flock(LOCK_EX | LOCK_NB)`) on a per-GPU lockfile (overridable via `--gpu-lock-path` / `GAMMA_GPU_LOCK_PATH`, optionally annotated with a host/cluster lease ID via `--external-lease-id`) before model load and holds it through adapter teardown.
- Runs an initial foreign-PID audit, a continuous background watchdog polling GPU compute PIDs throughout the run (`--gpu-poll-interval`, default `5.0s`), and a final audit before releasing the lock.
- Fails closed on lock contention or any mid-run foreign compute intrusion; Stage 3 (`gate-rung3-dev`) rejects any Stage 1, Stage 2, or Stage 3 receipt lacking `lease_held_for_full_run == true`, `exclusive_maintained_throughout_run == true`, `watchdog_polls >= 1`, and `mid_run_intrusions == []`.

## Staged Gate Order (Make the Helper Matter First)

Do not scale up the alias comparison before passing Stage 1 and Stage 2 on development data:

### Stage 1 — Qualify the Ordinary Helper (`qualify-helper`)
- Compare `ordinary_named_fn` against `no_helper` (the same solver without helper exposure or binding) at equal elapsed-time budgets on development problems spanning multiple families, including one-use (`useful_once`), repeated-use (`repeatedly_useful`), and decoy (`irrelevant_decoy`) helpers, under a whole-run `ExclusiveGpuLease`.
- Require verified solves that **actually execute the helper at runtime** (`passing_runtime_helper_calls > 0`, recorded separately from syntactic mentions across generated code) across at least two distinct families, with a strictly positive solve-rate gain over `no_helper`.
- **Scope boundary:** Stage 1 establishes whether the helper is useful, **not** whether installing it as a vocabulary entry pays.
- **Fail-closed rule:** If the ordinary helper cannot beat `no_helper`, the fixture cannot test the alias (`HELPER_NOT_QUALIFIED`). Stop and improve the fixture before testing `<H0>`.

### Stage 2 — Earn Rung 2 with Paired Installation Outcomes (`run-stage2-val` + `eval-rung2`)
- Freeze a helper-agnostic switch-time rule (`predictor.py`) using only pre-switch transcript and switch-time contract features (no family-name lookup tables, no oracle labels).
- Collect **paired vocabulary-installation outcomes** (`run-stage2-val`) on the **separate validation development families** (`DEV_VAL_PROBLEMS`: `string_parsing`, `window_aggregation`, `grid_flood`, strictly disjoint from `DEV_PROBLEMS` `duplicate_handling`, `interval_processing`, `graph_traversal`, while keeping the sealed holdout untouched) under a whole-run `ExclusiveGpuLease`:
  - Run the installed vocabulary entry (`score_and_input_alias`) and the equally adapted single-token alias (`score_only_alias`) with the **exact same helper, transcript, matched adaptation loss positions, and total wall-clock budget**.
- Score the frozen predictor (`eval-rung2`) strictly against those paired `(score_and_input_alias, score_only_alias)` validation outcomes—predicting **losses** as well as **wins**—against three baselines:
  1. `always_install`
  2. `never_install`
  3. `simple_helper_length`
- **Fail-closed rule:** `eval-rung2` rejects Stage 1 (`ordinary_named_fn` vs `no_helper`) comparisons, train-family overlap, unequal total budgets, or unmatched adaptation setup. Require strictly higher realized net utility than all three baselines plus both `win_recall >= 0.6` and `loss_recall >= 0.6`.

### Stage 3 — Rung 3 Development Gate on a Reserved Exclusive GPU (`run-live --require-exclusive-gpu` + `gate-rung3-dev`)
- Run only after Stage 1 and Stage 2 pass, holding a whole-run `ExclusiveGpuLease` across the entire run.
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
