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

## 2. A fixed universe order for dictionary IDs (codex review, LOG 01:18Z)

The frozen runner built each trial as `fixed + chosen`. An incumbent entry that was freed and then reselected
therefore moved to the end. The same selected word set could then get different IDs, and through canonical ID
tie-breaking, a different canonical C. That did not implement the fixed order agreed in LOG 01:09Z.

Now a **fixed universe order** is built once: item 43's actual seed order, followed by the sorted non-seed fit-pool
entries. Every trial in **both** arms is serialized as its selected subset in that order (`run.ordered`). Relative
canonical ties are therefore preserved across moves, including for removed and reintroduced entries. The seed
serializes to itself, which is asserted.

A synthetic regression test shows the hazard: the same set in two orders gives different canonical C, while
`ordered` serializes both identically. It also checks that new entries follow the seed entries in sorted order, and
that an entry outside the universe is rejected. 10 of 10 tests pass.

This changes canonical identity, not the optimization objective. No corpus run followed it. The stand-in in item 1
predates this change. The stand-in carried the unchanged seed, which `ordered` serializes to itself, so its
re-measurement is unaffected.
