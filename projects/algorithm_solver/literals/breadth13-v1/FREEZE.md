# breadth13-v1: breadth-aware exact repairs carried onto item 13 (board item 29)

## Question

Can the exact large-neighbourhood repairs of [mip-lns-v1](../mip-lns-v1/README.md) (item 11) and
[breadth-lns-v1](../breadth-lns-v1/FREEZE.md) (item 22) improve item 13's ready candidate without the breadth
damage seen before? Item 11 on R cut dev-val actions 2.59%, but 45 programs got worse. Item 15 stacked LNS on
item 13 naming and reached 8,335 actions, but the median rose from 62.5 to 65. Item 22 tests two breadth-aware
objectives on R. This stage carries all three objectives onto item 13 as a frozen successor attempt (owner
direction 2026-10-23 21:35Z, track T1).

While this freeze was being written, codex recorded item 24 (character-slots-v1, `a8b0ff852`). Its optional
arm is a ready successor of item 13 on the same sources, with 8,336 dev-val actions, and it is now the current
best in M1-GAP. The owner direction names item 13 as this track's seed, and item 24 changes the character slots,
which is a different repair space. So the seed stays item 13. Item 24 is a frozen comparator (below), and
stacking these repairs onto item 24 belongs to T3.

It is frozen **before item 22's validation opens**. At the time of writing, item 22 has published only interim fit
counts in its live receipts. No item 22 dev-val number exists yet, so nothing here is adapted to it.

## Inputs

- **Seed.** Item 13's selected scope_joint256 (`5f3a4bd23`). Its dictionary (`e3cb3e3c…`, the public hash in
  binding-descent-v1/evidence) and its selected fit and validation sources are pinned by private SHA-256 in
  [contract.json](contract.json). A pre-freeze check reproduced item 13 exactly: fit 24,750 selections and dev-val
  8,504 actions, every selection count matching per program, and all 400 source hashes matching item 13's evidence.
- **Data.** The qualified R allowlist (cost-decomposition-v1): 300 fit and 100 consumed-validation programs.
- **Exposure.** The seed was selected on these dev-val outcomes, so this is adaptive development, not confirmation.
- **Closed sets.** The final held-out 100 and the protected 66 stay closed.
- **Sources are fixed.** No rewrite happens in this stage. Only the dictionary changes.

## Arms (256 entries, one core each)

All three start from item 13's dictionary and per-program costs, and use `breadth.repair()` from breadth-lns-v1
unchanged (imported, hash-pinned).

| Arm | Objective | Constraint |
| --- | --- | --- |
| unweighted | total fit selections | none |
| nonregress | total fit selections | no fit program costs more than under the current incumbent |
| relative | sum of w_p × cost_p, with w_p = round(10^6 / start_p) | none |

Weights for relative come from the seed's per-program fit costs and are fixed for the run.

**LNS, as in item 22:**
- k 40 learned entries removed per move, uniformly at random (seed 8);
- candidates: the removed entries, the top 3,000 pool strings by occurrence × (length − 1), and 1,000 random pool
  strings;
- 300 s HiGHS limit per repair, 5,400 s LNS budget per arm;
- pool: all strings of length 2–64 shared in the fit sources, minus banned strings (complete sources and solve
  bodies);
- a move is accepted only on a strict improvement of the arm's own objective under exact canonical rescoring.
  The rescored objective must not exceed the solver's (tolerance 0.25), and must equal it when the solver
  reports optimal. nonregress also asserts its constraint after rescoring.

**Validation** opens only after the arm's dictionary is written and its fit seal hash recorded. It is item 13's own
validation sources, unchanged, measured under the sealed dictionary. There is no refit.

## Checks and qualification

- All 400 sources of every arm are encoded and decoded through the canonical codec (`selection.measure`).
- The whole-solution audit uses fit and validation banned strings, and any illegal entry fails readiness.
- **Qualification.** Every source is byte-identical to item 13's, so qualification reuses item 13's passing
  receipts by exact source hash (`binding-descent-v1/evidence/results.json`, pinned by SHA-256). evidence.py
  asserts the hash of every one of the 400 sources against that receipt. No fresh sandbox job is needed.

