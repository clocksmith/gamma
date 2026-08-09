# enwiki9 Target Revision - 2026-08-09

## Decision

The canonical full-corpus research target is now:

```text
canonical research target   <= 108,000,000 bytes  (10.8000000%)
current prize ceiling       <= 109,685,196 bytes
scope_bytes                 == 1,000,000,000
roundtrip_ok                == true
determinism_ok              == true
runtime_ok                  == true
memory_ok                   == true
```

This revision supersedes `docs/target_revision_20260808.md` for new proposals,
promotion economics, operator status, and victory decisions. The prize ceiling
is derived from the currently accepted `110,793,128` record and the one-percent
minimum-improvement rule. It must be rechecked before any claim.

Historical receipts, frozen proposals, measured candidates, and archived
research entries retain their original target fields for provenance.

## Current Frontier Effect

```text
best counted forecast        109,389,323 bytes
canonical research target    108,000,000 bytes
remaining forecast debt        1,389,323 bytes
counted endpoint package         261,125 bytes
maximum archive at target    107,738,875 bytes
cmix-obias reported total    108,492,825 bytes
cmix-obias target debt           492,825 bytes
prize-threshold margin         1,685,196 bytes
```

A child of the forecast parent must save at least `1,389,323 + incremental
counted bytes + transfer reserve` at full scope. At a guarded 100M admission
gate, with incremental package cost `delta_P` and a precommitted reserve `R`,
require:

```text
10 * g_100 - delta_P >= 1,389,323 + R
```

## Claim Boundary

The `108,000,000` target is the research stopping condition, not merely a
checkpoint. A score between `108,000,001` and `109,685,196` may remain eligible
under the current official record, but it does not satisfy this repository's
active target. No prefix, forecast, proxy, teacher, oracle, or shadow proves
either boundary. Victory requires a self-contained official full-1G receipt
satisfying score, reconstruction, determinism, package, CPU, memory, disk,
runtime, dependency, and source requirements.
