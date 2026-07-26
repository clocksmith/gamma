# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-26T19:55:32+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `None`
- Scope bytes: `n/a`
- Gate verdict: `orphaned_running_receipt`
- Gate next action: `reconcile_orphaned_gate_receipt`
- Heavy lock held: `false`
- Active scorer observed: `false`
- Active cmix mode: `n/a`
- Driver result present: `true`
- RSS guard status: `running`
- RSS samples: `1`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `3,916`
- Latest sampled single RSS KiB: `3,916`
- Tightest binary single-process margin KiB: `10,481,844`
- Tightest decimal single-process margin KiB: `9,761,709`
- Latest binary single-process margin KiB: `10,481,844`
- Latest decimal single-process margin KiB: `9,761,709`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Orphaned Gate Reconciliation

- Heavy lock held: `false`
- Gate verdict: `orphaned_running_receipt`
- Next action: `reconcile_orphaned_gate_receipt`
- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `100,000,000`
- Driver result JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json`
- Driver result present: `true`
- RSS guard JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `false`
- Live gate: `false`
- Liveness classification: `orphaned_running_receipt`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
- RSS guard status: `running`
- RSS guard JSON bytes: `923`
- RSS guard JSON modified UTC: `2026-07-21T21:23:10+00:00`
- RSS guard JSON SHA-256: `bc9512b59b2c979a6ba0128b6d257adc6ce15f13592f8415027949a6d6f1f1fe`
- RSS samples: `1`
- Max sampled single RSS KiB: `3,916`
- Max sampled tree RSS KiB: `3,916`
- Single-process RSS margin KiB: `10,481,844`
- Single-process decimal `10GB` margin KiB: `9,761,709`
- Tree RSS margin KiB: `10,481,844`
- Tree decimal `10GB` margin KiB: `9,761,709`
- Latest sampled single RSS KiB: `3,916`
- Latest sampled tree RSS KiB: `3,916`
- Latest sampled single-process margin KiB: `10,481,844`
- Latest sampled single-process decimal `10GB` margin KiB: `9,761,709`
- Latest sampled tree margin KiB: `10,481,844`
- Latest sampled tree decimal `10GB` margin KiB: `9,761,709`

## Gate Evidence Status

- Claim status: `orphaned_running_receipt`
- Driver result terminal: `true`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected scope bytes: `100,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected active scope bytes: `100,000,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `false`
- Action: `reconcile_orphaned_gate_receipt`
- Reason: `persisted running state has no live owner and must be cleared or terminalized before another heavy gate is launched`
- Allowed work: `inspect and repair the orphaned receipt; run non-heavy oracle and shadow experiments; claim and publish independent non-heavy work`
- Forbidden work: `report the orphaned receipt as active; launch another heavy gate`

## Handoff

- Terminal verdict present: `false`
- Heavy gate mutation allowed: `false`
- Recommended action: `reconcile_orphaned_gate_receipt`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `546`
- Registered programs: `229`
- Untracked nonignored entries: `1`
- Modified tracked entries: `3`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=3, measured_negative=92, retired=398`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| n/a | n/a | n/a | n/a | n/a |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| n/a | n/a | n/a |

## Proof Boundary

- best_exact_10m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_10m_archive: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_online_native_10m_v1`; status `exact-10m-counted-projection`; score `109,524,268`

## Claim Rule

No prefix row proves `10.95%`.
