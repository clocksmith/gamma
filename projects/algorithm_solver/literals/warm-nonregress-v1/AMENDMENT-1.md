# Amendment 1, 2026-10-23: evidence verifies the pinned contract first (before launch)

Nothing has launched. From codex's review (gamma-team LOG, 22:52Z): `evidence.py` loaded `contract.json` with
`json.loads` alone, so the reporter would have accepted changed dependency or parent files silently. It now calls
`warm.contract()` before reading anything else. That call verifies every pinned code hash, the interpreter's real
path and SHA-256, and the parent contract hash. No arm, budget, prediction or decision rule changes. This file is
added to the contract.

Also corrected: claude's LOG entry of 22:25Z claimed item 37 with an "R dictionary start". The freeze and contract
start from item 13's scope_joint256, matching item 29. The freeze is authoritative.

## Further prelaunch fixes (codex final review, LOG 22:58Z)

- **HiGHS extension pinned.** The contract now pins the HiGHS extension that item 26's `solve()` actually loads,
  `scipy/optimize/_highspy/_core…so`, by real path and SHA-256. `contract()` verifies it. FREEZE.md promised scipy
  pinning; until now only the version string was checked.
- **No unreconciled copied counters.** evidence.py rebuilds these counters itself before evaluating W1–W6:
  - from the replay: start and final fit selections, and fit programs better or worse than the seed;
  - from the retained `moves.jsonl`: moves, accepted moves, feasible moves, optimal moves and statuses.

  It asserts that each one equals the arm's own report. It also asserts that every warm move was warm and
  feasible, and every cold move cold. Only reconciled values are published, and the registered predictions W1–W6
  are emitted.

No objective, budget, gate or prediction changes.

**Pre-launch stand-in check, disclosed.** After these fixes, evidence.py was run once end to end on a stand-in. The
stand-in has two arms, each carrying the unchanged sealed seed dictionary and a one-line synthetic `moves.jsonl`.
It only re-measures item 13's existing results and does no search. The replay, the counter reconciliation and the
prediction output all ran; the stand-in reproduces 8,504 actions. The receipt is
`warm-nonregress/standin-prefreeze/results.json`,
`17d39f3a7b6f59b4be8da689aba12def078e3f93c8296935ed8e290f0ef612de`. No corpus search ran before launch.
