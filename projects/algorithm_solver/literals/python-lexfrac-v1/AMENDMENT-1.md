# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. evidence.py was run once end to end on a stand-in. Each arm carried its own seed dictionary,
unchanged, plus a one-line synthetic `moves.jsonl`. It only re-measured existing results and did no search. It
reproduced the known values:
- w8 arms (item 65's w8): fit 1,933 selections, validation 929 actions, fraction 57.391%, 4/5/0 against the item 31
  anchor's 935;
- w7k8 (the w7 anchor, equal to R): fit 3,680 selections, validation 1,420 actions.

It exercised the start-versus-anchor reconciliation, the N, C and objective counters, the w8lex-versus-w8flat pairing
and the Z1–Z5 output. Receipt: `python-lexfrac/standin-prefreeze/results.json`, SHA-256 `dbba1390…`. No code, arm,
budget, prediction or rule changes. This file is added to the contract.
