# Amendment 1, 2026-10-24: exact checks on the rounded integral point (before launch)

Nothing has launched. A fresh-context Claude subagent reviewed the freeze `ba7b48be6`, standing in for codex, who is
out until 2026-10-30. It found **no blocker**. All 8 tests passed, every contract hash matched, and `capped.py` was
byte-identical to python-ratiocap-v1's.

**The fix.** Its main residual risk was numerical. `solve(..., integral_arcs=True)` checked rows on HiGHS's
unrounded point with an absolute 1e-6 tolerance. The JS ratio row has coefficients of about ±1.2·10⁴ (N_inc ≈ 24,069
and C_inc ≈ 11,997). An integer-feasible point off by 10⁻¹⁰ on a few arcs would then fail the row check and abort an
arm on a valid move. Item 51 passed the same absolute checks without a ratio row, so this may not bite, but the check
was wrong in principle.

[capped.py](capped.py) now does the following:
- asserts integrality within 1e-6, as before;
- rounds the point;
- checks every row **exactly** on the rounded integral point. The data and the point are integers, so the check is
  exact in float64;
- compares the objective with HiGHS's under a relative tolerance of 1e-9.

No arm, seed, budget, rule or prediction changes, and the 8 tests pass. capped.py is no longer byte-identical to
item 69's. The only difference is this check.

**The reviewer's other minor notes**, kept as limits of the evidence:
- coverage-failed arms skip move-log reconciliation;
- killed arms are recorded by exit code only;
- `lns_seconds` and the incumbent snapshots are not reconciled;
- `validation_loaded: false` is guaranteed by code order, not measured;
- `/usr/bin/node` is not in the runtime pins;
- ties broken by ID can raise canonical C at equal N, and so cause ratio rejections unrelated to the row itself.

The README will disclose the smoke run and the stand-in that the FREEZE plans. This file is added to the contract.
