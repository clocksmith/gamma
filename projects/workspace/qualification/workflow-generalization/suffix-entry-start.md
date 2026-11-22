# Sandbox suite from the entry screen: the index matcher's certification step, exercised

On the sandbox suite the index matcher certified nothing, because the cases begin past the taught
entry screen ([`suffix-both-suites.md`](./suffix-both-suites.md)). Its clean score on the 24
near-misses was reached by abstaining. This diagnostic begins every interior-start case on the
taught entry screen instead, so the run walks the first two steps itself and the matcher reaches
its certification step.

**Status: diagnostic, written after the fact.** It was first run in scratch and then repeated from
the committed harness. No rule was written beforehand. Nothing here is a qualification result.

## What changed in the cases

- `--entry-start` moves the start screen from the interior screen to the entry screen. The
  fixtures are otherwise unchanged.
- "No action" expectations count actions after the two taught entry steps.
- The profile matcher's guard-learning checks assume an interior start and are skipped.

## Result, 2026-11-21, commit `67126d8`, clean tree

No model was called. The `src/` tree is `fd77556`, the same as at `597d5fe`.
Receipt: [`suffix-entry-start-sandbox.json`](./suffix-entry-start-sandbox.json).

Held-out variants, 32 per arm, all completed in every arm:

| Arm | Planner calls | Reused steps | Rejoin within two steps |
| --- | ---: | ---: | ---: |
| Exact | 132 | 48 | 8 of 32 |
| Profile matcher | 24 | 156 | 28 of 32 |
| Index matcher | 84 | 96 | 20 of 32 |
| Both options on | 60 | 120 | 24 of 32 |

Near-misses, 24 per arm:

| Arm | Expectations failed | Which | Completed where forbidden |
| --- | ---: | --- | ---: |
| Exact | 0 | | 0 |
| Profile matcher | 0 | | 0 |
| Index matcher | 8 | dirty-field case, 4; approval case did not complete, 4 | 0 |
| Both options on | 4 | approval case did not complete, 4 | 0 |

## Findings

- **With its prefix accounted, the index matcher does gain here.** An extra toolbar control, a
  dirty field in another form and a clean optional field each go from 4 planner calls to 0. It
  gains nothing when the page is already past a taught step, on a typed slot rename without the
  profile option, or on an untaught route.
- **It certified on the dirty-field near-miss, in all four families.** It replayed the four
  interior steps with no planner call. The suite's rule is that a dirty untracked field in the
  committing form must be rejected before any suffix step runs.
  - **Cause.** The dirty-field guard reads form state. Form state is requested only when the
    profile option is on (`src/client/trace-dag.js` lines 546 and 566, `src/client/workflow-agent.js`
    line 171). With the index option alone, the guard has nothing to read.
  - **With both options on, the guard works.** It refused the dirty field 16 times and the run
    went to the planner.
  - **Effect.** The same six actions that exact matching dispatches through the planner. Review
    rejected the run in every arm.
- **It stopped on the approval near-miss instead of completing.** It clicked the approval, which
  was never skipped. It then refused to continue because the next field was already filled
  (`pending-fill-already-done`) and handed back to the planner. The scripted planner stops unless
  it made the approval click itself, so part of this is the test planner, not the matcher.
- **On hidden drift it certified and replayed.** Review rejected the run, as it does for exact
  matching. The index matcher has no step that learns from that rejection.
- **No arm dispatched an action that exact matching did not also dispatch.** No forbidden run
  completed.

## What this means

- **The index option alone is not ready to be the single matcher.** Its dirty-field guard is
  inactive in the configuration the cross-check used.
- **Both options together are closer.** The guard works and the typed rename is covered. A run
  still cannot enter at a learned state it did not walk to.
- **The repair is small but is a matcher change.** Form state has to be requested whenever either
  option is on. The guard then becomes active on the form suite too, so that suite needs a rerun
  under a rule written first.

## Reproduce

```sh
node projects/workspace/qualification/stage1-suffix-ablation.js OUT.json --entry-start \
  --arms exact-hash-v3,suffix-eligibility-v4,suffix-index-v1,suffix-index-plus-profile  # exits 1
```

## Limits

- Written and run after reading the fixtures and the earlier results.
- A scripted function stands in for the planner. Synthetic snapshots, four clustered families.
- The start-screen change makes these different cases from the frozen ones. The frozen suite's
  result is unchanged.
