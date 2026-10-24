# Amendment 1, 2026-10-24: the drop keeps exactly 160 learned entries (before launch)

Nothing has launched. A fresh-context Claude subagent reviewed the freeze `99a367c18`, standing in for codex, who is out
until 2026-10-30. It found no confirmed blocker and one conditional blocker.

**The problem.** The drop's budget row only bounded the kept count from above: at most 160. If an equal-(N, C) solution
left some learned entry unused, HiGHS could keep 159 or fewer. That would drop 5 or more, waste a slot, and crash
evidence.py's exactly-4 check in both arms.

**The fix.** `run.keep_exactly` makes the budget row an equality for the drop only. With no caps and no ratio row, it
is the model's last row, and the function asserts this. It also asserts that the warm start keeps exactly 160. The
runner now asserts `len(chosen) == capacity`. A new synthetic test with entries that occur nowhere checks that warm and
cold solves keep exactly `capacity`, and that the drop test asserts the kept count. All 9 tests pass. The LNS repair is
unchanged and keeps its at-most budget row.

**The reviewer's minor notes, kept as limits:**
- the drop test checks N, not the C tie-break;
- if a drop solve hits its time limit, the two arms may start from different drops, recorded as `same_drop`;
- F1 ranges only over completed arms;
- `fit_programs_worse_than_start` is not re-derived from a replay; it is inherited from item 72.

**The stand-in.** The disclosed fit-only smoke ran before this change. The evidence stand-in is re-run under this
contract on the smoke's sealed drop-arm dictionary. That dictionary is the naive warm start and keeps exactly 160. No
arm, budget, rule or prediction changes. This file is added to the contract.
