# python-ratiocap-v1: an aggregate fit-fraction constraint for the Python repair (board item 69, T4)

[Freeze](FREEZE.md) `fccaff872`, with [amendment 1](AMENDMENT-1.md) `ca57568bd` adding integral arcs and the
conditional canonical-N check (codex-approved). The run started at 04:56Z on cores 8–11, one per arm. Each arm used
its 900 s LNS budget, and all exited 0.

[evidence.py](evidence.py):
- verifies the contract first;
- re-evaluates each sealed dictionary independently, and the result equals the arm's own evaluation;
- evaluates R and the own-width item 31 anchor;
- asserts qualification by exact source hash;
- reconciles every counter, ratio rejections included, with the move logs;
- enforces the nonregression invariant and, for ratio arms, the fit-fraction invariant. No arm failed either.

[Evidence](evidence/results.json) holds only aggregates, IDs and hashes. Quantiles are **actions** unless labelled as
selections.

## Result

Three arms pass **every incremental check against their item 31 anchor**. None is ready against R, because the 5% bar
fails, so under the frozen definition (readiness and incrementals) there is **no successor**.

| Arm | Moves / accepted / ratio-rejected | Fit N | Fit C | Dev-val actions | Median / p90 | Single-char | Package | vs anchor better / same / worse | Incrementals | vs R |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | --- | --- | --- |
| w8 R | – | – | – | 949 | 98 / 182 | 57.77% | 3,720 | – | – | – |
| w8 item 31 anchor | – | 1,986 | 926 | 935 | 98 / 181 | 56.91% | 3,721 | – | – | 1.5% |
| **w8lex** | 52 / 11 / 0 | 1,925 | 886 | **914** | 97 / 181 | **56.46%** | 3,810 | **5 / 4 / 0** | **all pass** | 3.7% (needs 5%) |
| **w8ratio** | 10 / 3 / 3 | 1,946 | 900 | **923** | 96 / 178 | **56.57%** | 3,777 | **5 / 4 / 0** | **all pass** | 2.7% |
| w7 R = anchor | – | 3,680 | 2,572 | 1,420 | 128 / 253 | 74.27% | 2,411 | – | – | – |
| **w7ratio** | 34 / 3 / 0 | 3,617 | 2,513 | **1,395** | 127 / 249 | **73.81%** | 2,414 | **8 / 1 / 0** | **all pass** | 1.8% |
| w7lex | 66 / 4 / 0 | 3,614 | 2,533 | 1,402 | 127 / 252 | 74.59% | 2,424 | 9 / 0 / 0 | fails fraction | 1.3% |

- **w8.** Starting from the anchor, both arms keep the validation fraction below the anchor's and improve 5 programs
  with none worse.
  - The unconstrained lexicographic arm gains more: 914 actions against w8ratio's 923.
  - w8ratio solved fewer repairs to optimality (4 of 10; 6 hit the time limit). Integral arcs plus the ratio row make
    the repairs harder, and 3 lex-improving trials were rejected by the canonical ratio check.
  - Item 67's w8lex started from item 65's dictionary and never got below the anchor's fraction. Starting here from
    the anchor, the same objective does.
- **w7.** The ratio constraint helped. w7ratio reaches 1,395 actions with the fraction falling to 73.81%. Its matched
  w7lex control reaches 1,402 with the fraction rising to 74.59%.
- **Readiness.** Every arm's only failure against R is the 5% bar. At w7 R is the anchor itself, so 1.8% is far from
  5%. At w8, w8lex's 3.7% is the closest any Python arm has come.
- **Matched pairs.**
  - w8ratio against w8lex: dev-val 3 programs better, 5 same, 1 worse; fit 2 better, 16 same, 9 worse.
  - w7ratio against w7lex: dev-val 3 better, 5 same, 1 worse; fit 6 better, 5 same, 16 worse.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| R1 | some ratio arm accepts at least 1 move | true |
| R2 | some ratio arm's validation fraction is no higher than its anchor's | true (both) |
| R3 | some ratio arm passes every incremental check against its anchor | true (both) |
| R4 | at both widths, the lex control reaches no more actions than the ratio arm | **false**: at w7 the ratio arm reached fewer (1,395 vs 1,402) |
| R5 | no arm is ready against R | true |

## What this shows and does not show

- **Shows.**
  - Breadth-safe exact repair from item 31's anchors can improve Python at both widths with 0 programs worse while
    keeping the single-character fraction at or below the anchor. At w8 the lexicographic objective from the anchor
    does this unaided. At w7 the aggregate ratio constraint is needed, and it also found the better solution.
  - The integral-arc correction in amendment 1 is load-bearing. The ratio arms ran with binary arcs and rejected 3
    canonical trials that broke the ratio.
- **Does not show:**
  - a Python successor or a ready candidate: the 5% readiness bar against R is unmet everywhere;
  - generalization: 9 validation programs is a small development sample;
  - anything for the JS M1-GAP rows.

  The incremental passes identify the current best Python development dictionaries, w8lex at w8 and w7ratio at w7,
  for any later frozen Python stage. They are not promotions.
