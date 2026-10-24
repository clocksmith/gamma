# Amendment 1, 2026-10-24: disclosed pre-launch evidence stand-in (before launch)

Nothing has launched. evidence.py was run once end to end on a stand-in. Each arm carried its own-width item 31
anchor's dictionary, unchanged, plus a one-line synthetic `moves.jsonl`. It only re-measured existing results and did
no search. It reproduced the known values:
- w8: fit N 1,986, fit C 926, validation 935 actions, fraction 56.911%;
- w7: fit N 3,680, fit C 2,572, validation 1,420 actions, fraction 74.274%.

It exercised the replay, the ratio-rejection counter, the fraction-invariant check, the ratio-versus-lex pairings and
the R1–R5 output. Receipt: `python-ratiocap/standin-prefreeze/results.json`, SHA-256 `837024cf…`. No code, arm,
budget, prediction or rule changes. This file is added to the contract.

## 2. Integral arcs and the canonical-N check under the ratio row (codex review, LOG 04:52Z; blockers)

Nothing has launched. Codex found two correctness blockers, and both are fixed here.

1. **Fractional paths.** Item 26's `solve()` declares only entry activations integer and leaves arc (flow) variables
   continuous, relying on the flow structure for integral paths. A binding aggregate ratio row breaks that structure,
   and the LP can mix paths. On codex's constructed source `abcdefghi`:
   - the seed path a|bc|de|fg|hi has N 5 and C 1, ratio 1/5;
   - the best integral ratio-feasible path, ab|cd|ef|ghi, has N 4 and C 0;
   - the mixture of 2/3 a|bcde|fghi and 1/3 ab|cd|ef|ghi meets the ratio exactly at a lower objective.

   The FREEZE's statements that the ratio row describes an actual path, and that the model equals the brute-force
   optimum, did not hold in general. `capped.solve(..., integral_arcs=True)` now declares **every** variable integer,
   arcs included. All arcs lie in [0, 1], so they are binary. The function is item 26's code, unchanged except for that
   declaration, and it asserts integrality of every variable. **All four arms** use it, so integrality is matched
   between the ratio arms and their lexicographic controls.
2. **The canonical-N equality.** The runner asserted that canonical N equals the solver path's N at optimality. Under
   the ratio row, a longer ratio-feasible path can be optimal while the same dictionary's canonical shortest path has
   fewer selections and breaks the ratio. `run.trial_check` now always asserts canonical N ≤ path N. It requires
   equality only at optimality **and** when the canonical trial itself meets the ratio; in that case the canonical
   path is feasible and lexicographically no worse. Otherwise the trial is rejected and counted as `ratio_rejected`,
   never aborted.

**Tests.** [test_python.py](test_python.py) now has 6 passing tests. The exhaustive ratio-row test uses integral arcs.
The new regression on codex's instance checks:
- continuous arcs give an objective below 4M, and integral arcs give exactly 4M;
- a shorter canonical decode that breaks the ratio is rejected, not aborted;
- without a ratio row, the optimal equality still holds;
- canonical N can never exceed the path's N.

No arm, seed, budget, prediction, gate or validation rule changes, and no corpus run followed. The stand-in in item 1
exercised evidence.py only, which is unchanged by this fix.
