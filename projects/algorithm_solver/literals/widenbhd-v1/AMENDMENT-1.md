# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. After the freeze commit `3041ad392`, evidence.py was run once end to end on a stand-in.
- **What it was.** Two arms, each carrying item 43's unchanged dictionary, plus a one-line synthetic `moves.jsonl`.
- **What it measured.** It only re-measured item 43's existing results and did no search. It reproduced dev-val
  8,285.
- **What it exercised.** The reconciliation, the K1–K6 prediction output, and an explicit record-time binding to
  item 43's evidence.
- **Receipt.** `widenbhd/standin-prefreeze/results.json`, SHA-256 `271decb5…`.

No code, arm, budget, prediction or rule changes. This file is added to the contract.
