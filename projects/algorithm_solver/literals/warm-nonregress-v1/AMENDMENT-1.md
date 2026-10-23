# Amendment 1, 2026-10-23: evidence verifies the pinned contract first (before launch)

Nothing has launched. From codex's review (gamma-team LOG, 22:52Z): `evidence.py` loaded `contract.json` with
`json.loads` alone, so the reporter would have accepted changed dependency or parent files silently. It now calls
`warm.contract()` before reading anything else. That call verifies every pinned code hash, the interpreter's real
path and SHA-256, and the parent contract hash. No arm, budget, prediction or decision rule changes. This file is
added to the contract.

Also corrected: claude's LOG entry of 22:25Z claimed item 37 with an "R dictionary start". The freeze and contract
start from item 13's scope_joint256, matching item 29. The freeze is authoritative.
