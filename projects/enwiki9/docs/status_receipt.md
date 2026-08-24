# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-24T14:39:35+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-105m-v1`
- Objective digest: `sha256:ce4c435c0f398caf65a09050c8518d9c5ea63239f9156048ea2aaaf9b8ffa7e8`
- Objective path: `contracts/research/v1/objective-contract.json`
- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix_filebacked_fxcm_full_a_qm8_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `8,000,000,000`
- Scope unit: `canonical raw enwik9 byte`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active stage: `encode`
- Roundtrip arm: `a`
- Active scorer observed: `true`
- Active cmix mode: `encode`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `116,572`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,978,032`
- Latest sampled single RSS KiB: `8,732,932`
- Tightest binary single-process margin KiB: `1,507,728`
- Tightest decimal single-process margin KiB: `787,593`
- Latest binary single-process margin KiB: `1,752,828`
- Latest decimal single-process margin KiB: `1,032,693`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `48`
- Held pending adaptive jobs: `30`
- Claimable pending adaptive jobs: `18`
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
- Candidate: `cmix_filebacked_fxcm_full_a_qm8_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `8,000,000,000`
- Scope unit: `canonical raw enwik9 byte`
- Active stage: `encode`
- Roundtrip arm: `a`
- Coordinator PID: `4,135,830`
- Driver result JSON: `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/full-roundtrip-receipt.json`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Codec progress: `23.96%`
- Reported payload bytes: `31,674,759`
- Progress log: `projects/enwiki9/scratch/cmix_filebacked_fxcm_full_a_qm8_v1/encode/progress.log`
- Progress log modified UTC: `2026-08-24T14:39:35+00:00`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `true`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, or matching live worker PID and command.`
- RSS guard status: `running`
- RSS guard JSON bytes: `57,641`
- RSS guard JSON modified UTC: `2026-08-24T14:39:35+00:00`
- RSS guard JSON SHA-256: `7f5c7a8d15d018a75390bd21797abeb6ec960e887416ef25f669e00bc6e28bbf`
- RSS samples: `116,572`
- Max sampled single RSS KiB: `8,978,032`
- Max sampled tree RSS KiB: `8,998,152`
- Single-process RSS margin KiB: `1,507,728`
- Single-process decimal `10GB` margin KiB: `787,593`
- Tree RSS margin KiB: `1,487,608`
- Tree decimal `10GB` margin KiB: `767,473`
- Latest sampled single RSS KiB: `8,732,932`
- Latest sampled tree RSS KiB: `8,751,572`
- Latest sampled single-process margin KiB: `1,752,828`
- Latest sampled single-process decimal `10GB` margin KiB: `1,032,693`
- Latest sampled tree margin KiB: `1,734,188`
- Latest sampled tree decimal `10GB` margin KiB: `1,014,053`
- Cgroup memory peak bytes: `9,002,086,400`
- Latest cgroup current bytes: `8,999,657,472`
- Cgroup event deltas: `{'high': 337142, 'low': 0, 'max': 0, 'oom': 0, 'oom_group_kill': 0, 'oom_kill': 0, 'sock_throttled': 0}`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix_filebacked_fxcm_full_a_qm8_v1`
- Expected scope bytes: `1,000,000,000`
- Driver process count: `1`
- Active gate command observed: `true`
- Driver command mismatch count: `0`

| Role | PID | Candidate Match | Scope Bytes | Scope Match | Command Contract | Determinism Flag | Proof Schedule |
|---|---:|---|---:|---|---|---|---|
| `q1_full_roundtrip` | 4,135,830 | `true` | 1,000,000,000 | `true` | `true` | `false` | `q1_arm_a_full_roundtrip` |

## Observed Controller Command

- Expected active candidate: `cmix_filebacked_fxcm_full_a_qm8_v1`
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
- Program directories: `907`
- Registered programs: `448`
- Untracked nonignored entries: `0`
- Modified tracked entries: `0`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=193, measured_negative=100, retired=563`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 4,135,580 | 902,673 | 42,348 | `python3 tools/enwiki9_lab.py run --adaptive --max-workers 1 --candidate cmix_filebacked_fxcm_full_a_qm8_v1` |
| `q1_full_roundtrip` | 4,135,830 | 4,135,580 | 33,748 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/cmix_filebacked_fxcm_full_roundtrip.py --arm a --build-receipt /home/x/deco/gamma/projec...` |
| `resource_guard_soft_high` | 4,135,986 | 4,135,830 | 18,796 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_resource_guard_v3_soft_high.py --limit-kib 9765625 --limit-mode tree --official...` |
| `resource_guard` | 4,135,989 | 4,135,986 | 67,360 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_resource_guard_v3.py --limit-kib 9765625 --limit-mode tree --official-decimal-l...` |
| `q1_full_stage` | 4,136,006 | 4,135,989 | 18,640 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/cmix_filebacked_fxcm_full_stage.py --mode encode --corpus /home/x/enwiki9-quarantine/mat...` |
| `native_cmix` | 4,136,098 | 4,136,006 | 8,745,472 | `./cmix -e /home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9 out.cmix` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/guard.json` | 57,641 | `2026-08-24T14:40:49+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/encode.codec.stderr` | 569,435 | `2026-08-24T14:40:44+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/encode.codec.stdout` | 115 | `2026-08-23T21:54:49+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/phase-markers.jsonl` | 41 | `2026-08-23T21:52:04+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/package/head.blob` | 23,002 | `2026-08-23T21:52:03+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/guard.stderr` | 0 | `2026-08-23T21:52:03+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/encode/guard.stdout` | 0 | `2026-08-23T21:52:03+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/package/cmix` | 719,861 | `2026-08-23T21:52:03+00:00` |
| `projects/enwiki9/results/cmix_filebacked_fxcm_full_a_qm8_v1/lease-transitions.json` | 1,564 | `2026-08-23T21:52:03+00:00` |

## Active RSS

- Max cmix PID: `4136098`
- Active cmix mode: `encode`
- Max cmix RSS KiB: `8,745,472`
- Active process tree RSS KiB: `8,926,364`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `1,740,288`
- Single-process decimal margin KiB: `1,020,153`
- Active process tree margin KiB (binary): `1,559,396`
- Active process tree decimal margin KiB: `839,261`
- Temp input path: `/home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9`
- Temp output path: `/home/x/deco/gamma/projects/enwiki9/scratch/cmix_filebacked_fxcm_full_a_qm8_v1/encode/out.cmix`
- Temp output staging path: `/home/x/deco/gamma/projects/enwiki9/scratch/cmix_filebacked_fxcm_full_a_qm8_v1/encode/out.cmix.cmix.temp`
- Temp input bytes: `1,000,000,000`
- Temp output bytes: `0`
- Temp output staging bytes: `587,138,826`
- Temp input modified UTC: `2011-06-01T15:29:40+00:00`
- Temp output modified UTC: `2026-08-23T21:55:26+00:00`
- Temp output staging modified UTC: `2026-08-23T21:55:26+00:00`
- Process read bytes: `522,935,787,520`
- Process write bytes: `33,733,350,932,480`

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
