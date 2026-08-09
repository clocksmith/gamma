# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-09T15:20:22+00:00`

## Target State

- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Scope bytes: `1,998,848`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `4,022`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `5,691,344`
- Latest sampled single RSS KiB: `5,691,344`
- Tightest binary single-process margin KiB: `4,794,416`
- Tightest decimal single-process margin KiB: `4,074,281`
- Latest binary single-process margin KiB: `4,794,416`
- Latest decimal single-process margin KiB: `4,074,281`
- Safe to launch candidate gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `27`
- Held pending adaptive jobs: `27`
- Claimable pending adaptive jobs: `0`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves the 10.5000000% full-corpus target.`

## Active Gate

- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Scope bytes: `1,998,848`
- Driver result JSON: `projects/enwiki9/results/nncp_libnc_trainlen32_mature_1998848_qm2_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `/home/x/deco/gamma/projects/enwiki9/results/nncp_libnc_trainlen32_mature_1998848_qm2_guard_v1.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, or matching live worker PID and command.`
- RSS guard status: `running`
- RSS guard JSON bytes: `990`
- RSS guard JSON modified UTC: `2026-08-09T15:20:18+00:00`
- RSS guard JSON SHA-256: `8b2d1407ba6b536a4e878fa44dc0701a475e23e8a2c81a53234b10cb9bf64495`
- RSS samples: `4,022`
- Max sampled single RSS KiB: `5,691,344`
- Max sampled tree RSS KiB: `5,711,868`
- Single-process RSS margin KiB: `4,794,416`
- Single-process decimal `10GB` margin KiB: `4,074,281`
- Tree RSS margin KiB: `4,773,892`
- Tree decimal `10GB` margin KiB: `4,053,757`
- Latest sampled single RSS KiB: `5,691,344`
- Latest sampled tree RSS KiB: `5,711,868`
- Latest sampled single-process margin KiB: `4,794,416`
- Latest sampled single-process decimal `10GB` margin KiB: `4,074,281`
- Latest sampled tree margin KiB: `4,773,892`
- Latest sampled tree decimal `10GB` margin KiB: `4,053,757`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Expected scope bytes: `1,998,848`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Expected active scope bytes: `1,998,848`
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
- Program directories: `728`
- Registered programs: `291`
- Untracked nonignored entries: `0`
- Modified tracked entries: `1`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=39, measured_negative=100, retired=538`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 510,791 | 2,229,505 | 21,656 | `python3 projects/enwiki9/tools/enwiki9_lab.py run --candidate nncp_libnc_trainlen32_mature_1998848_qm2_v1 --max-workers 1 --min-free-mib 12000` |
| `rss_guard` | 510,888 | 510,791 | 16,848 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 510,895 | 510,888 | 20,524 | `python3 tools/nncp_libnc_trainlen32_mature_1998848_qm2.py` |
| `process` | 510,946 | 510,895 | 5,691,344 | `/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp -q -T 4 --profile enwik9 --encode_only --n_symb 16392 --dict /home/x/enwiki9-nonproof/result...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/nncp_libnc_trainlen32_mature_1998848_qm2_v1/candidate_encode_only.nncp` | 1,097,728 | `2026-08-09T13:27:31+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `5,750,372`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `4,735,388`
- Active process tree decimal margin KiB: `4,015,253`

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
