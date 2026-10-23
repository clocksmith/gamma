# Amendment 1, 2026-10-23: cores, failure receipts, selection quantiles (before launch)

Nothing has run. These changes come from codex's review (gamma-team LOG, 21:36Z) and the owner direction of 21:35Z,
which limits the team to cores 0–15.

1. **Cores.** The arms move from 16–25 to seed 11, az_fixed 12, palette_fixed 13, az_joint 14 and palette_joint 15,
   one core each. Launch waits until codex's item 26 frees 12–15 and item 22 releases 8–10.
2. **Failure receipts.** `qualify()` now keeps every failure detail in a separate private `failures` map. Before
   this change, each completion overwrote the earlier failure details.
3. **Reporting.** `evidence.py` adds selection quantiles (total, median, p90, p95, worst, within 32 and 96)
   alongside the action ones, for the M1 gap ledger. The decoder dependency source bytes and the offline encoder
   inventory are reported separately.

No policy, arm, budget, prediction or decision rule changes. The frozen ranking still uses actions.

Hash changes in `contract.json`:

| File | Before | After |
| --- | --- | --- |
| palette.py | `4708323017a497488c456df589e3d7eb233b83ea0f95d0a28238b89fa09e5ac8` | `e10bcc4759b623f61627399f7e10e1e18c15560767d3900afaeb335f910180aa` |
| evidence.py | `1d28aacd343823c84ffe30cc9c03916958f7cd4589c38b64927d9e5794962017` | `8d9683e35e854cda410e97ac604a1759d27fb5fc50cdfb0caf47d5d98fec4713` |

This file is added to the contract.
