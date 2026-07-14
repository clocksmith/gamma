# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-14T21:54:38+00:00`

## Target State

- `10.95%` target score: `109,500,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `n/a`
- Gate verdict: `None`
- Gate next action: `None`
- Heavy lock held: `true`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `unknown`
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

- Heavy lock held: `true`
- Gate verdict: `unknown`
- Next action: `unknown`
- Candidate: `unknown`
- Scope bytes: `n/a`
- Driver result JSON: `not present`
- Driver result present: `unknown`
- RSS guard JSON: `not present`
- RSS guard present: `unknown`
- Active scorer observed: `true`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected scope bytes: `n/a`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected active scope bytes: `n/a`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `false`
- Action: `wait_for_current_gate_receipts`
- Reason: `the serialized scorer lane is already owned by an observed guarded process`
- Allowed work: `refresh status receipt; inspect driver and RSS receipts; update documentation and accounting ledgers; work on shadow-coder specs from cached logs`
- Forbidden work: `launch another compression gate; package a fallback candidate; run result-corpus forecast scans; change active candidate source`

## Handoff

- Terminal verdict present: `false`
- Heavy gate mutation allowed: `false`
- Recommended action: `wait_for_current_gate_receipts`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260714T040213Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `532`
- Registered programs: `225`
- Untracked nonignored entries: `0`
- Modified tracked entries: `10`
- Candidate statuses: `active=7, blocked_dependency=12, candidate=144, measured_negative=20, retired=349`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `lock_wrapper` | 3,783,327 | 2,803,071 | 3,848 | `/bin/bash -lc flock /tmp/enwiki9-heavy.lock bash -s <<'SCRIPT' set -euo pipefail cd /home/x/deco/gamma TEST=/home/x/enwiki9-nonproof/results/fx2_cm...` |
| `rss_guard` | 3,868,009 | 3,868,007 | 16,672 | `python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json /ho...` |
| `lock_wrapper` | 3,869,431 | 2,803,071 | 3,908 | `/bin/bash -lc flock /tmp/enwiki9-heavy.lock bash -s <<'SCRIPT' set -euo pipefail cd /home/x/deco/gamma SCREEN=/home/x/enwiki9-nonproof/results/fx2_...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| n/a | n/a | n/a |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `24,428`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `10,461,332`
- Active process tree decimal margin KiB: `9,741,197`

## Proof Boundary

- best_exact_10m: `missing`; status `missing`; score `n/a`
- best_exact_10m_archive: `missing`; status `missing`; score `n/a`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `fx2-calibrated-from-exact-100m`; score `110,181,114`

## Claim Rule

No prefix row proves `10.95%`.
