# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-27T01:03:06+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `1,000,000,000`
- Gate verdict: `incomplete`
- Gate next action: `wait_for_gate_receipts`
- Heavy lock held: `false`
- Active scorer observed: `false`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `n/a`
- RSS samples: `n/a`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `n/a`
- Latest sampled single RSS KiB: `n/a`
- Tightest binary single-process margin KiB: `n/a`
- Tightest decimal single-process margin KiB: `n/a`
- Latest binary single-process margin KiB: `n/a`
- Latest decimal single-process margin KiB: `n/a`
- Safe to launch heavy gate: `true`
- Terminal verdict present: `false`
- Command source: `operator_action.next_gate_command`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `false`
- Gate verdict: `incomplete`
- Next action: `wait_for_gate_receipts`
- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `1,000,000,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_1000000000_determinism_rss_guard.json`
- RSS guard present: `false`
- Active scorer observed: `false`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
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
- Action: `launch_active_gate`
- Reason: `the active candidate and scope have no guard or driver receipt yet`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Heavy gate mutation allowed: `true`
- Recommended action: `launch_active_gate`
- Command source: `operator_action.next_gate_command`
- Claim rule: `No prefix row proves 10.95%.`
- Next gate command:
```bash
python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_1000000000_determinism_rss_guard.json --label cmix21_gate_fxcmrcm20_1000000000_determinism -- python3 projects/enwiki9/lib/driver.py fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1 --limit 1000000000 --check-determinism
```

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `546`
- Registered programs: `229`
- Untracked nonignored entries: `6`
- Modified tracked entries: `3`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=3, measured_negative=92, retired=398`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| n/a | n/a | n/a | n/a | n/a |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
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
