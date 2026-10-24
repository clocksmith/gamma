# nonregress24-v1: the breadth-safe direct-HiGHS repair continued from item 24 (board item 43)

[Freeze](FREEZE.md) `19ad4bf05`, [amendment 1](AMENDMENT-1.md) `8b707fafa` and `a69935a42` (codex-approved). The run
started at 23:59Z on cores 10 and 11, one per arm. Each arm used its 3,000 s LNS budget, and both exited 0. No solver
call exceeded its limit: the longest was 229 s.

[evidence.py](evidence.py):
- verifies the pinned contract first, including code, runtime, HiGHS extension and parent hashes, and refuses to run
  with assertions disabled;
- replays each sealed dictionary over all 400 programs, coverage-safe;
- rebuilds every counter from the replay and from the retained `moves.jsonl`;
- asserts that the seed reproduces item 24's 8,336 dev-val actions.

Qualification is reused by exact source hash from item 13's receipt; all 400 were asserted. [Evidence](evidence/results.json)
holds only aggregates, IDs and hashes.

## Result

**nonregress is a frozen-rule successor of item 24, so it becomes the new current best development candidate.** It
improves 21 dev-val programs and worsens none. The uncapped control is not a successor.

| | Item 24 (seed) | **nonregress** | unweighted (control) |
| --- | ---: | ---: | ---: |
| Moves / accepted | – | 22 / 7 | 30 / 13 |
| Solver: optimal / time limit | – | 21 / 1 | 29 / 1 |
| Fit selections | 24,167 | 24,074 (−0.38%) | 23,908 (−1.07%) |
| Fit programs better / worse | – | 41 / 0 | 45 / 55 |
| **Dev-val actions** | 8,336 | **8,285 (−0.61%)** | 8,301 (−0.42%) |
| Median / p90 actions | 62.5 / 155 | 62.5 / 155 | 63.5 / 155 |
| Median / p95 selections | 61.5 / 197 | 61.5 / **195** | 62.5 / **165** |
| Within 32 / 96 selections | 17 / 74 | 17 / 74 | 16 / 73 |
| Single-character fraction | 49.60% | **49.54%** | 50.05% |
| Package bytes | 14,998 | **14,977** | 15,198 |
| Dev-val vs item 24: better / same / worse | – | **21 / 79 / 0** | 19 / 61 / 20 |
| Dev-val vs R: better / same / worse | 74 / 21 / 5 | 76 / 20 / 4 | 71 / 22 / 7 |
| Coverage, fit and dev-val | 300 + 100 | 300 + 100 | 300 + 100 |

- **Successor checks.** nonregress passes every readiness check against R and every incremental check against item
  24: fewer actions, median, p90 and fraction no worse, 0 worse, and a smaller package. It is the selected successor.
- **The control.** unweighted fails two checks against item 24: the fraction rises to 50.05%, and the median rises by
  one action. Its p95 of 165 selections is the lowest yet, but it pays for it with breadth: 20 programs worse.
- **nonregress against unweighted.** On dev-val, nonregress is better on 21 programs, the same on 73 and worse on 6.
  On fit it is better on 59, the same on 218 and worse on 23.
- **Characters.** The repair frees only learned entries, so the dictionary keeps item 24's 92 characters.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| N1 | nonregress accepts at least 2 moves | true (7) |
| N2 | nonregress: 0 fit worse, and at most 5 dev-val worse than item 24 | true (0 and 0) |
| N3 | unweighted lowers fit more than nonregress | true (−259 vs −93) |
| N4 | unweighted has more dev-val programs worse than nonregress | true (20 vs 0) |
| N5 | nonregress is a successor of item 24 | true |
| N6 | both arms keep full coverage, and neither fails | true |

## What this shows and does not show

- **Shows.** The breadth-protecting exact repair stacks on the current best. Starting from item 24, the per-program
  nonregression constraint keeps every fit program at or below its cost and turns a 0.38% fit gain into a 0.61%
  dev-val gain, with no dev-val program worse. The same model without the constraint gains more on fit but loses
  breadth and fraction. This mirrors item 37 on item 13.
- **Does not show:**
  - transfer: this is consumed-development evidence from an adaptive seed, and confirmation is owner-gated;
  - any closing of the M1 gap. The median is 61.5 against 32, the p95 195 against 96, and the single-character
    fraction 49.54% against 10%. The gain is small.
  - which part of the solver path, as opposed to the cap rows, made the direct-HiGHS repair productive (see item 37).
- Item 13 remains the frozen confirmation subject. A successor here can only motivate an owner-approved, separately
  frozen confirmation.
