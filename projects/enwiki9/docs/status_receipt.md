# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-09-05T19:59:51+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-99m-v2`
- Objective digest: `sha256:16badfa6c1a53b47bcc12b089fdd9c21f7405ea56a84344d60c28d2252da8288`
- Objective path: `contracts/research/v2/objective-contract.json`
- Active `9.9000000%` target score: `99,000,000`
- Full-corpus constructive result present: `false`
- Active objective constructive upper bound present: `false`
- Source certificate target (legacy field names): `99,000,000`; certificate upper bound present: `false`

## Operator Summary

- Candidate: `endpoint428_horizon_retained_parent_trace_q0_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `647,798,592`
- Scope unit: `Endpoint428 WRT bit at a frozen A-active byte`
- Gate verdict: `running`
- Gate next action: `wait_for_existing_observer`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Active scorer observed: `false`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `n/a`
- RSS samples: `10,842`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `n/a`
- Latest sampled single RSS KiB: `n/a`
- Tightest binary single-process margin KiB: `n/a`
- Tightest decimal single-process margin KiB: `n/a`
- Latest binary single-process margin KiB: `n/a`
- Latest decimal single-process margin KiB: `n/a`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `26`
- Held pending adaptive jobs: `26`
- Claimable pending adaptive jobs: `0`
- Canonical release bundles: `1`
- Validated release run receipts: `0`
- Validated failed release attempts: `0`
- Objective-achieved receipts: `0`
- Release index mode: `structure-only-router`
- Command source: `none while gate is non-terminal`
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Active Gate

- Gate verdict: `running`
- Next action: `wait_for_existing_observer`
- Candidate: `endpoint428_horizon_retained_parent_trace_q0_v1`
- Scope bytes: `1,000,000,000`
- Scope symbols: `647,798,592`
- Scope unit: `Endpoint428 WRT bit at a frozen A-active byte`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Coordinator PID: `n/a`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `not present`
- RSS guard present: `false`
- Active scorer observed: `false`
- Existing observer job: `20260904T134731Z_441f96254f`
- Observer worker verified on this host: `true`
- Adopted source identities verified on this host: `true`
- Observer progress UTC: `2026-09-05T19:59:45+00:00`
- Observer progress fresh: `true`
- Trace bytes: `8,410,693,632` / `10,364,777,488`
- Archive bytes: `95,649,792`
- Observer samples: `10,842`
- Maximum observed tree RSS bytes: `9,320,497,152`
- Continuous resource proof: `false`
- Science accessed before terminal: `false`
- Observer state: `observing`
- Progress source: `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_orphan_adoption_q0_v1/progress.json`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, matching live worker, or frozen adopted process identities.`

## Gate Evidence Status

- Claim status: `observer_progress_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
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
- Action: `wait_for_existing_observer`
- Reason: `The frozen HORIZON source identities remain live and its sole observer owns terminal routing.`
- Allowed work: `independent work with its own frozen contract and resource authorization`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Gate mutation allowed: `false`
- Recommended action: `wait_for_existing_observer`
- Command source: `none while gate is non-terminal`
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `960`
- Registered programs: `499`
- Untracked nonignored entries: `38`
- Modified tracked entries: `5`
- Candidate statuses: `active=18, blocked_dependency=41, candidate=235, measured_negative=100, retired=565, track_source_before_evolution=1`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| n/a | n/a | n/a | n/a | n/a |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.p1` | 8,412,135,424 | `2026-09-05T20:01:14+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.archive` | 95,674,368 | `2026-09-05T20:01:11+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent-trace.log` | 332,249 | `2026-09-05T20:01:10+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent-trace-guard.json` | 7,057 | `2026-09-04T12:55:53+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/parent.archive.cmix.temp` | 647,798,592 | `2026-08-30T23:00:19+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/.cmix9-PzZd3n/english.dic` | 411,996 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/.cmix9-PzZd3n/cmix` | 1,625,944 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-b.log` | 4,803 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-b-guard.json` | 4,348 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-b.bin` | 30,309,597 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/scan-b.json` | 4,286 | `2026-08-30T23:00:07+00:00` |
| `projects/enwiki9/results/endpoint428_horizon_retained_parent_trace_q0_v1/manifest-a.log` | 4,803 | `2026-08-30T22:56:04+00:00` |

## Contingencies

- If current gate passes: `record pass and inspect the frozen candidate promotion rule`
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

No prefix row proves the `9.9000000%` full-corpus target.
