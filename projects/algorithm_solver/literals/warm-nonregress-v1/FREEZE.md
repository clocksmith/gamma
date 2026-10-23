# warm-nonregress-v1: does a checked warm start make the nonregression repair productive? (board item 37)

## Question

In items 22 and 29, the nonregression exact repair forbids any fit program from getting worse, and it protects
breadth: in item 22, 0 programs were worse. But it barely moves:
- **Item 22**, from R: 16 of 18 repairs ended at the 300 s limit with no feasible point found, and 1 move was
  accepted.
- **Item 29**, from item 13: 0 of 8 moves were accepted at 22:41Z, while the run was still going. That is a live
  count, not a result.

These repairs are never infeasible. The removed entries stay among the candidates, so the current dictionary with
its canonical paths is always a feasible point. Both runs cold-started SciPy's `milp`, which cannot accept a start.

Item 26 (seeded-repair-v1) added a checked warm start to a direct-HiGHS model. On unconstrained repairs, the warm
start preserved the incumbent but never improved on it within 90 s. This stage asks whether a warm start, plus the
nonregression rows, turns the breadth-protecting constraint into real gains. Codex suggested it in its review of
item 22 (LOG, 22:21Z).

## Inputs

- **Seed.** Item 13's scope_joint256, the same seed as item 29. Its dictionary and `fit-sources.json` are pinned
  by private SHA-256; `sources.json` is read only after the seal.
- **Data.** The qualified R allowlist: 300 fit and 100 consumed-validation programs.
- **Exposure.** This is adaptive development: the seed was selected on these dev-val outcomes.
- **Closed sets.** The final held-out 100 and the protected 66 stay closed.
- **Sources are fixed.** No rewrite happens in this stage; only the dictionary changes.
- **Pre-freeze runs.** None on the corpus. Only the synthetic tests in [test_capped.py](test_capped.py) ran.

## Arms (256 entries, one core each, threads 1)

Both arms run the same LNS loop as item 29's `succ.py`, adapted here in [warm.py](warm.py):
- k = 40 learned entries removed per move, using `random.Random(8)`;
- candidates are the removed entries, the top 3,000 shared fit strings of length 2–64 ranked by
  occurrence × (length − 1), and 1,000 random pool strings;
- each repair has 300 s, and each arm has a 3,600 s LNS budget.

Each repair solves [capped.py](capped.py)'s model. This is item 26's occurrence-flow model: unit arc costs,
activation links, and a capacity row. It is rebuilt with arc owners, plus one row per fit program,
`sum(arcs of p) <= cap_p`, where cap_p is p's exact cost under the current incumbent. Both arms use item 26's
unchanged `solve()` with `threads=1`, `mip_rel_gap=0` and `random_seed=8`.

| Arm | Difference |
| --- | --- |
| warm | Before each solve, the current incumbent is passed with `setSolution`: every incumbent candidate is active, and its canonical shortest paths are the 0/1 flows. It is first checked against every row, the cap rows included, and against the exact objective identity. |
| cold | The same model, solved without a start. |

**Acceptance** needs a strict decrease of exact rescored fit selections, with no fit program worse (asserted) and
no banned entry. The rescored total must not exceed the solver's objective (tolerance 0.25), and must equal it
when the solver reports optimal.

After the first accepted move the two arms' incumbents diverge, so they are matched procedures, not identical
models. The first snapshot is identical in both arms.

**Validation** opens only after the arm's dictionary and fit seal are written. It uses item 13's unchanged
validation sources under the sealed dictionary, with no refit.

## Checks, qualification and costs

These follow item 29 (breadth13-v1 after amendment 1).
- [evidence.py](evidence.py) re-reads each sealed dictionary, checks its hash against the fit seal, and
  re-measures all 400 sources through the canonical codec. It asserts that the replay equals the arm's own report,
  and all decision rules use the replay.
- A missing arm or a nonzero exit is recorded under `failed_arms`. An illegal entry fails readiness.
- **Qualification.** All sources are byte-identical to item 13's, so qualification reuses item 13's passing
  receipts by exact source hash, asserted for all 400.
- **Charges.** Every literal selection, one Finish per program, dictionary bytes, eight-bit payload, frames and
  padding. Decoder and offline inventories are reported separately.
- **Reported per arm.**
  - Solver outcomes: moves, feasible, optimal and improving moves, and statuses.
  - Program changes: fit programs better or worse.
  - Dev-val: selections and actions (total, median, p90, p95, worst, counts within 32 and 96), the
    single-character fraction and package bytes.
  - Paired counts against the pinned R, the seed and item 24.
  - Warm against cold: paired counts on fit and on dev-val.

## Predictions

- **W1:** cold accepts at most 2 moves, reproducing the stall.
- **W2:** warm returns a feasible point on every repair. A warm start that is not preserved is an assertion
  failure, so this is a machinery check.
- **W3:** warm accepts more improving moves than cold.
- **W4:** warm lowers fit selections by less than 1% from 24,750. Item 26 never improved an incumbent within
  90 s, so I expect small gains.
- **W5:** warm ends with 0 fit programs worse (by construction) and at most 5 dev-val programs worse than the seed.
- **W6:** neither arm becomes the new current best against item 24.

## Decision rules (frozen in evidence.py; the same as item 29's)

**Readiness** against the pinned R baseline:
- every program qualified, the audit clean and all 400 decoded;
- at least 5% fewer dev-val actions;
- median and p90 actions strictly lower;
- at least 60 programs better and at most 25 worse;
- the single-character fraction no higher;
- package bytes at most 105%.

**Successor of item 13.** Ready against R, **and** against the seed:
- strictly fewer actions;
- median, p90 and fraction no worse;
- at most 25 programs worse;
- package at most 105%.

**New current best.** A successor that also passes the same incremental predicates against item 24's optional arm
(8,336 actions; pinned by evidence hash). Rank by actions, then package bytes, then arm name. A successor only
motivates an owner-approved, separately frozen confirmation.

## Resources and rules

- Cores 8 and 9, one process per arm, `OMP_NUM_THREADS=1`, and the launcher under `taskset -c 8-9`.
- Each arm runs under `timeout 5400` and a 10 GiB RLIMIT_AS. The 3,600 s LNS budget is inside that cap; the cap
  also covers setup and validation measurement. An arm killed by a cap is a retained failure, and there are no
  restarts.
- Interpreter and scipy are pinned by real path and SHA-256, and verified in `contract()`.
- Cross-review by codex before launch. No training, learned scorer, private-source publication, protected
  opening, BITS deployment, human study, or ledger, claim or catalog write. Component intent is preserved:
  development measurement only.
