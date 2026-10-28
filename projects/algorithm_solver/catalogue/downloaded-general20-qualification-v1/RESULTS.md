# First downloaded batch: measured results

All 40 exact supplied `solve` programs passed the independently authored public
domain checks on Jupiter, Linux: Python 3.14.4 and Node v22.22.1. Each language
covered 6,923 distinct cases across 20 problems. Repeated calls increased total
execution to 14,368 calls in 482 isolated interpreter batches. The fleet attempt
completed with exit code zero. No candidate source changes were needed.

The host validator checked full typed results, unchanged arguments and mutable
alias edges. Its references were cross-checked against exhaustive small
enumerations. Official examples, tiny exhaustive cases, seeded random cases and
legal maximum-size inputs were included. Both Jupiter and Mars subsequently
regenerated the expectations and replayed every raw observation. Mars performed
host verification only; this is not evidence of candidate execution on macOS.

The [source-specific receipt](evidence/qualification-receipt.json) binds every
program to the [frozen contract](frozen-contract.json),
[per-program report](evidence/report.json) and
[raw replay manifest](evidence/replay.json).
The [second host replay](evidence/mars-replay.json) matched the first exactly.
The receipt records hash-verified raw archive copies on Jupiter, Mars and
Jupiter's external drive, UUID `69A8-6B92`. Full official statement snapshots
remain in the private run inputs; their URLs and hashes are in the freeze.

The [fleet receipt](evidence/fleet-result.json) observes checkout `dd7dd823`,
which is the executor's working directory identity. The actual tested code came
from a task-specific archive of `a121ceacb15a081afa2030a802f053bcbcd7ca9b`,
with all 51 source/helper hashes checked against the freeze before dispatch.
The checkout identifier must not be reported as the tested candidate snapshot.

Jupiter's [judge preflight](evidence/jupiter-judge-preflight.log) passed 37 checks.
Suby's [preflight](evidence/suby-judge-preflight.log) failed because bubblewrap
could not configure its private loopback interface. That environment failure
was retained; no isolation settings were weakened and no candidate was run there.

These are finite independent-test results for the first downloaded, explicitly
source-exposed cohort. They do not establish formal correctness, official judge
acceptance, held-out generalization, wrapper execution, canonical admission or
retrieval qualification. Historical protected payloads remained sealed. Original
authoring receipts and the registry's unknown statuses are preserved. Later
downloaded batches remain pending independent qualification.
