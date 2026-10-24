# python-lexfrac-v1: fraction-aware w8 continuation and smaller-k w7 on the Python panel (board item 67, T4)

[Freeze](FREEZE.md) `acf686d0d` and [amendment 1](AMENDMENT-1.md) (codex-approved). The run started at 04:26Z on cores
8, 9 and 10, one per arm. Each arm used its 900 s LNS budget, and all exited 0.

[evidence.py](evidence.py):
- verifies the contract first;
- re-evaluates each sealed dictionary independently, and the result equals the arm's own evaluation;
- evaluates R, the own-width item 31 anchor and each arm's own search start;
- asserts qualification by exact source hash;
- reconciles N, C, objective and move counters with the logs.

[Evidence](evidence/results.json) holds only aggregates, IDs and hashes. Quantiles are **actions** unless labelled as
selections.

## Result: no successor; every arm gains actions with 0 programs worse but raises the single-character fraction

| Arm | Moves (accepted) | Fit N | Fit C | Dev-val actions | Median / p90 actions | Single-char | Package | vs anchor better / same / worse |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | --- |
| w8 R | – | – | – | 949 | 98 / 182 | 57.77% | 3,720 | – |
| w8 item 31 anchor | – | 1,986 | – | 935 | 98 / 181 | **56.91%** | 3,721 | – |
| w8 start (item 65) | – | 1,933 | 910 | 929 | 97 / 181 | 57.39% | 3,835 | 4 / 5 / 0 |
| **w8lex** | 53 (5) | 1,923 | **902** | **927** | 97 / 181 | **57.41%** | 3,833 | **5 / 4 / 0** |
| w8flat | 60 (3) | 1,923 | 909 | 929 | 97 / 181 | 57.94% | 3,840 | 4 / 5 / 0 |
| w7 R = anchor = start | – | 3,680 | 2,572 | 1,420 | 128 / 253 | 74.27% | 2,411 | – |
| **w7k8** | 89 (4) | **3,614** | 2,533 | **1,402** | 127 / 252 | 74.59% | 2,424 | **9 / 0 / 0** |

- **Objective comparison.** w8lex and w8flat reach the same fit N (1,923), and w8lex has 7 fewer single-character
  selections. On dev-val, w8lex is better on 1 program, the same on 8 and worse on none against w8flat, with a
  fraction 0.53 points lower.
- **Successor checks.** Each arm passes every incremental check against its anchor **except the fraction**: w8lex
  57.41% against 56.91%, w8flat 57.94%, w7k8 74.59% against 74.27%.
- **Readiness against R.**
  - w8lex fails only the 5% bar (2.3% below R).
  - w8flat and w7k8 also fail the fraction check.
  - w7k8 is 1.3% below R, improving all 9 validation programs.
- **w7 headroom.** k = 8 finds it: 4 accepted moves, fit −1.8% (27 programs better, 0 worse), and dev-val −18
  actions. So item 65's w7 null came from k = 32 timeouts, not from an absence of headroom.

## Predictions

| | Prediction | Outcome |
| --- | --- | --- |
| Z1 | w8lex's fraction below w8flat's | true (57.41% vs 57.94%) |
| Z2 | w8lex's fraction no higher than the anchor's 56.91% | **false** (57.41%) |
| Z3 | w8lex is a w8 successor | **false** (fraction) |
| Z4 | w7k8 accepts at least 1 move | true (4) |
| Z5 | no arm ready against R | true |

## What this shows and does not show

- **Shows.** On Python, breadth-safe exact repair reliably lowers actions without making any program worse. At w7 it
  lowers all 9. But it raises the single-character fraction at both widths, because the selections it removes are
  mostly multi-character ones. The lexicographic C objective reduces that drift, by 0.53 points at w8, but does not
  reverse it. Under the standing "fraction no higher than the anchor" rule, that drift alone blocks every Python
  successor here.
- **Does not show:**
  - that a successor is impossible. A stronger C weight, a C-capped objective (per-program C caps beside the N caps),
    or more budget were not tested;
  - anything for the JS M1-GAP rows, or generalization beyond 9 programs.
