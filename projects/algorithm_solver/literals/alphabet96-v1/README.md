# alphabet96-v1: restoring item 51's four missing characters at an exactly minimal cost (board item 77, T1/T3)

[Freeze](FREEZE.md) `99a367c18` and [amendment 1](AMENDMENT-1.md) `416c1eeca`, which makes the drop keep exactly 160.
**Review:** a fresh-context Claude subagent stood in for codex, who is out until 2026-10-30. The run started at
17:04:24Z and ended at 17:07:18Z on cores 8 and 9.

**Disclosed pre-launch runs:**
- A fit-only smoke, `--smoke 1`.
- An evidence stand-in, run on the smoke's naive warm-start drop dictionary: receipt
  `alphabet96/standin-prelaunch/evidence-results.json`, `64defdd4…`. It measured that warm start's dev-val at 8,454.
  It was a pipeline check only, and it changed nothing.

[Evidence](evidence/results.json) (`b465741b…`) holds only aggregates, IDs and hashes.

## Result

### drop (complete): an exact, coverage-robust dictionary that beats item 13 on actions but not on fraction

The exact drop MILP was **solved to optimality in 2.7 s** (gap 0). It restores B, P, R and `_` and drops the 4 learned
entries whose loss costs least: fit N 24,069 → **24,162** (+93), C 11,997 → 12,107.

| | Item 13 (96 chars, frozen subject) | **drop** (96 chars) | Item 51 (92 chars, current best) | R |
| --- | ---: | ---: | ---: | ---: |
| Dev-val actions | 8,504 | **8,337** | 8,283 | 9,048 |
| Median / p90 actions | 62.5 / 155 | 62.5 / 155 | 62.5 / 155 | – |
| Median / p95 selections | – | 61.5 / 195 | 61.5 / 195 | – |
| Single-character fraction | 49.893% | **49.970%** | 49.505% | 55.14% |
| Package bytes | 14,724 | 15,008 | 14,979 | – |
| Coverage by construction | yes | **yes** | no (14 programs depend on learned entries) | – |

- **Against R:** ready, at 73 / 22 / 5.
- **Against item 13:** 41 / 42 / 17, with 167 fewer actions and median, p90 and package within the bounds. The one
  failing check is the fraction, 49.970% against 49.893%. So **not robust-ready** under the frozen rule.
- **Against item 51:** 0 / 94 / 6, with +54 actions. Restoring the four characters costs 54 dev-val actions and
  0.47 points of fraction.

### repair: a retained failure (exit 1), with no restart

On its second move, the repair arm aborted in item 26's inherited `solve()` (`seeded-repair-v1/model.py:71`). That
function checks the objective against HiGHS's with an **absolute** 1e-6 tolerance. With M = 131,072 the objective is
about 3.2·10⁹, where float64 rounding of a 385,902-term dot product exceeds 1e-6. Item 51's M = 32,768 kept its
objective four times smaller, and it passed the same check. This was a check defect, not a model defect. The
reviewer's synthetic probe at this M passed, so it was not caught before launch. Under the frozen rules the arm is a
retained failure. The real fix, a relative objective tolerance, belongs to a new frozen stage.

Move 0, retained in `repair-live/moves.jsonl`, shows something useful. The solver found a path with the same N and
**183 fewer single characters**, but canonical rescoring returned the incumbent's C exactly, so the move was rejected.
Canonical decoding breaks equal-N ties by smaller ID, not by C. That hides C gains, as items 51 and 72 also noted.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| F1 | the exact drop solves to optimality | true (2.7 s) |
| F2 | drop at most 8,303 dev-val actions | **false** (8,337) |
| F3 | some arm robust-ready | **false** (fraction 49.970% against 49.893%) |
| F4 | repair below drop | None (repair failed) |
| F5 | both arms complete | **false** |

## What this shows and does not show

- **Shows** the exact price of coverage robustness for the current best: +93 fit selections and +54 dev-val actions.
  The resulting 96-character dictionary still beats the frozen subject, item 13, by 167 dev-val actions with
  median and p90 unchanged. It misses item 13's fraction by 0.08 points.
- **Does not show** what repair from this dictionary would give, because the arm failed. It also does not show
  confirmation or any change to the M1 gap, and it changes none of the M1-GAP rows.
