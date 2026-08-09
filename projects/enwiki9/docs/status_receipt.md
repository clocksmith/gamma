# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-09T22:12:43+00:00`

## Target State

- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix_obias_full1g_bare_decode_qm0_v1`
- Scope bytes: `1,000,000,000`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `121`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,337,948`
- Latest sampled single RSS KiB: `8,337,948`
- Tightest binary single-process margin KiB: `2,147,812`
- Tightest decimal single-process margin KiB: `1,427,677`
- Latest binary single-process margin KiB: `2,147,812`
- Latest decimal single-process margin KiB: `1,427,677`
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
- Candidate: `cmix_obias_full1g_bare_decode_qm0_v1`
- Scope bytes: `1,000,000,000`
- Driver result JSON: `projects/enwiki9/results/cmix_obias_full1g_bare_decode_qm0_v1/decision.json`
- Driver result present: `false`
- RSS guard JSON: `/home/x/deco/gamma/projects/enwiki9/results/cmix_obias_full1g_bare_decode_qm0_guard_v1.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A running receipt or registered adaptive job is live only with an exact driver, owning controller, or matching live worker PID and command.`
- RSS guard status: `running`
- RSS guard JSON bytes: `968`
- RSS guard JSON modified UTC: `2026-08-09T22:12:42+00:00`
- RSS guard JSON SHA-256: `37b4780bcee70e694b5fe54aa55c7f1b5344a533fd7a55e8db58be4e97f7be4c`
- RSS samples: `121`
- Max sampled single RSS KiB: `8,337,948`
- Max sampled tree RSS KiB: `8,358,040`
- Single-process RSS margin KiB: `2,147,812`
- Single-process decimal `10GB` margin KiB: `1,427,677`
- Tree RSS margin KiB: `2,127,720`
- Tree decimal `10GB` margin KiB: `1,407,585`
- Latest sampled single RSS KiB: `8,337,948`
- Latest sampled tree RSS KiB: `8,358,040`
- Latest sampled single-process margin KiB: `2,147,812`
- Latest sampled single-process decimal `10GB` margin KiB: `1,427,677`
- Latest sampled tree margin KiB: `2,127,720`
- Latest sampled tree decimal `10GB` margin KiB: `1,407,585`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix_obias_full1g_bare_decode_qm0_v1`
- Expected scope bytes: `1,000,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `cmix_obias_full1g_bare_decode_qm0_v1`
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
- Program directories: `737`
- Registered programs: `295`
- Untracked nonignored entries: `7`
- Modified tracked entries: `18`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=42, measured_negative=100, retired=543, track_source_before_evolution=1`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 523,095 | 2,229,505 | 21,724 | `python3 tools/enwiki9_lab.py run --candidate cmix_obias_full1g_bare_decode_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `rss_guard` | 523,195 | 523,095 | 16,812 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-li...` |
| `process` | 642,027 | 2,229,505 | 21,684 | `python3 tools/enwiki9_lab.py run --candidate nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `rss_guard` | 642,117 | 642,027 | 16,700 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 523,198 | 523,195 | 20,092 | `python3 tools/cmix_obias_full1g_bare_decode_qm0.py` |
| `process` | 523,323 | 523,198 | 8,337,956 | `./archive9` |
| `process` | 642,123 | 642,117 | 37,892 | `python3 tools/nncp_libnc_full_dictionary_midsegment32_65536_qm0.py` |
| `process` | 642,446 | 642,123 | 5,497,856 | `/tmp/nncp-prod-midpoint-bridge-f2h71_nr/parent/nncp -q -T 4 --profile enwik9 --n_symb 16392 --dict /home/x/enwiki9-nonproof/results/nncp_full_symbo...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix_obias_full1g_bare_decode_qm0_v1/decode.log` | 362,702 | `2026-08-09T22:12:43+00:00` |
| `projects/enwiki9/results/cmix_obias_full1g_bare_decode_qm0_v1/scratch_state.txt` | 62 | `2026-08-09T22:02:42+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `13,970,716`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `-3,484,956`
- Active process tree decimal margin KiB: `-4,205,091`
- Active process tree warning: `active process tree RSS crossed the local numeric guard; the running kill guard is single-process`

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
