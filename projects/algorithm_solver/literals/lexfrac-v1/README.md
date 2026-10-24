# lexfrac-v1: lexicographic N-then-C nonregression repair from the current best (board item 51)

[Freeze](FREEZE.md) `9276c3174`, [amendment 1](AMENDMENT-1.md) `e444f3f1b` and `a850516a8`, the latter adding the fixed
universe ID order (codex-approved). The run started at 01:23Z on cores 8 and 9, one per arm. Each arm used its 3,000 s
LNS budget, and both exited 0.

[evidence.py](evidence.py):
- verifies the contract first;
- replays all 400 programs, coverage-safe;
- reconciles N, C and the M·N + C objective with the move logs;
- enforces the nonregression invariant;
- asserts that the seed reproduces item 43's 8,285.

The record-time comparator was bound explicitly to item 43's evidence (`c75ba8bc…`, arm nonregress), which was the
current best at record time: item 48 recorded no successor, item 54 had not recorded, and item 55 was running.
[Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

## Result: a frozen-rule successor of item 43, by a small margin

Both arms accepted the same 2 moves and ended on the **identical dictionary** (`75ff15af…`). lexnc against flat is
the same on all 400 programs. The frozen ranking (actions, then package bytes, then arm name) selects **flat** on the
name tie. The record-time replacement resolved with both arms eligible.

| | Item 43 (seed) | flat (selected) = lexnc |
| --- | ---: | ---: |
| Moves / accepted | – | 17 / 2 |
| Fit selections N | 24,074 | 24,069 |
| Fit single characters C | 12,003 | 11,997 |
| Fit programs better / worse | – | 5 / 0 |
| **Dev-val actions** | 8,285 | **8,283** |
| Median / p90 actions | 62.5 / 155 | 62.5 / 155 |
| Median / p95 selections | 61.5 / 195 | 61.5 / 195 |
| **Single-character fraction** | 49.542% | **49.505%** |
| Package bytes | 14,977 | 14,979 |
| Dev-val vs item 43: better / same / worse | – | 2 / 98 / 0 |

Every readiness check against R and every incremental check against item 43 passes, so this is **the new current
best** under the frozen rules.

## Attribution: read this before using the result

- **The lexicographic C objective did nothing here.** Both arms made the same 2 moves to the same dictionary.
- **The fraction gain comes from the fixed universe ID order, not from search.** Item 48 (`4a4fba9a9`) ran the same
  flat repair from item 43 and also gained −5 fit selections and −2 dev-val actions. There the single-character
  fraction **rose** by 0.012 points, because each trial was serialized as `fixed + chosen`. Here, amendment 1
  serializes every trial in item 43's order followed by the sorted pool. With canonical tie-breaking by smaller ID,
  that ordering gives a **lower** fraction (−0.037 points) for an equal-N result. The difference between "fails the
  fraction gate" (item 48) and "passes" (item 51) is therefore a dictionary-ID ordering effect of about 0.05 points.
- **The gain is small:** 2 dev-val actions and 0.037 fraction points, with no change to the median or p95.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| L1 | lexnc accepts at least 2 moves | true (2) |
| L2 | lexnc's dev-val fraction below 49.54% | true (49.505%) |
| L3 | lexnc's dev-val actions at most 8,285 | true (8,283) |
| L4 | lexnc's fit fraction below flat's | **false** (identical) |
| L5 | lexnc is a successor of item 43 | true |
| L6 | full coverage, no failure | true |

## What this shows and does not show

- **Shows.** From item 43, the capped repair still finds a 2-action breadth-safe gain. A fixed, order-preserving ID
  scheme makes canonical tie-breaking favour fewer single-character selections here.
- **Does not show:**
  - that a lexicographic N-then-C objective helps; it made no difference in this run;
  - transfer; this is consumed-development evidence, and confirmation is owner-gated;
  - any material change to the M1 gap: median 61.5 against 32, p95 195 against 96, fraction 49.5% against 10%.

  The ID-order sensitivity is itself a finding. Canonical costs near a gate can flip on entry order, so future
  comparisons should fix the order the same way across arms and runs.
