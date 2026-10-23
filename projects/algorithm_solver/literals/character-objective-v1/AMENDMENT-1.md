# Amendment 1 — 2026-10-23, before any corpus run

Self-review found that pruning after an accepted final-budget move could perform
one extra dictionary evaluation. Keep the legal incumbent with any unused entries
when the budget is already exhausted, rather than rescoring a prune. This makes
the12000-trial ceiling exact without changing the objective or legal capacity.
A seventh synthetic test asserts that pruning at the cap leaves state and counter
unchanged. Original FREEZE remains immutable; code/test/contract hashes updated.
No source/corpus measurement has run. New review requested before launch.
