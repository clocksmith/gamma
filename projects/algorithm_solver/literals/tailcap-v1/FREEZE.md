# tailcap-v1: tail-weighted nonregression repair from the current best (board item 48)

## Question

Item 43 (nonregress24-v1, `ded5c3fef`) is the current best: 8,285 dev-val actions, median 61.5 and p95 195
selections, single-character fraction 49.54%, and 21 programs better and 0 worse against item 24. Its uncapped
control reached p95 165 selections, but only by making 20 programs worse.

This stage asks whether a **tail-weighted** objective, under the same per-program nonregression caps, lowers the p95
without making any program worse. Under the caps no program can rise, so any strict decrease of the weighted
objective strictly lowers total fit selections. The tail emphasis therefore cannot be bought with regressions.
Codex suggested this direction (LOG 00:59Z); the design is claude's.

## Inputs

- **Seed.** Item 43's selected nonregress dictionary, pinned by SHA-256 `f53db5b5…`: 256 entries, 92 characters and
  164 learned.
- **Sources.** Its fixed sources, which are item 13's scope_joint256 sources. `fit-sources.json` is pinned, and
  `sources.json` is read only after the seal.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed-validation programs. This is adaptive development,
  since item 43 was itself selected on these dev-val outcomes.
- **Closed sets.** The final held-out 100 and the protected 66 stay closed.
- **Pre-freeze runs.** No corpus search. [test_capped.py](test_capped.py) passes 7 synthetic tests, including an
  exhaustive optimum for the weighted capped objective. One disclosed seed stand-in exercised evidence.py end to end. It
  re-measured item 43's existing results only and did no search. It reproduced fit 24,074 and dev-val 8,285, with
  47 tail programs at the seed cut of 122 fit selections. Receipt: `tailcap/standin-prefreeze/results.json`,
  `72894b4f…`.

## Arms (one core each, threads 1, both warm-started, both capped)

Both arms use item 43's model and LNS loop:
- item 26's direct-HiGHS occurrence-flow model with one nonregression cap row per fit program,
  `sum(arcs of p) <= cap_p`, where cap_p is p's current exact cost;
- k = 40, the top 3,000 shared fit strings of length 2–64 plus 1,000 random pool strings, and `random.Random(8)`;
- 300 s per repair and a 3,000 s LNS budget;
- a warm start from the fully checked incumbent, `threads=1` and `random_seed=8`.

| Arm | Objective |
| --- | --- |
| tail | `sum_p w_p * cost_p`, with w_p = 10 if p's **seed** fit cost is at or above the seed's nearest-rank 85th percentile, else 1. The weights are fixed for the run. |
| flat | `sum_p cost_p`: item 43's own method continued from its result, as the matched control. |

**Acceptance** requires a strict decrease of the arm's exact rescored objective, no banned entry, and no fit program
worse; both arms assert the last. The rescored value must not exceed the solver's objective by more than 0.25, and
must equal it when the solver reports optimal.

**Validation** opens after the seal. It uses the unchanged validation sources under the sealed dictionary, with no
refit. An unencodable row is a retained failure.

## Checks, qualification and costs

These follow item 43.
- **evidence.py** verifies the contract first: code, runtime, HiGHS extension, parent hashes, and the assertions
  guard. It also verifies the item 43 evidence by its SHA-256.
- **Replay.** Every sealed dictionary is replayed over all 400 programs, coverage-safe.
- **Reconciled counters.** Every counter is rebuilt from the replay and from `moves.jsonl`. This includes the
  weighted final objective and the number of tail programs, which are recomputed from the seed costs.
- **Seed check.** The seed must reproduce item 43's 8,285 dev-val actions.
- **Qualification** reuses item 13's passing receipts by exact source hash, asserted for all 400.
- **Comparison.** In addition to the standard outputs, tail is compared with flat as paired counts on fit and on
  dev-val.

## Predictions

- **T1:** tail accepts at least 2 moves.
- **T2:** tail's dev-val p95 is below 195 selections.
- **T3:** flat lowers total fit selections more than tail.
- **T4:** tail is a successor of item 43 and so becomes the new current best. I put this at roughly even odds.
- **T5:** both arms end with 0 fit programs worse (by construction) and at most 5 dev-val programs worse than the
  seed.
- **T6:** both arms keep full coverage, and neither fails.

## Decision rules (frozen in evidence.py)

These are the standing rules.

**Readiness** against the pinned R baseline:
- full coverage, every program qualified, the audit clean and all 400 decoded;
- at least 5% fewer dev-val actions;
- median and p90 actions strictly lower;
- at least 60 programs better and at most 25 worse;
- single-character fraction no higher;
- package bytes at most 105%.

**Successor of item 43, which is then the new current best.** Ready against R, **and** against item 43:
- strictly fewer actions;
- median, p90 and single-character fraction no worse;
- at most 25 programs worse;
- package at most 105%.

A p95-only gain does not pass. Rank by actions, then package bytes, then arm name. A successor only motivates an
owner-approved, separately frozen confirmation. M1 is unchanged.

## Resources and rules

- Cores 10 and 11, one process per arm, `OMP_NUM_THREADS=1`, and the launcher under `taskset -c 10-11`.
- Each arm runs under `timeout --kill-after=10 4800` and a 10 GiB RLIMIT_AS. Optimized Python is refused, and every
  killed arm is a retained failure, with no restarts.
- Cross-review by codex before launch. No training, learned scorer, private-source publication, protected opening,
  BITS deployment, human study, or ledger, claim or catalog write.
