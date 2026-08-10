# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-10T01:31:27+00:00`

## Target State

- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1`
- Scope bytes: `65,536`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `2,388`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `6,380,124`
- Latest sampled single RSS KiB: `6,203,852`
- Tightest binary single-process margin KiB: `4,105,636`
- Tightest decimal single-process margin KiB: `3,385,501`
- Latest binary single-process margin KiB: `4,281,908`
- Latest decimal single-process margin KiB: `3,561,773`
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
- Candidate: `nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1`
- Scope bytes: `65,536`
- Driver result JSON: `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `/home/x/deco/gamma/projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_guard_v1.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, or matching live worker PID and command.`
- RSS guard status: `running`
- RSS guard JSON bytes: `1,004`
- RSS guard JSON modified UTC: `2026-08-10T01:31:24+00:00`
- RSS guard JSON SHA-256: `c5cdd67e368d45f3220bab2c03dd686cb2dcb4d7d9ff6d635afaa7848c9fd762`
- RSS samples: `2,388`
- Max sampled single RSS KiB: `6,380,124`
- Max sampled tree RSS KiB: `6,419,324`
- Single-process RSS margin KiB: `4,105,636`
- Single-process decimal `10GB` margin KiB: `3,385,501`
- Tree RSS margin KiB: `4,066,436`
- Tree decimal `10GB` margin KiB: `3,346,301`
- Latest sampled single RSS KiB: `6,203,852`
- Latest sampled tree RSS KiB: `6,243,160`
- Latest sampled single-process margin KiB: `4,281,908`
- Latest sampled single-process decimal `10GB` margin KiB: `3,561,773`
- Latest sampled tree margin KiB: `4,242,600`
- Latest sampled tree decimal `10GB` margin KiB: `3,522,465`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1`
- Expected scope bytes: `65,536`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1`
- Expected active scope bytes: `65,536`
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
- Program directories: `755`
- Registered programs: `313`
- Untracked nonignored entries: `2`
- Modified tracked entries: `2`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=61, measured_negative=100, retired=543`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 642,027 | 2,229,505 | 21,652 | `python3 tools/enwiki9_lab.py run --candidate nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `rss_guard` | 642,117 | 642,027 | 16,668 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 642,123 | 642,117 | 39,308 | `python3 tools/nncp_libnc_full_dictionary_midsegment32_65536_qm0.py` |
| `process` | 3,016,424 | 642,123 | 6,203,852 | `/tmp/nncp-prod-midpoint-bridge-f2h71_nr/candidate/nncp -q -T 4 --profile enwik9 --n_symb 16392 --dict /home/x/enwiki9-nonproof/results/nncp_full_sy...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/F_trace.bin` | 229,376 | `2026-08-10T01:31:06+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/F_trace.nncp` | 49,152 | `2026-08-10T01:29:37+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/F_clean.nncp` | 143,414 | `2026-08-10T01:29:36+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/P_restored.raw` | 322,978 | `2026-08-10T00:12:36+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/P_trace.bin` | 7,405,677 | `2026-08-09T23:31:15+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/P_trace.nncp` | 148,140 | `2026-08-09T23:31:15+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/P_clean.nncp` | 148,140 | `2026-08-09T22:51:13+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/environment.json` | 65 | `2026-08-09T22:12:22+00:00` |
| `projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1/symbols_65536.be16` | 131,072 | `2026-08-09T22:12:22+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `6,281,480`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `4,204,280`
- Active process tree decimal margin KiB: `3,484,145`

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
