# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-09-16T02:57:53+00:00`

## Target State

- Objective ID: `gamma-enwiki9-hutter-90m-v3`
- Objective digest: `sha256:e91ff20e92c3cac8acb0cbe5c79fc8e8a3b427d7e151245c8eecc52b1c32fa00`
- Objective path: `contracts/research/v3/objective-contract.json`
- Active `9.0000000%` target score: `90,000,000`
- Full-corpus constructive result present: `false`
- Active objective constructive upper bound present: `false`
- Source certificate target (legacy field names): `90,000,000`; certificate upper bound present: `false`

## Operator Summary

- Candidate: `fx2_trim_auxiliary_ppm_v1`
- Scope bytes: `250,000`
- Scope symbols: `250,000`
- Scope unit: `raw byte`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Active scorer observed: `true`
- Active cmix mode: `compress`
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
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `26`
- Held pending adaptive jobs: `26`
- Claimable pending adaptive jobs: `0`
- Canonical release bundles: `4`
- Validated release run receipts: `0`
- Validated failed release attempts: `0`
- Objective-achieved receipts: `0`
- Release index mode: `structure-only-router`
- Command source: `none while gate is non-terminal`
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Active Gate

- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `fx2_trim_auxiliary_ppm_v1`
- Scope bytes: `250,000`
- Scope symbols: `250,000`
- Scope unit: `raw byte`
- Active stage: `n/a`
- Roundtrip arm: `n/a`
- Coordinator PID: `n/a`
- Driver result JSON: `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `not present`
- RSS guard present: `unknown`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, matching live worker, or frozen adopted process identities.`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_trim_auxiliary_ppm_v1`
- Expected scope bytes: `250,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| Role | PID | Candidate Match | Scope Bytes | Scope Match | Command Contract | Determinism Flag | Proof Schedule |
|---|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `fx2_trim_auxiliary_ppm_v1`
- Expected active scope bytes: `250,000`
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
- Claim rule: `Only an exact full-corpus package can prove the active objective.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Audit mode: `inventory_snapshot`
- Inventory generated: `2026-09-16T02:57:32+00:00`
- Snapshot identity is verified; inventory inputs were not rescanned. This is not live occupancy or launch authority.
- Program directories: `1,071`
- Registered programs: `610`
- Untracked nonignored entries: `0`
- Modified tracked entries: `2`
- Candidate statuses: `active=18, blocked_dependency=98, candidate=264, measured_negative=100, retired=591`

## View Refresh

- Profile: `routine`
- Historical reports were not refreshed by this routine/status operation and may be stale. Use enwiki9_normalize_receipts.py --profile full for historical audits.

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 883,577 | 472,530 | 4,040 | `/bin/bash -lc taskset -c 2 python3 tools/enwiki9_lab.py run --candidate fx2_trim_auxiliary_ppm_v1 --max-workers 1 > run_logs/manual/trim_auxiliary_...` |
| `process` | 883,692 | 883,577 | 41,748 | `python3 tools/enwiki9_lab.py run --candidate fx2_trim_auxiliary_ppm_v1 --max-workers 1` |
| `resource_guard` | 883,801 | 883,692 | 37,228 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_resource_guard_v3.py --limit-kib 9765624 --official-decimal-limit-kib 9765624 -...` |
| `process` | 883,820 | 883,801 | 42,008 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/fx2_trim_auxiliary_ppm_v1.py` |
| `process` | 910,400 | 883,820 | 7,844 | `/usr/bin/timeout --signal=TERM --kill-after=2 360 /home/x/deco/gamma/projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/cmix -c /home/x/deco...` |
| `native_cmix` | 910,401 | 910,400 | 4,325,564 | `/home/x/deco/gamma/projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/cmix -c /home/x/deco/gamma/projects/enwiki9/results/fx2_trim_auxiliary...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-dict-encode.stderr` | 209,975 | `2026-09-16T02:57:53+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/progress.log` | 41,906 | `2026-09-16T02:57:53+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/ppm.temp` | 14,680,064,001 | `2026-09-16T02:57:53+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/assets/dict.comp` | 0 | `2026-09-16T02:57:23+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/assets/dict.comp.cmix.temp` | 412,001 | `2026-09-16T02:57:23+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-dict-encode.stdout` | 0 | `2026-09-16T02:57:23+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-main-repeat-cleanup.json` | 103 | `2026-09-16T02:57:23+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-main-repeat.execution.json` | 683 | `2026-09-16T02:57:23+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-main-repeat.stderr` | 742,645 | `2026-09-16T02:57:22+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-main-repeat.stdout` | 114 | `2026-09-16T02:57:22+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/repeat.arc` | 33,429 | `2026-09-16T02:57:22+00:00` |
| `projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/P-main-decode-cleanup.json` | 103 | `2026-09-16T02:56:44+00:00` |

## Active RSS

- Max cmix PID: `910401`
- Active cmix mode: `compress`
- Max cmix RSS KiB: `4,325,564`
- Active process tree RSS KiB: `4,458,432`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `6,160,196`
- Single-process decimal margin KiB: `5,440,061`
- Active process tree margin KiB (binary): `6,027,328`
- Active process tree decimal margin KiB: `5,307,193`
- Temp input path: `/home/x/deco/gamma/projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/dictionary/english.dic`
- Temp output path: `/home/x/deco/gamma/projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/assets/dict.comp`
- Temp output staging path: `/home/x/deco/gamma/projects/enwiki9/results/fx2_trim_auxiliary_ppm_v1/work/P/assets/dict.comp.cmix.temp`
- Temp input bytes: `411,996`
- Temp output bytes: `0`
- Temp output staging bytes: `412,001`
- Temp input modified UTC: `2026-09-16T02:54:59+00:00`
- Temp output modified UTC: `2026-09-16T02:57:23+00:00`
- Temp output staging modified UTC: `2026-09-16T02:57:23+00:00`
- Process read bytes: `0`
- Process write bytes: `3,829,760`

## Contingencies

- If current gate passes: `record pass and inspect the frozen candidate promotion rule`
- Pass next scope: `n/a`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact artifact-backed`; score `1,895,625`
- best_exact_10m_archive: `fx2_trim_scale10m_v1`; status `exact artifact-backed`; score `n/a`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `9.0000000%` full-corpus target.
