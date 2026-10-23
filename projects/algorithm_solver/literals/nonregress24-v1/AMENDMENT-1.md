# Amendment 1, 2026-10-23: a hard per-arm kill cap and an assertions guard (before launch)

Nothing has launched. These changes come from codex's review of `19ad4bf05` (gamma-team LOG, 23:57Z).

1. **Hard cap.** The launcher used `timeout 4800`. That sends only SIGTERM, and the signal can stay pending inside an
   overrunning native HiGHS call, so it was not a hard cap. Each arm now runs under `timeout --kill-after=10 4800`,
   which escalates to SIGKILL 10 s after the cap. A killed arm's nonzero exit code, 124 or 137, is kept in
   `results.json` and becomes a retained failure under `failed_arms`. A new synthetic test checks this: a child that
   ignores SIGTERM under `timeout --kill-after=2 1` exits 137 in under 10 s.
2. **Assertions guard.** `contract()` now asserts that Python's assertions are enabled (no `-O`, no
   `PYTHONOPTIMIZE`) before any contract check. The proof and acceptance checks rely on asserts.

Codex also noted that warm feasibility is a guarantee about the model. A runtime error remains possible, and it is a
retained failure, not a successful process.

No arm, objective, budget, prediction or decision rule changes. This file is added to the contract.
