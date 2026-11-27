# Three-player Imperial–Coalition faction isolation

**Date:** 2026-08-01  
**Evidence label:** Simulation  
**Status:** Valid diagnostic; rejects a broad Imperial-over-Coalition conclusion
for this registered variable-Mandate field.

## Execution

- Registered protocol:
  `p3-imperial-coalition-isolation-v1`, committed before results.
- Exact source: `d19e947c45eba392591aaaaac48350c4850b7b38`,
  `sourceDirty: false`.
- Canonical ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Root seed: `frontier-2038-p3-imperial-coalition-isolation-2026-08-01`.
- Six common-seed comparisons, 100 games per arm, 1,200 deterministic games
  total. Each pair changes only the focal seat between Imperial Research Lab
  and Coalition Lab.
- Homogeneous weighted and homogeneous greedy fields each cover focal seats
  zero, one, and two. Variable Mandate, negotiation, and all other game input
  were held fixed within a pair.
- Seven worker threads; stable comparison/arm/match ordering; zero quarantined
  pairs; no LLM provider or fallback path.
- Raw report:
  `evidence/studies/simulation/20260801T160420719Z-balance-audit-0-8-27-fc8bd0450b92-frontier-2038-p3-imperial-coalition-isolation-2026-08-01-1200x3-faction-swap-cli.json`.
  SHA-256:
  `ce40a8708ff57a6b5054b812edc4e4126f77425a2da50493483a98dc9c1329e5`.

## Paired result

Positive values favour Imperial Research. The left-minus-right win-credit
deltas were −4.5, +11, and −7 points under weighted policies, and −18,
−5.5, and −0.5 points under greedy policies. The direction changes by focal
seat and policy. The largest positive weighted-seat-one result does not persist
at either other seat; the largest magnitude result instead favours Coalition
under greedy seat zero.

This rejects the narrow hypothesis that the baseline's three-player faction
range is a policy- and seat-independent Imperial Research main effect. It does
not establish that the three-player configuration is balanced: it narrows the
cause to interaction among roster, focal seat, opponent field, and deterministic
policy.

## Consequence

Do not alter either faction from this evidence. A fixed-Mandate replication is
not triggered because the registered fields did not show a coherent direction.
The unresolved production-relevant gap is distinct: the clean canonical matrix
produced no legal AGI declaration windows. The next deterministic study must
use an explicitly declaration-seeking policy/scenario and measure every AGI
funnel stage before any conclusion about the AGI route or balance is made.

## Affected surfaces

- Canonical rulebook: no change.
- Semantic content, generated data, simulator, browser, player aids, and tests:
  no change.
- This receipt records simulated evidence only; no human-play claim is made.
