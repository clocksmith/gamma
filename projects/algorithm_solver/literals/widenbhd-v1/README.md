# widenbhd-v1: larger nonregression neighbourhoods from item 43 (board item 55)

[Freeze](FREEZE.md) `3041ad392`, [amendment 1](AMENDMENT-1.md) `65eb9c750` and `3c08b7165` (codex-approved). The run
started at 02:03Z on cores 10 and 11, one per arm. Each arm used its 3,000 s LNS budget, and both exited 0.

[evidence.py](evidence.py):
- verifies the contract first;
- replays all 400 programs, coverage-safe;
- reconciles every counter with the move logs;
- enforces the nonregression invariant;
- asserts that the seed reproduces item 43's 8,285.

The record-time comparator was bound explicitly to **item 51 flat** (`lexfrac-v1/evidence/results.json`, `c287fe48…`),
the current best at record time. [Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

## Result: a successor of item 43, but not of item 51; item 51 stays the current best

| | Item 43 (seed) | k80 | k120 | Item 51 flat (record-time best) |
| --- | ---: | ---: | ---: | ---: |
| Moves / accepted | – | 6 / 1 | 5 / 0 | – |
| Solver: optimal / time limit | – | 4 / 2 | 0 / 5 | – |
| Fit selections | 24,074 | 24,071 | 24,074 | 24,069 |
| Fit programs better / worse | – | 3 / 0 | 0 / 0 | – |
| Dev-val actions | 8,285 | 8,283 | 8,285 | 8,283 |
| Median / p90 actions | 62.5 / 155 | 62.5 / 155 | 62.5 / 155 | 62.5 / 155 |
| p95 selections | 195 | 195 | 195 | 195 |
| Single-character fraction | 49.542% | 49.530% | 49.542% | 49.505% |
| Package bytes | 14,977 | 14,976 | 14,977 | 14,979 |
| Dev-val vs item 43: better / same / worse | – | 2 / 98 / 0 | 0 / 100 / 0 | 2 / 98 / 0 |

- **k80** passes readiness against R and every incremental check against item 43, so it is a frozen-rule successor of
  item 43. Against item 51 it fails two checks: actions are equal, not strictly fewer, and the fraction is 49.530%,
  above 49.505%. Its per-program actions equal item 51's on all 100 dev-val programs, from a different dictionary
  (`9898248e…`). The record-time replacement resolved with **no eligible candidate**.
- **k120** accepted nothing. All 5 of its repairs ended at the 600 s limit with no improvement over the warm start.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| K1 | some arm accepts at least 3 moves | **false** (1 and 0) |
| K2 | k120 has more time-limited repairs than k80 | true (5 vs 2) |
| K3 | some arm lowers fit by more than 5 | **false** (3) |
| K4 | some arm is a successor of item 43 | true (k80) |
| K5 | both arms: 0 fit worse, at most 5 dev-val worse | true |
| K6 | full coverage, no failure | true |

## What this shows and does not show

- **Shows.** Doubling or tripling the neighbourhood from item 43 does not unlock more breadth-safe gains within
  3,000 s. With k = 80, fewer repairs fit in the budget (6), and one helped. With k = 120, every 600 s repair hit
  the limit. Together with item 48, where k = 40 accepted 2 of about 15 moves, this suggests item 43's region is close
  to a local optimum for capped exact repairs at these budgets.
- **Does not show** that longer per-repair limits or a different solver configuration would not help k120. Only
  600 s was tested. The descriptive narrow reference (item 48, k = 40) is a separate run, not a matched arm.
