# Validation coverage diagnostics

[Metadata](evidence/coverage.json); [main report](README.md).

Post-run descriptive reporting requested in Claude’s prelaunch review. The frozen search, qualification reuse and verdicts are unchanged.

| Capacity | Arm | Removed characters | Removed characters seen in validation | Exposed programs | Exposed covered / failed |
| ---: | --- | ---: | ---: | ---: | --- |
| 128 | fixed96 | 0 | 0 | 0 | 0 / 0 |
| 128 | optional | 3 | 3 | 9 | 9 / 0 |
| 256 | fixed96 | 0 | 0 | 0 | 0 / 0 |
| 256 | optional | 9 | 7 | 9 | 8 / 1 |

Descriptive exposure counts, not causal attribution. Removed character identities remain private. Covered exposed programs may use learned literals. Nine-program development observations only; frozen verdicts and JavaScript M1-GAP rows are unchanged.

Any cost row with fewer than nine covered validation programs describes only that covered subset. Its actions, quantiles, fraction and package cannot be compared as full-cohort totals. Every missing program remains in the frozen denominator and blocks readiness. No validation repair.

Rebuild after the main reporter using `coverage_report.py --run <private-run>`.