## Costs and reporting

**Charges:** all literal selections, one Finish per program, dictionary bytes, eight-bit payload, frames and
padding.

**Reported:**
- fit and validation selections (total, median, p90, p95, worst, counts within 32 and 96) and actions;
- single-character fraction and package bytes;
- paired better/same/worse against the pinned R baseline and against the seed;
- moves, accepted moves, solver statuses including every time-limited repair, and fit programs better or worse
  than the seed.

[evidence.py](evidence.py) writes the public aggregates, IDs and hashes, and applies the rules below.

## Predictions

- **Q1:** unweighted lowers fit selections 1.5–3.5% below 24,750, and lowers dev-val actions below 8,504, but
  fails the successor rule on the median or on more than 25 programs worse than the seed, as item 15 did.
- **Q2:** nonregress ends with no fit program worse than the seed (guaranteed by construction) and cuts dev-val
  actions 0.3–1.5%, with at most 15 dev-val programs worse than the seed.
- **Q3:** relative's dev-val action total and its count of programs worse than the seed both fall between
  nonregress and unweighted.
- **Q4:** at least one arm passes the successor rule. I put this at roughly even odds.
- **Q4b:** no arm becomes the new current best (beats item 24 on all of its predicates).
- **Q5:** no arm gets near the M1 gates. Median selections stay above 55, p95 above 180, and the single-character
  fraction above 45%.
- **Q6:** all 400 sources decode in every arm, no illegal entry appears, and qualification is reused for all 400.

## Decision rules (frozen in evidence.py)

**Readiness** against the pinned R baseline (original sources under the pinned L-R-256), the standing bar:
- every program qualified and the audit clean, and all 400 decoded;
- at least 5% fewer validation actions;
- median and p90 actions strictly lower;
- at least 60 programs better and at most 25 worse;
- single-character fraction no higher;
- package bytes at most 105%.

**Successor.** An arm is a successor of item 13 only if it is ready against R **and**, against the seed:
- strictly fewer validation actions;
- median and p90 actions, and the single-character fraction, no worse;
- at most 25 programs worse;
- package bytes at most 105%.

Successors are ranked by actions, then package bytes, then arm name.

**New current best.** A successor replaces the current-best row in M1-GAP only if it also passes the same
incremental predicates against item 24's optional arm (published per-program actions and aggregates, pinned by
evidence hash in the contract): strictly fewer actions than 8,336, median, p90 and fraction no worse, at most 25
programs worse, and package bytes at most 105% of 14,998. Otherwise a successor is recorded as a successor of
item 13 only. Either way, it can only motivate an owner-approved, separately frozen confirmation.
Item 13's commissioned confirmation is unaffected. A failed arm is kept and reported with every failed check.

## Pre-freeze and pre-launch runs

- The reproduction check described under Inputs (no search, no new dictionary).
- After this document is written, and before the freeze commit, one fit-only smoke of all three arms with a
  120 s LNS budget (`succ.py --smoke 120`), into a scratch directory. It checks wiring only. Its outputs are not
  results and do not change any parameter. Validation is never loaded in smoke mode.

## Resources and rules

- Cores 11, 12 and 13, one process per arm, `OMP_NUM_THREADS=1`, the launcher itself under `taskset -c 11-13`.
  Cores 11–15 are claude's under the owner's 0–15 limit and the codex split. Item 22 stays on 8–10.
- Python: `/home/x/deco/gamma/.venv_rocm/bin/python` (scipy 1.18.1, HiGHS).
- Cross-review by codex after the freeze push, under PLAN's 30-minute rule.
- No training, learned scorer, private-source publication, protected opening, BITS deployment, human study, or
  ledger, claim or catalog write. Component intent is preserved: this is development measurement only.
