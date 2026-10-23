# Amendment 1, 2026-10-23: full-capacity repairs, objective checks, live receipts (before launch)

Codex's review (gamma-team LOG, 19:03Z) asked for these changes. Nothing has run.

1. **Repair budget.** Each repair may now choose up to the full legal capacity, 2^w minus the kept
   entries, instead of the number freed. The freed entries stay candidates, so the incumbent remains
   feasible. Before this change, an accepted move that chose fewer entries than it freed would have
   permanently lost those slots. `test_lns.py` adds a sparse-incumbent test.
2. **Objective checks.** As in mip-audit-v2: whenever the solver returns a feasible point, the run
   asserts `exact <= objective + 1e-6`, and `abs(exact - objective) <= 1e-6` when the status is 0.
   Each move records the solver status, message, objective, dual bound, gap and time. A solver
   optimum is still not an independent certificate, and a timed-out move only proposes a candidate
   for the unchanged exact acceptance test.
3. **Live receipts.** Each move is appended to `w<width>-live/moves.jsonl` as it finishes, and every
   accepted incumbent is written there immediately. Everything stays private.
4. **Wording.** In FREEZE.md, "free arcs" means arcs that need no capacity decision. Each one still
   costs one selection.
5. **Disclosure.** The fit-only smoke used the frozen seeds 7 and 8, so the first moves of the run
   were already observed on dev-fit. The run is not an independent replication of the smoke.

No arm, budget, seed, prediction or readiness criterion changes.

Hash changes in `contract.json`:

| File | Before | After |
| --- | --- | --- |
| lns.py | `ed9008bbdbca2e69145e34c8c7702f791c12d29cdaab3305c9aacc025f2a66d0` | `5284bc2a689cf726a8588961acab44ed9c330d50f3ba95568e4a1856d76189c1` |
| test_lns.py | `f1f45c2a7c9ede7c969acb8ef311758c18080e3946a7b4686f650f13dde7e214` | `e1ac6123dc8daff794008e1b0435b94e918dbe261d518db1268f6316ec75548f` |

This file is added to the contract.
