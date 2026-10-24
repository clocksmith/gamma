# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. After the freeze commit `9276c3174`, evidence.py was run once end to end on a stand-in.
- **What it was.** Two arms, each carrying item 43's unchanged sealed dictionary, plus a one-line synthetic
  `moves.jsonl`.
- **What it measured.** It only re-measured item 43's existing results and did no search. It reproduced fit N
  24,074, fit C 12,003 and dev-val 8,285.
- **What it exercised.** The character-count reconciliation, the M·N + C objective reconciliation, the prediction
  output, and a record-time binding to item 43's evidence. The binding resolved, with no eligible replacement.
- **Receipt.** `lexfrac/standin-prefreeze/results.json`, SHA-256 `215d378d…`.

FREEZE.md's "no corpus search" remains true. This stand-in is disclosed because it re-measured consumed data. No
code, arm, budget, prediction or rule changes. This file is added to the contract.
