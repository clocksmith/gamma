# Prelaunch amendment 1 — 2026-10-23

Claude reviewed freeze 3ec1f7392 before any corpus run. The overall execution
guard increases from 3,600 to 7,200 seconds to leave headroom for fresh strict
qualification after the declared search phases. Search budgets, cores 0–7,
address-space limits, evidence rules and all promotion predicates are unchanged.
This is a resource cap, not an estimated completion time. The outer supervisor
kills the process group at the cap and preserves failure evidence; no retry.

Items 22 and 29 were unrecorded at this freeze, and item 27 was null, so they
are excluded. Any recorded gain from 22 or 29 receives its own later stacking
freeze on the selected result. Item 14 saved seven validation actions but failed
its character-fraction predicate: S2 tests a component with an action gain but
no prior standalone successor, rather than an already accepted representation.

The original FREEZE.md remains unchanged. This amendment supersedes only its
overall wall guard and clarifies the component inventory. Contract regeneration
pins this amendment and the updated contract generator before launch.
