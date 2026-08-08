# enwiki9 Target Revision - 2026-08-08

## Decision

The canonical full-corpus design target is now:

```text
engineering checkpoint       <= 109,000,000 bytes  (10.9000000%)
prize-competitive checkpoint <= 108,500,000 bytes  (10.8500000%)
canonical design target      <= 105,000,000 bytes  (10.5000000%)
scope_bytes                  == 1,000,000,000
roundtrip_ok                 == true
determinism_ok               == true
runtime_ok                   == true
memory_ok                    == true
```

The checkpoints remain progress diagnostics and are not stopping conditions.
This revision supersedes `docs/target_revision_20260725.md` as active policy.
Historical receipts, frozen proposals, sealed theorem artifacts, and measured
candidate decisions retain the targets under which they were produced.

## Current Frontier Effect

```text
best counted forecast        109,389,323 bytes
canonical design target      105,000,000 bytes
remaining forecast debt        4,389,323 bytes
counted endpoint package         261,125 bytes
maximum archive at target    104,738,875 bytes
```

A child of the current forecast parent must therefore save at least
`4,389,323 + incremental counted bytes + transfer reserve` at full scope.
At the guarded 100M admission gate, with incremental package cost `delta_P`
and a precommitted reserve `R`, require:

```text
10 * g_100 - delta_P >= 4,389,323 + R
```

The unverified `cmix-obias` contingency ceiling of `107,407,896` remains a
record-movement diagnostic. A score of `105,000,000` would clear it by
`2,407,896` bytes, subject to official eligibility and any newer record.

## Claim Boundary

No prefix, forecast, proxy, teacher, oracle, shadow, or infrastructure
certificate proves this target. Victory still requires one self-contained
official full-1G receipt satisfying every score, reconstruction, determinism,
package, CPU, memory, disk, runtime, and dependency rule.
