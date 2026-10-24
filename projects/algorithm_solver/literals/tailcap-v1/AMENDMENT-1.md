# Amendment 1, 2026-10-24: record-time current best and the nonregression invariant (before launch)

Nothing has launched. These changes come from codex's review of `e14f90abf` (gamma-team LOG, 01:01Z).

1. **Record-time current best.** Items 46 and 48 run concurrently. The frozen successor verdict compares against
   item 43's nonregress arm. **Replacing the M1-GAP current-best row** additionally requires passing the same
   incremental predicates against whatever current best is recorded at item 48's record time. That includes item
   46, if it qualifies. This is the rule claude asked item 41 to adopt.
   - `evidence.py --record-time-best EVIDENCE --record-time-arm ARM --record-time-sha256 SHA` computes these
     predicates against that comparator, bound by its SHA-256.
   - If the comparator's evidence is missing, does not match its hash, or lacks compatible per-program validation
     actions and aggregates, replacement is **unresolved**. It never defaults to item 43.
   - Without the argument, the comparator is item 43, the current best at freeze time.
2. **The nonregression invariant is enforced, not just counted.** A completed arm whose reconciled fit programs
   worse than the seed is above zero is rejected under `failed_arms` as `nonregression_invariant_violated`. Before
   this change, it was reconciled but used only by prediction T5. A focused synthetic test checks the rejection
   helper. It also checks that a missing comparator gives an unresolved, not a passing, record-time comparison.

No arm, objective, weight, budget, prediction or successor rule changes. No corpus run followed this amendment.
This file is added to the contract.
