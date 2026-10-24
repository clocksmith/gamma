# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. evidence.py was run once end to end on a stand-in. Each arm carried its own-width item 31
anchor's dictionary, unchanged, plus a one-line synthetic `moves.jsonl`. It only re-measured existing results and did
no search. It reproduced the known values:
- w8: fit N 1,986, fit C 926, validation 935 actions, fraction 56.911%;
- w7: fit N 3,680, fit C 2,572, validation 1,420 actions, fraction 74.274%.

It exercised the replay, the ratio-rejection counter, the fraction-invariant check, the ratio-versus-lex pairings and
the R1–R5 output. Receipt: `python-ratiocap/standin-prefreeze/results.json`, SHA-256 `837024cf…`. No code, arm,
budget, prediction or rule changes. This file is added to the contract.
