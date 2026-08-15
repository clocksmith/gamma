# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-15T20:08:55+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-105m-v1`
- Objective digest: `sha256:ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8`
- Objective path: `contracts/research/v1/objective-contract.json`
- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `delta_midas_named_midpoint_gradient_65536_q3_v1`
- Scope bytes: `n/a`
- Scope symbols: `65,536`
- Scope unit: `production-alphabet transformed symbol`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `9`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `6,204,004`
- Latest sampled single RSS KiB: `6,204,004`
- Tightest binary single-process margin KiB: `4,281,756`
- Tightest decimal single-process margin KiB: `3,561,621`
- Latest binary single-process margin KiB: `4,281,756`
- Latest decimal single-process margin KiB: `3,561,621`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `27`
- Held pending adaptive jobs: `27`
- Claimable pending adaptive jobs: `0`
- Canonical release bundles: `0`
- Validated release run receipts: `0`
- Validated failed release attempts: `0`
- Objective-achieved receipts: `0`
- Release index mode: `structure-only-router`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves the 10.5000000% full-corpus target.`

## Active Gate

- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `delta_midas_named_midpoint_gradient_65536_q3_v1`
- Scope bytes: `n/a`
- Scope symbols: `65,536`
- Scope unit: `production-alphabet transformed symbol`
- Driver result JSON: `projects/enwiki9/results/delta_midas_named_midpoint_gradient_65536_q3_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `/home/x/deco/gamma/projects/enwiki9/results/delta_midas_named_midpoint_gradient_65536_q3_v1/guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, or matching live worker PID and command.`
- RSS guard status: `running`
- RSS guard JSON bytes: `7,088`
- RSS guard JSON modified UTC: `2026-08-15T20:08:54+00:00`
- RSS guard JSON SHA-256: `e25acc14f7e06a197cc2b55760188383b13b242588bf0d6a9e3b8afc326fc87a`
- RSS samples: `9`
- Max sampled single RSS KiB: `6,204,004`
- Max sampled tree RSS KiB: `6,254,324`
- Single-process RSS margin KiB: `4,281,756`
- Single-process decimal `10GB` margin KiB: `3,561,621`
- Tree RSS margin KiB: `4,231,436`
- Tree decimal `10GB` margin KiB: `3,511,301`
- Latest sampled single RSS KiB: `6,204,004`
- Latest sampled tree RSS KiB: `6,254,324`
- Latest sampled single-process margin KiB: `4,281,756`
- Latest sampled single-process decimal `10GB` margin KiB: `3,561,621`
- Latest sampled tree margin KiB: `4,231,436`
- Latest sampled tree decimal `10GB` margin KiB: `3,511,301`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `delta_midas_named_midpoint_gradient_65536_q3_v1`
- Expected scope bytes: `n/a`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `delta_midas_named_midpoint_gradient_65536_q3_v1`
- Expected active scope bytes: `n/a`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch candidate gate: `false`
- Action: `wait_for_gate_receipts`
- Reason: `the gate state is incomplete and cannot drive a mutation yet`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Gate mutation allowed: `false`
- Recommended action: `wait_for_gate_receipts`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves the 10.5000000% full-corpus target.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `782`
- Registered programs: `339`
- Untracked nonignored entries: `1`
- Modified tracked entries: `1`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=86, measured_negative=100, retired=545`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 1,231,546 | 130,532 | 41,120 | `python3 tools/enwiki9_lab.py run --candidate delta_midas_named_midpoint_gradient_65536_q3_v1 --max-workers 1` |
| `rss_guard` | 1,231,690 | 1,231,546 | 31,656 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode tree --official-decimal-limit-kib...` |
| `process` | 1,231,709 | 1,231,690 | 50,320 | `python3 tools/nncp_delta_midas_named_midpoint_gradient_q3.py --experiment operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536...` |
| `process` | 1,232,039 | 1,231,709 | 6,204,004 | `/home/x/deco/gamma/projects/enwiki9/results/delta_midas_named_midpoint_gradient_65536_q3_v1/scratch/source/nncp -q -T 4 --profile enwik9 --n_symb 1...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/delta_midas_named_midpoint_gradient_65536_q3_v1/F_named_gradient_1.stderr` | 17,885 | `2026-08-15T20:08:55+00:00` |
| `projects/enwiki9/results/delta_midas_named_midpoint_gradient_65536_q3_v1/guard.json` | 7,088 | `2026-08-15T20:08:54+00:00` |
| `projects/enwiki9/results/delta_midas_named_midpoint_gradient_65536_q3_v1/F_named_gradient_1.nncp` | 49,152 | `2026-08-15T20:08:15+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `6,327,100`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `4,158,660`
- Active process tree decimal margin KiB: `3,438,525`

## Proof Boundary

- best_exact_10m: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact artifact-backed`; score `1,895,625`
- best_exact_10m_archive: `endpoint428_pair_layer0_runtime_successor_10m_v1`; status `exact artifact-backed`; score `1,914,647`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `10.5000000%` full-corpus target.
