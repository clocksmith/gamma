# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-31T21:00:00+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-105m-v1`
- Objective digest: `sha256:ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8`
- Objective path: `contracts/research/v1/objective-contract.json`
- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `endpoint428_horizon_retained_parent_trace_q0_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `647,798,592`
- Scope unit: `Endpoint428 WRT bit at a frozen A-active byte`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Active scorer observed: `true`
- Active cmix mode: `text_compress`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `78,994`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `9,098,816`
- Latest sampled single RSS KiB: `9,098,508`
- Tightest binary single-process margin KiB: `1,386,944`
- Tightest decimal single-process margin KiB: `666,809`
- Latest binary single-process margin KiB: `1,387,252`
- Latest decimal single-process margin KiB: `667,117`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `26`
- Held pending adaptive jobs: `26`
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
- Candidate: `endpoint428_horizon_retained_parent_trace_q0_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `647,798,592`
- Scope unit: `Endpoint428 WRT bit at a frozen A-active byte`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Coordinator PID: `n/a`
- Driver result JSON: `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `/home/x/deco/gamma/projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent-trace-guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, or matching live worker PID and command.`
- RSS guard status: `running`
- RSS guard JSON bytes: `7,055`
- RSS guard JSON modified UTC: `2026-08-31T20:59:59+00:00`
- RSS guard JSON SHA-256: `6344da90e037fbbd86bd4c3eea510f41df74e40be29e827db45aba5faef97bca`
- RSS samples: `78,994`
- Max sampled single RSS KiB: `9,098,816`
- Max sampled tree RSS KiB: `9,102,532`
- Single-process RSS margin KiB: `1,386,944`
- Single-process decimal `10GB` margin KiB: `666,809`
- Tree RSS margin KiB: `1,383,228`
- Tree decimal `10GB` margin KiB: `663,093`
- Latest sampled single RSS KiB: `9,098,508`
- Latest sampled tree RSS KiB: `9,102,032`
- Latest sampled single-process margin KiB: `1,387,252`
- Latest sampled single-process decimal `10GB` margin KiB: `667,117`
- Latest sampled tree margin KiB: `1,383,728`
- Latest sampled tree decimal `10GB` margin KiB: `663,593`
- Cgroup memory peak bytes: `n/a`
- Latest cgroup current bytes: `n/a`
- Cgroup event deltas: `n/a`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `endpoint428_horizon_retained_parent_trace_q0_v1`
- Expected scope bytes: `1,000,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| Role | PID | Candidate Match | Scope Bytes | Scope Match | Command Contract | Determinism Flag | Proof Schedule |
|---|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `endpoint428_horizon_retained_parent_trace_q0_v1`
- Expected active scope bytes: `1,000,000,000`
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
- Program directories: `913`
- Registered programs: `454`
- Untracked nonignored entries: `33`
- Modified tracked entries: `29`
- Candidate statuses: `active=18, blocked_dependency=34, candidate=197, measured_negative=100, retired=563, track_source_before_evolution=1`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 2,878,317 | 902,673 | 37,920 | `python3 tools/enwiki9_lab.py run --candidate endpoint428_horizon_retained_parent_trace_q0_v1 --max-workers 1 --min-free-mib 32768` |
| `process` | 2,878,467 | 2,878,317 | 20,792 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/endpoint428_horizon_retained_parent_trace_q0_v1.py` |
| `rss_guard` | 2,965,296 | 2,878,467 | 31,560 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-li...` |
| `process` | 2,965,314 | 2,965,296 | 3,524 | `/home/x/enwiki9-nonproof/results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/clean-build-b/comp9a-decomp9 c /home/x/deco/gam...` |
| `native_cmix` | 2,965,315 | 2,965,314 | 9,098,508 | `/home/x/deco/gamma/projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/.cmix9-PzZd3n/cmix -t /home/x/deco/gamma/projects/enwik...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.p1` | 1,304,465,408 | `2026-08-31T21:01:16+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent-trace-guard.json` | 7,055 | `2026-08-31T21:01:15+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.archive` | 19,161,088 | `2026-08-31T21:01:00+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent-trace.log` | 215,663 | `2026-08-31T21:00:39+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.archive.cmix.temp` | 647,798,592 | `2026-08-30T23:00:19+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/.cmix9-PzZd3n/english.dic` | 411,996 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/.cmix9-PzZd3n/cmix` | 1,625,944 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-b.log` | 4,803 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-b-guard.json` | 4,348 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-b.bin` | 30,309,597 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/scan-b.json` | 4,286 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-a.log` | 4,803 | `2026-08-30T22:56:04+00:00` |

## Active RSS

- Max cmix PID: `2965315`
- Active cmix mode: `text_compress`
- Max cmix RSS KiB: `9,098,508`
- Active process tree RSS KiB: `9,192,304`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `1,387,252`
- Single-process decimal margin KiB: `667,117`
- Active process tree margin KiB (binary): `1,293,456`
- Active process tree decimal margin KiB: `573,321`
- Temp input path: `/home/x/deco/gamma/projects/enwiki9/data/enwik9`
- Temp output path: `/home/x/deco/gamma/projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.archive`
- Temp output staging path: `/home/x/deco/gamma/projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.archive.cmix.temp`
- Temp input bytes: `1,000,000,000`
- Temp output bytes: `19,144,704`
- Temp output staging bytes: `647,798,592`
- Temp input modified UTC: `2011-06-01T15:29:40+00:00`
- Temp output modified UTC: `2026-08-31T20:59:43+00:00`
- Temp output staging modified UTC: `2026-08-30T23:00:19+00:00`
- Process read bytes: `12,541,952`
- Process write bytes: `2,623,397,888`

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `n/a`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact artifact-backed`; score `1,895,625`
- best_exact_10m_archive: `endpoint428_pair_layer0_runtime_successor_10m_v1`; status `exact artifact-backed`; score `1,914,647`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `10.5000000%` full-corpus target.
