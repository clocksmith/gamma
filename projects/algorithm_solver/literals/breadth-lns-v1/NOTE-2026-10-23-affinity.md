# Dated runtime note, 2026-10-23T21:35Z: mid-run core reassignment

The owner direction of 21:35Z (`parallel-20261023-gamma.md`) limits the team to cores 0–15 and explicitly keeps item
22 running. At 21:35Z the three running arm processes were moved without being stopped or restarted
(`taskset -a -cp`, all threads):

| Arm | Before | After |
| --- | --- | --- |
| unweighted | cores 26–27 | core 8 |
| nonregress | cores 28–29 | core 9 |
| relative | cores 30–31 | core 10 |

Each arm then had one core instead of two for the remaining LNS budget, which ran from launch at about 20:49Z to
about 22:19Z. The change applied to all three arms at the same moment, so they stay matched with each other. Fewer
moves may fit in the remaining time than under the frozen two-core allocation. The results will report move counts
and solver statuses, and will state this change.

No code, input, budget, seed or decision rule changed, and no validation data had been opened.
