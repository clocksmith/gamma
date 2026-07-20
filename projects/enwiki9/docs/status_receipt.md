# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-20T18:31:02+00:00`

## Target State

- `10.95%` target score: `109,500,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1_10m`
- Scope bytes: `10,000,000`
- Gate verdict: `receipt_incomplete`
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
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `false`
- Gate verdict: `receipt_incomplete`
- Next action: `wait_for_gate_receipts`
- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1_10m`
- Scope bytes: `10,000,000`
- Driver result JSON: `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/receipt.json`
- Driver result present: `false`
- RSS guard JSON: `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_10000000_determinism_rss_guard.json`
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

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1_10m`
- Expected scope bytes: `10,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1_10m`
- Expected active scope bytes: `10,000,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `false`
- Action: `wait_for_gate_receipts`
- Reason: `the gate state is incomplete and cannot drive a mutation yet`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Heavy gate mutation allowed: `false`
- Recommended action: `wait_for_gate_receipts`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260715T010811Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `540`
- Registered programs: `225`
- Untracked nonignored entries: `0`
- Modified tracked entries: `4`
- Candidate statuses: `active=7, blocked_dependency=12, candidate=144, measured_negative=20, retired=357`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `lock_wrapper` | 2,872,957 | 964,780 | 19,472 | `/home/x/.codex/tmp/arg0/codex-arg0bVB3hB/codex-linux-sandbox --sandbox-policy-cwd /home/x/deco --command-cwd /home/x/deco --permission-profile {"ty...` |
| `lock_wrapper` | 2,872,975 | 2,872,957 | 2,284 | `bwrap --new-session --die-with-parent --ro-bind / / --dev /dev --bind /tmp /tmp --perms 555 --tmpfs /tmp/.git --remount-ro /tmp/.git --perms 555 --...` |
| `lock_wrapper` | 2,872,976 | 2,872,975 | 1,576 | `bwrap --new-session --die-with-parent --ro-bind / / --dev /dev --bind /tmp /tmp --perms 555 --tmpfs /tmp/.git --remount-ro /tmp/.git --perms 555 --...` |
| `lock_wrapper` | 2,872,977 | 2,872,976 | 2,036 | `flock -n /tmp/enwiki9-heavy.lock python3 tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 ...` |
| `rss_guard` | 2,872,979 | 2,872,977 | 16,624 | `python3 tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json results/fx2_geometry...` |
| `process` | 2,872,986 | 2,872,979 | 51,348 | `python3 lib/driver.py fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1 --limit 10000000` |
| `process` | 2,897,366 | 2,872,986 | 5,951,080 | `/tmp/g5b -c /tmp/g5d /tmp/g5i /tmp/g5o` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| n/a | n/a | n/a |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `6,044,420`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `4,441,340`
- Active process tree decimal margin KiB: `3,721,205`

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `100,000,000`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `missing`; status `missing`; score `n/a`
- best_exact_10m_archive: `missing`; status `missing`; score `n/a`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact-10m-counted-projection`; score `109,389,323`

## Claim Rule

No prefix row proves `10.95%`.
