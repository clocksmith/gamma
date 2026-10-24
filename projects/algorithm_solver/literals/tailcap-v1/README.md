# tailcap-v1: tail-weighted nonregression repair from the current best (board item 48)

[Freeze](FREEZE.md) `e14f90abf`, [amendment 1](AMENDMENT-1.md) `39595d6a6` and `f8ab9ec5a` (codex-approved). The run
started at 01:05Z on cores 10 and 11, one per arm. Each arm used its 3,000 s LNS budget, and both exited 0.

[evidence.py](evidence.py):
- verifies the contract first;
- replays all 400 programs, coverage-safe;
- reconciles every counter, including the weighted objective and the 47 tail programs, with the move logs;
- enforces the nonregression invariant;
- asserts that the seed reproduces item 43's 8,285 dev-val actions.

The record-time comparator was bound explicitly to item 43's evidence (`c75ba8bc…`, arm nonregress). That was the
current best at record time: item 46 stopped with no verdict, and item 47 is fit-only. [Evidence](evidence/results.json)
holds only aggregates, IDs and hashes.

## Result: no successor; the tail weighting made no difference

Both arms accepted the same 2 moves and ended on the **identical dictionary** (`23a4f27a…`). Tail against flat is the
same on all 300 fit and all 100 dev-val programs.

| | Item 43 (seed) | tail | flat |
| --- | ---: | ---: | ---: |
| Moves / accepted | – | 16 / 2 | 15 / 2 |
| Solver: optimal / time limit | – | 15 / 1 | 12 / 3 |
| Fit selections | 24,074 | 24,069 | 24,069 |
| Fit programs better / worse | – | 5 / 0 | 5 / 0 |
| Dev-val actions | 8,285 | 8,283 | 8,283 |
| Median / p90 actions | 62.5 / 155 | 62.5 / 155 | 62.5 / 155 |
| Median / p95 selections | 61.5 / 195 | 61.5 / 195 | 61.5 / 195 |
| Single-character fraction | 49.5418% | 49.5540% | 49.5540% |
| Package bytes | 14,977 | 14,979 | 14,979 |
| Dev-val vs item 43: better / same / worse | – | 2 / 98 / 0 | 2 / 98 / 0 |

- **The failed check.** Both arms pass readiness against R and every incremental check against item 43 except one:
  **the single-character fraction rises by 0.012 points**, and the frozen rule needs it to be no higher.
- **Current best.** No successor, and the record-time replacement resolved with no eligible candidate. Item 43 remains
  the current best.
- **Tail weighting.** It weighted 47 fit programs, those with seed cost of at least 122 selections, ten times. It did
  not change which moves improved anything. From item 43 only 2 of about 15 repairs found an improvement in either
  arm, so item 43 looks close to a local optimum for this neighbourhood.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| T1 | tail accepts at least 2 moves | true (2) |
| T2 | tail's dev-val p95 below 195 | **false** (195) |
| T3 | flat lowers fit more than tail | **false** (equal) |
| T4 | tail is a successor of item 43 | **false** (fraction +0.012 points) |
| T5 | both arms: 0 fit worse, at most 5 dev-val worse | true (0 and 0) |
| T6 | full coverage, no failure | true |

## What this shows and does not show

- **Shows.** From item 43, this LNS neighbourhood (k = 40, 300 s repairs) is nearly exhausted under the nonregression
  caps. Tail weighting under those caps does not reach different moves. The p95 did not move.
- **Does not show** that the tail cannot be lowered without regressions. Only this weight (10 on the top 15%), this
  neighbourhood and this budget were tested. Larger neighbourhoods, longer solver limits or a different seed were
  not.
