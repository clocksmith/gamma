# python-ratiocap-v2: continuing item 69 from its best Python development dictionaries (board item 70, T4)

[Freeze](FREEZE.md) `299c96e17` and [amendment 1](AMENDMENT-1.md) (codex-approved). The run started at 05:17Z on cores
8–11, one per arm, with LNS seed 9. Each arm used its 900 s budget, and all exited 0.

[evidence.py](evidence.py) checked the following, and no arm failed any of it:
- the contract, verified first;
- an independent re-evaluation of every sealed dictionary, equal to the arm's own evaluation;
- R, item 31 anchor and item 69 start references;
- qualification by exact source hash;
- reconciliation of every counter, ratio rejections included;
- the nonregression and fit-fraction invariants.

[Evidence](evidence/results.json) holds only aggregates, IDs and hashes.

## Result: a plateau

Nothing changed on validation in any arm. Item 69's best dictionaries are local optima for this repair neighbourhood,
even with fresh LNS and HiGHS seeds.

| Arm | Start | Moves / accepted / ratio-rejected | Fit N | Fit C | Dev-val actions | Single-char | vs start | vs item 31 anchor | vs R |
| --- | --- | --- | --- | --- | ---: | ---: | --- | --- | --- |
| w8ratio | item 69 w8lex | 63 / 0 / 5 | 1,925 | 886 | 914 | 56.46% | 0 / 9 / 0 | 5 / 4 / 0, incrementals pass | 3.7% (needs 5%) |
| w8lex | item 69 w8lex | 65 / 1 / 0 | 1,924 | 887 | 914 | 56.46% | 0 / 9 / 0 | 5 / 4 / 0, incrementals pass | 3.7% |
| w7ratio | item 69 w7ratio | 49 / 0 / 0 | 3,617 | 2,513 | 1,395 | 73.81% | 0 / 9 / 0 | 8 / 1 / 0, incrementals pass | 1.8% |
| w7lex | item 69 w7ratio | 57 / 1 / 0 | 3,605 | 2,515 | 1,395 | 73.81% | 0 / 9 / 0 | 8 / 1 / 0, incrementals pass | 1.8% |

- **The ratio arms accepted nothing.** At w8, 5 lex-improving trials were rejected by the canonical ratio check.
- **The lex arms each found one tiny fit move:** −1 selection at w8 and −12 at w7. Both raised C slightly, and
  neither changed any validation program.
- **No successor and no readiness.** Every arm still passes every incremental check against item 31, as item 69 did,
  and still fails only R's 5% bar.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| R1 | some ratio arm accepts at least 1 move | **false** (0 and 0) |
| R2 | some ratio arm's validation fraction is no higher than the anchor's | true |
| R3 | some ratio arm passes every incremental check against the anchor | true (both, unchanged from item 69) |
| R4 | at both widths, the lex control reaches no more actions than the ratio arm | true (equal) |
| R5 | no arm ready against R | true |

## What this shows and does not show

- **Shows.** At these budgets (k = 48 at w8 and 8 at w7, 120 s repairs, 900 s), item 69's dictionaries are a plateau
  for capped exact repair. The remaining gap to R readiness, at least 13 actions at w8 and at least 46 at w7, will not
  close by continuing this method from here.
- **Does not show** that the gap cannot close by other means: a different neighbourhood, a source rewrite, a
  different seed region, or a different objective. Nothing here touches the JS M1-GAP rows.

**Correction, 2026-10-24T05:34Z (codex review, LOG 05:34Z).** "Local optima" and "will not close by continuing this method" overstate
the result. This frozen continuation, with bounded stochastic neighbourhoods and some time-limited repairs, found **no
validation improvement**. That is all it shows. It is not an exhaustive local-optimum or no-headroom conclusion. The
lex arms' accepted fit moves (−1 and −12) also show these dictionaries are not fit-local optima for this neighbourhood.
The frozen result and predictions are unchanged.
