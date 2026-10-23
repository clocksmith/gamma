# breadth-lns-v1: breadth-aware exact LNS objectives at 256 entries

## Question

This is gamma-team board item 22 (claude; proposed by codex), goals 2a/2b.
[mip-lns-v1](../mip-lns-v1/README.md) cut 256-entry dev-fit selections 3.26% and dev-val actions
2.59%, but the dev-val gain was concentrated: 33 programs better and 45 worse, with the median one
action worse. This stage asks whether changing only the objective inside the same exact repairs
trades some total gain for breadth.

## Inputs

These are as in mip-lns-v1: cost-decomposition-v1's allowlist, R dev-fit 300 and dev-val 100, and
the pinned L-R-256 dictionary. Validation opens only after each arm's dictionary is sealed. The final
held-out 100 and the protected 66 stay closed. Dev-val is consumed development, and mip-lns-v1's
dev-val outcome motivated this stage.

**Pre-freeze exposure, dev-fit only.** One 150 s smoke of all three arms, in which every first move
hit the smoke time limit and was rejected.

## Arms (256 entries; all three matched)

| Arm | Repair objective (exact HiGHS MILP over all 300 fit programs) | Acceptance (exact canonical rescoring) |
| --- | --- | --- |
| unweighted | total selections (mip-lns-v1's objective, under this code) | strictly fewer total selections |
| nonregress | total selections, plus a per-program constraint inside every repair: no fit program may cost more than under the current incumbent | strictly fewer total selections; asserted that no fit program got worse |
| relative | Σ_p w_p · selections_p, with integer w_p = round(10^6 / start_p) and start_p the program's cost under the pinned dictionary | strictly lower weighted objective |

**Shared settings.** The same seed (8), the same per-move procedure as mip-lns-v1 (free 40 random
learned entries; offer the freed entries plus the top 3,000 ranked pool strings plus 1,000 random
pool strings), full legal capacity (256 minus the kept entries), at most 300 solver seconds per
move, and a 5,400 s LNS budget per arm. There is **no polish**: mip-lns-v1's unweighted polish added
only 10 selections, and here it would blur the objectives.

**Checks on every feasible solver point:**
- the exact score of the arm's own objective must not exceed the solver objective, and must equal
  it at status 0 (relative tolerance 1e-6);
- in `nonregress`, no fit program may get worse.

Each move and accepted incumbent is written privately as it happens.

Three processes pinned to cores 26–27, 28–29 and 30–31 (scipy exposes no HiGHS thread option),
PYTHONHASHSEED=0. [test_breadth.py](test_breadth.py) checks the weighted and the capped repairs
against brute force on more than 20 tiny instances.

## Measurement

**Per arm:** moves and accepted moves, solver statuses, start and final fit selections, the final
objective, and the fit programs better and worse than at the start.

**On dev-val, per arm and for the pinned dictionary:** actions with total, median, p90, p95, worst,
and the counts within 32 and 96; the single-character fraction; dictionary and package bytes;
per-problem actions; and paired better/same/worse counts, against both the pinned baseline and the
unweighted arm.

Every program is encoded and decoded through the canonical codec, and the whole-solution audit covers
fit and validation.

**Readiness (unchanged and unweighted).** This is the frozen bar from the earlier literal stages.
Against the pinned L-R-256 baseline on dev-val, an arm is ready only if all of these hold:
- 100/100 programs decode;
- the audit is clean;
- at least 5% fewer actions;
- median and p90 both lower;
- at least 60 programs improve and at most 25 worsen;
- the fraction does not increase;
- package bytes are at most 105% of baseline.

## Predictions

- **B1:** unweighted lands within 1% of mip-lns-v1's pre-polish dev-fit result (25,268); this is
  time-dependent, so not exact.
- **B2:** nonregress has zero fit programs worse than the start (true by construction; it checks the
  machinery), and fewer dev-val programs worse than unweighted.
- **B3:** relative has a lower dev-val median than unweighted.
- **B4:** both breadth arms achieve a smaller total dev-fit reduction than unweighted.
- **B5:** no arm is ready.
- **B6:** everything decodes, and the audit is clean.

No source rewriting, scorer, training, BITS change or M1 claim. Dictionaries stay private.
