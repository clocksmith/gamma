# Amendment 1, 2026-10-23: full decode, binding-cap test, absolute tolerance (before launch)

Codex's review (gamma-team LOG, 20:46Z) asked for these changes. Nothing has run.

1. **Full decode.** The final measurement now encodes and decodes all 400 programs, fit and validation, through
   the canonical codec for both the pinned and the arm dictionary. Validation aggregates are taken from that run,
   and the decoded count and fit selections are recorded. Previously only the 100 validation packets were decoded.
2. **Binding-cap test.** `test_breadth.py` adds a restrictive-cap case where the caps change the choice: texts
   `aaaa` and `bbbb`, alphabet only, candidates `aa` and `bb`, one slot, weights 5 and 1. Uncapped, the repair picks
   `aa`; with caps of 4 and 2 it must pick `bb`; with caps of 2 and 2 it must be infeasible.
3. **Tolerance.** The objective identity checks use an absolute tolerance of 0.25 (`objective_tolerance` in
   `contract.json`) instead of a relative 1e-6. At the weighted arm's scale (about 3e8) the relative tolerance would
   have hidden a discrepancy of several hundred, while the objectives are integers, so any real discrepancy is at
   least 1. Positive integer weights are asserted.

**Interpretation note.** The inverse-cost weights, round(10^6 / start_p), approximate equal relative weighting up to
rounding.

No arm, objective, budget, seed or prediction changes.

Hash changes in `contract.json`:

| File | Before | After |
| --- | --- | --- |
| breadth.py | `e12ef03b1cc0af7d426432f754186a8859f875b1479a710dae0ad5ac72d961c2` | `310b37eea345646eb924a0c57ff1e7cdfa177f46df2b50a9e7405b023a94222b` |
| test_breadth.py | `6cb7e59baae96766d33da573ee4abe1d85a2d781251349d6a1049a245616adcd` | `04b191c45afd59b10ed72a81805687c10bcce8d3a89531e05b3c1cf98df93288` |

This file is added to the contract.
