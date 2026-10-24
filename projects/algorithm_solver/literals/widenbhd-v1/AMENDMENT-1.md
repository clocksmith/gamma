# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. After the freeze commit `3041ad392`, evidence.py was run once end to end on a stand-in.
- **What it was.** Two arms, each carrying item 43's unchanged dictionary, plus a one-line synthetic `moves.jsonl`.
- **What it measured.** It only re-measured item 43's existing results and did no search. It reproduced dev-val
  8,285.
- **What it exercised.** The reconciliation, the K1–K6 prediction output, and an explicit record-time binding to
  item 43's evidence.
- **Receipt.** `widenbhd/standin-prefreeze/results.json`, SHA-256 `271decb5…`.

No code, arm, budget, prediction or rule changes. This file is added to the contract.

## 2. Three-valued existential predictions (codex review, LOG 02:00Z)

K1, K3 and K4 are existential: some arm accepts at least 3 moves, lowers fit by more than 5, or is a successor. As
first written, they returned False when only one arm completed, even though an unobserved failed arm cannot establish
the negative. They now evaluate as follows:
- **True** if any fully replayed arm satisfies the prediction;
- **False** only if both arms fully replayed and neither satisfies it;
- **None** otherwise.

K2 and K5 already require both arms. K6 predicts completion, so it is False on an incomplete run. A synthetic test
covers four cases: one failed arm with a non-satisfying survivor (None), one failed arm with a satisfying survivor
(True), both replayed with neither satisfying (False), and none replayed (None). 9 of 9 tests pass. No corpus run
followed this change; item 48's history is unchanged.
