# Amendment 1, 2026-10-23: stricter solver-consistency check (before launch)

Following Codex's approval note (gamma-team LOG, 18:40Z), the check on solver-optimal instances becomes
`abs(exact - objective) <= 1e-6`, replacing equality after rounding. A large numerical discrepancy now fails
the run instead of being rounded away. Nothing has run, and no instance, arm, budget, prediction or
interpretation rule changes.

Reporting will follow the same note:
- all 6 instances per size stay in witness summaries, with a missing witness marked incomplete;
- the 4-of-6 solver-optimal rule stays an additional gate;
- dictionary hashes are JSON-content hashes; the written files add a trailing newline.

`contract.json`'s hash for `mip-audit-v2/audit.py` changes from `0c0d46f7a7feb73c0cdf1253b25415827535fda605ff0faaa74a71ab94847dd6` to `1d418780137c1302b60250a3e550b8c1540b60784f742defe504d6cfdde7e19b`.
