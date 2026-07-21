# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-21T16:56:32+00:00`

## Target State

- `10.95%` target score: `109,500,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `100,000,000`
- Gate verdict: `incomplete`
- Gate next action: `wait_for_gate_receipts`
- Heavy lock held: `false`
- Active scorer observed: `true`
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
- Scope bytes: `100,000,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json`
- RSS guard present: `false`
- Active scorer observed: `true`
- Live guard note: `guard JSON is absent while the scorer is observed; keep waiting for final receipts and use process-table RSS meanwhile`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected scope bytes: `100,000,000`
- Driver process count: `1`
- Active gate command observed: `false`
- Driver command mismatch count: `1`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| 331,314 | `false` | 1,024 | `false` | `true` |

## Observed Controller Command

- Expected active candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected active scope bytes: `100,000,000`
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
- Heavy gate mutation allowed: `false`
- Recommended action: `launch_active_gate`
- Command source: `operator_action.next_gate_command`
- Claim rule: `No prefix row proves 10.95%.`
- Next gate command:
```bash
python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json --label cmix21_gate_fxcmrcm20_100000000_determinism -- python3 projects/enwiki9/lib/driver.py fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1 --limit 100000000 --check-determinism
```

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `540`
- Registered programs: `225`
- Untracked nonignored entries: `6`
- Modified tracked entries: `113`
- Candidate statuses: `active=24, blocked_dependency=30, candidate=17, measured_negative=77, retired=392`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `driver` | 331,314 | 1 | 21,808 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1 --limit ...` |
| `process` | 331,479 | 331,314 | 3,370,948 | `/tmp/g331314b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1/d /tmp/g331314d` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_10000000_determinism_rss_guard.json` | 874 | `2026-07-20T19:57:07+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` | 1,012 | `2026-07-20T19:57:07+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `3,392,756`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `7,093,004`
- Active process tree decimal margin KiB: `6,372,869`

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `1,000,000,000`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_10m_archive: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact-10m-counted-projection`; score `109,389,323`

## Claim Rule

No prefix row proves `10.95%`.
