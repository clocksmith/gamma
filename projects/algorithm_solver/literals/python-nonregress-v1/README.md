# python-nonregress-v1: the JS current-best pipeline on the Python panel (board item 65, T4)

[Freeze](FREEZE.md) `f19e17692` and [amendment 1](AMENDMENT-1.md) (codex-approved). The run started at 04:06Z on cores 8
and 9, one per width. Each arm used its 900 s LNS budget, and both exited 0.

[evidence.py](evidence.py):
- verifies the contract first;
- re-evaluates each sealed dictionary independently with item 34's coverage-safe evaluator, and the result equals the
  arm's own evaluation;
- evaluates the own-width R and item 31 anchor references;
- asserts qualification by exact source hash against item 31's receipts;
- reconciles every counter with the move logs.

[Evidence](evidence/results.json) holds only aggregates, IDs and hashes. All quantiles below are **actions**
(selections plus one Finish) unless labelled as selections.

## Result

The breadth-safe repair **transfers at 256 entries**: 4 validation programs better and 0 worse. It is **not** a
successor, because the single-character fraction rises, and it is **not** ready against R, because it is 2.1% better
against a 5% bar. At 128 entries nothing moved.

| Width | Arm | Moves (accepted) | Solver: optimal / time limit | Fit selections | Fit better / worse |
| --- | --- | --- | --- | ---: | --- |
| w7 | item 31 anchor (= R) | – | – | 3,680 | – |
| w7 | this run | 8 (0) | 0 / 8 | 3,680 | 0 / 0 |
| w8 | item 31 anchor | – | – | 1,986 | – |
| w8 | this run | 23 (7) | 18 / 5 | **1,933 (−2.7%)** | 16 / 0 |

| Width | Dev-val (9 programs) | Actions | Median / p90 actions | Median / p95 selections | Single-char | Package bytes | vs anchor better / same / worse | vs R better / same / worse |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |
| w7 | R = anchor = this run | 1,420 | 128 / 253 | 127 / 252 | 74.27% | 2,411 | 0 / 9 / 0 | 0 / 9 / 0 |
| w8 | R | 949 | 98 / 182 | 97 / 181 | 57.77% | 3,720 | – | – |
| w8 | item 31 anchor | 935 | 98 / 181 | 97 / 180 | 56.91% | 3,721 | – | – |
| w8 | **this run** | **929** | **97** / 181 | 96 / 180 | 57.39% | 3,835 | **4 / 5 / 0** | 6 / 3 / 0 |

- **w8 against its anchor.** It passes fewer actions, median and p90 no worse, 0 worse, and package within 105% (3,835
  against 3,721). It fails one check: **the single-character fraction rises from 56.91% to 57.39%.** So it is not a
  successor.
- **w8 against R.** It passes strictly lower median and p90, 6 programs better (the minimum is 6), 0 worse, the
  fraction (57.39% ≤ 57.77%) and the package. It fails only **at least 5% fewer actions**: 929 is 2.1% below 949. So
  it is not ready.
- **w7.** At 128 entries the 96 characters leave 32 learned entries, and k = 32 frees all of them. Every repair is
  then a full re-optimization of the learned set, and all 8 hit the 120 s limit without improving on the warm start.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| Y1 | some width accepts at least 1 move | true (w8: 7) |
| Y2 | some width lowers validation actions below its anchor with 0 worse | true (w8: 929, 4/5/0) |
| Y3 | no width is ready against R | true |
| Y4 | full coverage at both widths | true |
| Y5 | no illegal entry | true |

## What this shows and does not show

- **Shows.** On Python at 256 entries, the JS breadth-safe exact repair finds real fit headroom (−2.7%, 16 programs
  better, 0 worse) and some validation gain (−6 actions, 4 better, 0 worse) from item 31's anchor. As on JS before the
  fixed-ID-order effect, the selection gain came with a slightly higher single-character fraction.
- **Does not show:**
  - a Python successor or a ready candidate;
  - anything at 128 entries, beyond showing that k = 32 is too large for 120 s repairs there;
  - generalization: 9 validation programs is a small development sample, and it does not touch the JS M1-GAP rows.

  A Python run at w7 with smaller k, or a fraction-aware objective at w8, would each need its own freeze.
