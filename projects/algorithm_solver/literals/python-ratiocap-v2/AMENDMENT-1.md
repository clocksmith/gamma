# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. evidence.py was run once end to end on a stand-in. Each arm carried its seed dictionary from
item 69, unchanged, plus a one-line synthetic `moves.jsonl`. It only re-measured item 69's recorded results and did
no search. It reproduced:
- w8 (item 69's w8lex): fit N 1,925, fit C 886, 914 validation actions, fraction 56.464%;
- w7 (item 69's w7ratio): fit N 3,617, fit C 2,513, 1,395 actions, fraction 73.81%, 8/1/0 against the anchor.

Receipt: `python-ratiocap-v2/standin-prefreeze/results.json`, SHA-256 `a74cb81b…`. No code, arm, budget, prediction or
rule changes. This file is added to the contract.
