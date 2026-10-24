# alphabet96-v2: repair from item 77's coverage-robust dictionary, with corrected solver checks (board item 78, T1/T3)

[Freeze](FREEZE.md) `9296d383f` and [amendment 1](AMENDMENT-1.md) `b076d62d9`, which fixes the start-dictionary hash
(found by the smoke), makes H3 false on failure, and corrects a docstring. **Review:** a fresh-context Claude subagent
stood in for codex, who is out until 2026-10-30, and found no blocker. The run started at 17:14:36Z and ended at
18:04:47Z on cores 8–10. All three arms exited 0.

**Disclosed pre-launch runs:**
- A fit-only smoke, `--smoke 1`, re-run after the amendment.
- An evidence stand-in on the smoke's sealed dictionaries: receipt `alphabet96-v2/standin-prelaunch/evidence-results.json`,
  `8d50ed00…`. **lastdrop is a deterministic re-serialization, so the stand-in already measured its final outcome
  before launch.** That outcome was dev-val unchanged, so H1 was known to be false at launch. The two repair arms were
  not affected.

[Evidence](evidence/results.json) (`81b55033…`):
- fresh replays of item 77's drop (8,337), item 51 (8,283) and item 13 (8,504), equal to their published rows;
- the full-alphabet and coverage invariants;
- counters reconciled with the move logs.

## Result: negative; the repair gains fit and loses dev-val, and ID placement does nothing

| Arm | Universe | Moves / accepted / optimal | Fit N / C (start 24,162 / 12,107) | Dev-val actions (start 8,337) | Median / p90 | Single-char | vs start | vs item 13 |
| --- | --- | --- | --- | ---: | --- | ---: | --- | --- |
| lastdrop | restored characters last | – | 24,162 / 12,107 | 8,337 | 62.5 / 155 | 49.970% | 0 / 100 / 0 | 41 / 42 / 17 |
| repair43 | after item 43's entries | 34 / 3 / 33 | 24,137 / 12,090 | **8,342** | **63.5** / 154 | 50.049% | 6 / 92 / 2 | 43 / 38 / 19 |
| repairlast | restored characters last | 35 / 3 / 34 | 24,137 / 12,090 | **8,342** | **63.5** / 154 | 50.049% | 6 / 92 / 2 | 43 / 38 / 19 |

- **The corrected check works.** 69 repairs ran at M = 32,768 with no abort, and 67 of them were solved to optimality.
- **The repair gains on fit and loses on dev-val.** Fit fell by 25 selections, with 17 single characters fewer and no
  fit program worse. Dev-val rose by 5 actions, the median went 62.5 → 63.5, and the fraction went 49.970% → 50.049%.
  This is the pattern of items 72 and 75 (JS) and item 74 (Python).
- **The restored characters' dictionary IDs do not matter here.** lastdrop matches item 77 on every dev-val program's actions
  (0 / 100 / 0) and on the dev-val fraction. The two repair arms each accepted 3 moves and reached the same fit
  and dev-val totals. Their sealed dictionaries differ in serialization (`e21beb53…` and `c3586e8f…`).
- **Gates.** Every arm is ready against R. No arm is robust-ready: all fail the fraction check against item 13
  (49.893%), and the repair arms also fail the median. None is a successor of item 51, and the record-time
  replacement has no candidate.
- **Item 77's drop dictionary (8,337) stays the best coverage-robust development dictionary.** It beats item 13 on
  actions, median, p90 and package, but not on fraction.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| H1 | lastdrop's fraction below 49.970% | **false** (equal; known from the stand-in before launch) |
| H2 | some arm robust-ready | **false** |
| H3 | both repair arms accept at least 1 move | true (3 and 3) |
| H4 | some repair arm below 8,337 | **false** (8,342) |
| H5 | all arms complete | true |

## What this shows and does not show

- **Shows.** Restoring full alphabet coverage costs item 51 54 dev-val actions (item 77). Capped fit-only repair cannot
  recover that cost. At this neighbourhood scale, its fit gains again make dev-val slightly worse. The canonical
  fraction does not depend on where the four restored characters sit in the ID order.
- **Does not show** whether a different objective or a source-side change could make a 96-character dictionary beat
  item 13 on fraction as well. It shows nothing about confirmation or the M1 gap, and the M1-GAP rows are unchanged.
