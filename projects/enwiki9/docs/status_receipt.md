# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-28T18:06:54+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `1,000,000,000`
- Gate verdict: `cancelled_no_result`
- Gate next action: `inspect_queue_before_launch`
- Heavy lock held: `false`
- Active scorer observed: `false`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `aborted_operator_cancelled`
- RSS samples: `53,691`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,243,192`
- Latest sampled single RSS KiB: `8,243,192`
- Tightest binary single-process margin KiB: `2,242,568`
- Tightest decimal single-process margin KiB: `1,522,433`
- Latest binary single-process margin KiB: `2,242,568`
- Latest decimal single-process margin KiB: `1,522,433`
- Safe to launch heavy gate: `true`
- Terminal verdict present: `true`
- Command source: `terminal operator cancellation; inspect queue before selecting new work`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `false`
- Gate verdict: `cancelled_no_result`
- Next action: `inspect_queue_before_launch`
- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `1,000,000,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_1000000000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `false`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
- RSS guard status: `aborted_operator_cancelled`
- RSS guard JSON bytes: `1,366`
- RSS guard JSON modified UTC: `2026-07-28T00:11:51+00:00`
- RSS guard JSON SHA-256: `5a1ba3a21010eca8ce580e964d2f169207de0cc8fdeb686bc9bc59fa143c8988`
- RSS samples: `53,691`
- Max sampled single RSS KiB: `8,243,192`
- Max sampled tree RSS KiB: `11,215,656`
- Single-process RSS margin KiB: `2,242,568`
- Single-process decimal `10GB` margin KiB: `1,522,433`
- Tree RSS margin KiB: `-729,896`
- Tree decimal `10GB` margin KiB: `-1,450,031`
- Latest sampled single RSS KiB: `8,243,192`
- Latest sampled tree RSS KiB: `11,215,656`
- Latest sampled single-process margin KiB: `2,242,568`
- Latest sampled single-process decimal `10GB` margin KiB: `1,522,433`
- Latest sampled tree margin KiB: `-729,896`
- Latest sampled tree decimal `10GB` margin KiB: `-1,450,031`

## Gate Evidence Status

- Claim status: `cancelled_no_score`
- Driver result terminal: `false`
- RSS guard terminal: `true`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected scope bytes: `1,000,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected active scope bytes: `1,000,000,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `true`
- Action: `inspect_queue_before_launch`
- Reason: `the previous guard was explicitly cancelled without a scored driver result and no longer owns the heavy lane`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `true`
- Heavy gate mutation allowed: `true`
- Recommended action: `inspect_queue_before_launch`
- Command source: `terminal operator cancellation; inspect queue before selecting new work`
- Claim rule: `No prefix row proves 10.95%.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `593`
- Registered programs: `249`
- Untracked nonignored entries: `1`
- Modified tracked entries: `0`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=19, measured_negative=92, retired=429`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| n/a | n/a | n/a | n/a | n/a |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_1000000000_determinism_rss_guard.json` | 1,366 | `2026-07-28T00:11:51+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json` | 1,209 | `2026-07-26T21:27:20+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json` | 1,388 | `2026-07-23T02:21:47+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_10000000_determinism_rss_guard.json` | 874 | `2026-07-20T19:57:07+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` | 1,012 | `2026-07-20T19:57:07+00:00` |

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `n/a`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_10m_archive: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_online_native_10m_v1`; status `exact-10m-counted-projection`; score `109,524,268`

## Claim Rule

No prefix row proves `10.95%`.
