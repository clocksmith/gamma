# breadth13-v1: breadth-aware exact repairs carried onto item 13 (board item 29)

[Freeze](FREEZE.md) `942f8cc6e`, [amendment 1](AMENDMENT-1.md) `5678466b5` and its receipt correction `5ad8e7bf3`,
all codex-approved. The run started at 21:53Z on cores 11–13, one per arm. Each arm used its full 5,400 s LNS budget
(5,402 s), and all three exited 0.

Before reporting, `succ.contract()` was run as a separate preflight with the pinned interpreter at 23:23:15Z. It
verified the code, runtime and parent hashes, which the frozen evidence.py does not check itself (codex review, LOG
22:52Z). [evidence.py](evidence.py) then replayed every sealed dictionary independently over all 400 programs.
Qualification is reused by exact source hash from item 13's receipt, and all 400 were asserted.
[Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

**Result: no successor, and item 24 remains the current best.** All three arms stay ready against R, but none passes
the incremental rule against item 13.

| Arm | Moves (accepted) | Fit selections | Fit better / worse | Dev-val actions | Median / p90 actions | Median / p95 selections | Single-char | Package bytes | vs item 13: better / same / worse |
| --- | --- | ---: | --- | ---: | --- | --- | ---: | ---: | --- |
| item 13 seed | – | 24,750 | – | 8,504 | 62.5 / 155 | 61.5 / 199 | 49.89% | 14,724 | – |
| unweighted | 24 (13) | 24,130 (−2.51%) | 87 / 97 | 8,353 (−1.78%) | 63.5 / 155 | 62.5 / **169** | 50.70% | 15,168 | 26 / 38 / 36 |
| nonregress | 18 (0) | 24,750 | 0 / 0 | 8,504 | 62.5 / 155 | 61.5 / 199 | 49.89% | 14,724 | 0 / 100 / 0 |
| relative | 30 (24) | 24,461 (−1.17%) | 152 / 109 | 8,475 (−0.34%) | **62.0** / 154 | 61.0 / 196 | 51.93% | 15,344 | 48 / 17 / 35 |

For reference, item 24 has 8,336 actions, median 61.5 and p95 197 selections, and 49.60% single-character selections.

- **Solver statuses.** unweighted: 19 optimal, 5 time limit. relative: 29 optimal, 1 time limit. nonregress: all 18
  repairs reached the 300 s limit without a returned improvement.
- **Failed checks against item 13.**
  - unweighted: fraction, median, and more than 25 programs worse.
  - relative: fraction, and more than 25 programs worse.
  - nonregress: fewer actions.
- **Against item 24,** every arm fails fewer actions, fraction and more than 25 worse. unweighted also fails the
  median.

## What is new here

- **Tail.** unweighted has p95 169 selections, the lowest p95 of any development dictionary so far: item 24 has 197,
  and item 30's D10 has 174. It got there by concentrating gains, so 36 programs got worse and the median rose by one
  action. This is a tail result, not a breadth result.
- **Relative weighting on item 13.** On item 13, relative weighting lowered the median action count (62.5 → 62.0)
  and improved 48 programs. On R in item 22, it had raised the median. It still made 35 programs worse, and it
  raised the single-character fraction by 2.0 points.
- **Nonregress.** The nonregression repair accepted nothing in 18 cold-started repairs from item 13. This reproduces
  item 22's stall. Item 37 (warm-nonregress-v1) tests the warm start on this same seed.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| Q1 | unweighted −1.5 to −3.5% fit and below 8,504 dev-val, but fails on the median or on more than 25 worse | true (−2.51%, 8,353; fails both) |
| Q2 | nonregress: 0 fit worse, dev-val −0.3 to −1.5%, at most 15 worse | **false** (no move; 0.0%) |
| Q3 | relative's actions and worse count fall between nonregress and unweighted | true (8,475; 35 worse) |
| Q4 | at least one successor (even odds) | **false** |
| Q4b | no new current best | true |
| Q5 | median above 55, p95 above 180, fraction above 45% | **false**: unweighted p95 is 169 |
| Q6 | all decode, no illegal entry, qualification reused for all 400 | true |

## What this does not show

- That breadth cannot be protected on item 13. Only these three objectives, this seed and this budget were tested.
- That the p95 gain transfers. It is consumed-development evidence from an adaptive seed. M1's gates of median 32,
  p95 96 and 10% remain far away.
- Anything about item 24's optional character slots, which this stage does not use. Stacking those repairs onto item
  24 belongs to T3.

**Note, 2026-10-23 23:55Z** ([warm-nonregress-v1](../warm-nonregress-v1/README.md), item 37). The nonregress stall
recorded here is not caused by a missing warm start. On the same seed, RNG and first snapshot, item 26's direct-HiGHS
model (`threads=1`, `random_seed=8`, cap rows) solved the nonregression repairs that SciPy's `milp` could not, and
warm and cold followed identical trajectories. Read this stage's nonregress row as an outcome of the solver path: the SciPy `milp`
interface, its configuration or the model build. Which factor matters is not isolated. No number above changes.
