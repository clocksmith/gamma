# BITS Paired-Switch Experiment Protocol (`paired-switch-v1`)

**Status:** Separate study (kept strictly separate from the two existing BITS
papers: Six-Bit leads for the fixed-set capacity result and Three Objectives
releases alongside it for the fresh-code evidence).

## Question

After a running model already knows how to select and execute a helper, does
changing what the helper token `<H0>` **feeds back into the model** (its input
embedding `E_in[<H0>]`) improve verified problem solving at equal total work,
beyond an equally adapted **score-only** alias (`W_out[<H0>]` only) and an
ordinary named function baseline?

## 1. Reproducible Switch Point

- First canonical fixture: `skip_equal(xs, i)` on `dup_02_unique_triplets_zero`
  (`fixtures/skip_equal_switch_point.json`).
- Save a solver session after **two verified failed attempts** that mishandle
  duplicate values.
- Snapshot captures: exact `prefix_token_ids`, contiguous `positions`,
  structured `verifier_feedback`, `search_frontier`, `remaining_budget`, exact
  `rng_state` (Python, NumPy, PyTorch CPU), and tested helper boundary cases
  (`empty_suffix`, `run_of_duplicates`, `end_of_array`).
- Reserve `<H0>` before the run. Fail closed if its symbol or token ID appears
  anywhere in the saved prefix (system messages, attempts, tool responses, or
  pre-switch text).
- At the switch, expose the identical helper description, operand convention,
  assignment, arguments, punctuation, boundary behaviors, and syntax mask to
  every arm. Bind `<H0>` once for the remainder of the session (`SingleBindRegistry`).
- Every arm executes the exact same tested implementation (`implementation_sha256`
  verified in every verdict).

## 2. Three Token Arms + Practical Baseline

| Arm | Output row scoring `<H0>` | Input embedding after `<H0>` |
| --- | --- | --- |
| `frozen_alias` | Original | Original |
| `score_only_alias` | Adapted (100% of setup budget) | Original (`delta_in == 0`) |
| `score_and_input_alias` | Adapted (shared setup budget) | Adapted (shared setup budget) |
| `ordinary_named_fn` | Ordinary tokens (0 adaptation) | Ordinary tokens (0 adaptation) |

- Both adapted arms receive the same maximum optimizer steps and the same total
  elapsed-time allowance. Their actual setup time reduces the time left to
  search. Adaptation uses only information visible at the switch point.
- When `tie_word_embeddings=True`, `PairedSwitchAdapter` decouples `delta_out`
  and `delta_in` via non-invasive forward hooks without mutating backbone
  weights or any non-`<H0>` row (`max_abs_diff == 0.0` verified by SHA-256).

## 3. Cache Reuse and Input-Effect Isolation

1. **Forward-only cache reuse:** Because `<H0>` is absent from the saved prefix,
   editing `E_in[<H0>]` leaves historical attention keys and values bit-exact
   unchanged (`historical_kv_max_abs_diff == 0.0`). Immediately at the switch
   boundary, re-score the cached pre-head hidden state with the **updated**
   output row (never stale pre-switch logits), and verify cached continuation
   logits match a full from-scratch rebuild from identical IDs within declared
   numerical tolerance (`1e-4` fp32, `1e-2` bf16).
2. **Forced-call isolation check:** Copy one exact output row (`shared_delta_out`)
   into both branches and toggle **only** `E_in[<H0>]`.
   - Pre-call check immediately before `<H0>` is consumed: any non-zero logit
     difference **fails the fixture** (`pre_call_max_abs_diff == 0.0` required).
   - Force the identical `<H0>` call, operands, and verifier response into both
     branches and compare subsequent scores and top-1 decisions.
   - A post-call difference isolates an input-embedding effect; whether that
     effect helps requires free search.

## 4. Rung 2 Development Families and Switch Predictor

- Development families (`dev_families.py`): `duplicate_handling` (`skip_equal`),
  `interval_processing` (`merge_span`), and `graph_traversal` (`push_unvisited`).
- Each family includes `useful_once`, `repeatedly_useful`, and `irrelevant_decoy`
  problems, evaluated at both narrow (`cap=2`) and wide (`cap=32`) remaining
  search caps.
- The switch-time predictor (`predictor.py`) uses strictly information visible
  at the switch point and is judged against `always_adapt` and `never_adapt` on
  new families.

## 5. Rung 3 Frozen Evaluation Bar

- Freeze adaptation procedure, budgets, stopping rule, and minimum worthwhile
  gain (`rung3_contract.json`) **before** scoring untouched families.
- Pair runs by `(problem_id, switch_point_id)`. Charge helper proposal,
  adaptation, generation, verification, retries, and unsuccessful branches.
- Keep refusals and timeouts in the denominator; report solve rate at fixed
  total compute and verifier limits, family-clustered paired uncertainty,
  elapsed time, and peak memory.
- Set one positive `--arm-budget-seconds` for every arm before running either
  search width. Run arms serially on the same device. Charge the measured
  switch-time prediction and historical prefix prefill once in full to each arm,
  then start its remaining clock before binding, tokenizing or adapting. The
  helper is supplied at the switch. Model loading and recreating the two
  already-completed attempts precede the switch and have separate receipt
  timings. The forced-call diagnostic runs after search, outside the decision
  path; its time is reported separately.
- Synchronize device work at billing boundaries and between model operations.
  Before generating a candidate and again before invoking its verifier, require
  the whole configured verifier timeout to fit in the remaining allowance.
  Charge the actual duration of each call, including process startup and
  teardown. The subprocess timeout is capped by the same absolute deadline.
  Timeouts, refusals and retries consume the same clock. Record an in-flight
  operation's actual overrun and score a late verdict as unsolved. The
  receipt's `total_work_units` and `work_to_first_verified` are elapsed seconds.
  A comparison in FLOPs requires separate instrumentation.
- **Claim boundaries:**
  - `score_only > frozen`: supports better action selection only.
  - Useful input representation: claimed **only** if `score_and_input` beats
    equally funded `score_only` in free search, the forced-call check passes,
    and the gain holds against `ordinary_named_fn`.
  - If `ordinary_named_fn` matches installation: retain helper reuse as the
    explanation and stop there.

## 6. Rung 4 Gate (Locked)

- Do **not** begin cache-invalidation or live-edit replay engineering unless
  Rung 3 establishes a search benefit worth preserving.
- If unlocked later, compare any historically-relevant live cache edit against
  both the unused-slot method and optimized replay retaining completed verifier
  work and every valid cached prefix.
