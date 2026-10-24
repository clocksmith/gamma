# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. evidence.py was run once end to end on a stand-in. Each arm carried its own-width anchor's
unchanged dictionary and a one-line synthetic `moves.jsonl`. The run only re-measured item 31's existing results and
did no search. It reproduced the known values:
- w7: 3,680 fit selections and 1,420 validation actions, equal to R;
- w8: 1,986 fit selections and 935 validation actions, against R's 949.

It exercised the replay, the R and anchor references, the qualification authority, reconciliation and the Y1–Y5
output. Receipt: `python-nonregress/standin-prefreeze/results.json`, SHA-256 `8bcd16da…`. No code, arm, budget,
prediction or rule changes. This file is added to the contract.
