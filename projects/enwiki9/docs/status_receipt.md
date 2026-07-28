# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-28T22:44:02+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `endpoint428_pair_layer0_online_native_trace_10m_v1`
- Scope bytes: `10,000,000`
- Gate verdict: `receipt_incomplete`
- Gate next action: `wait_for_gate_receipts`
- Heavy lock held: `true`
- Active scorer observed: `true`
- Active cmix mode: `text_compress`
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

- Heavy lock held: `true`
- Gate verdict: `receipt_incomplete`
- Next action: `wait_for_gate_receipts`
- Candidate: `endpoint428_pair_layer0_online_native_trace_10m_v1`
- Scope bytes: `10,000,000`
- Driver result JSON: `results/endpoint428_pair_layer0_online_native_trace_10m_v1/receipt.json`
- Driver result present: `false`
- RSS guard JSON: `results/endpoint428_pair_layer0_online_native_trace_10m_v1/encode_guard.json`
- RSS guard present: `false`
- Active scorer observed: `true`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
- Live guard note: `guard JSON is absent while the scorer is observed; keep waiting for final receipts and use process-table RSS meanwhile`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `endpoint428_pair_layer0_online_native_trace_10m_v1`
- Expected scope bytes: `10,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `endpoint428_pair_layer0_online_native_trace_10m_v1`
- Expected active scope bytes: `10,000,000`
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
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `596`
- Registered programs: `252`
- Untracked nonignored entries: `2`
- Modified tracked entries: `4`
- Candidate statuses: `active=22, blocked_dependency=32, candidate=21, measured_negative=92, retired=429`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 3,370,024 | 3,417,245 | 21,196 | `python3 tools/enwiki9_lab.py run --candidate janus_paid_residual_mdl_q0_v1 --max-workers 1 --min-free-mib 12000` |
| `lock_wrapper` | 3,370,097 | 3,370,024 | 2,132 | `flock /tmp/enwiki9-heavy.lock /usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/endpoint428_p1_trace_gate.py --wrapper /home/x/enwiki9-non...` |
| `process` | 3,370,098 | 3,370,097 | 22,180 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/endpoint428_p1_trace_gate.py --wrapper /home/x/enwiki9-nonproof/results/cmix21_lstm200_p...` |
| `rss_guard` | 3,370,136 | 3,370,098 | 16,844 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-li...` |
| `process` | 3,370,149 | 3,370,136 | 3,764 | `/home/x/enwiki9-nonproof/results/cmix21_lstm200_plus_fx2lite428_onlinepairlayer0_source_package_v17/clean-build-b/comp9a-decomp9 c /home/x/enwiki9-...` |
| `process` | 3,370,150 | 3,370,149 | 9,068,244 | `results/endpoint428_pair_layer0_online_native_trace_10m_v1/.cmix9-ru0MXP/cmix -t results/endpoint428_pair_layer0_online_native_trace_10m_v1/.cmix9-...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/native.p1` | 31,047,680 | `2026-07-28T22:44:03+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/encode_stderr.log` | 246,961 | `2026-07-28T22:44:02+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/archive.bin` | 540,672 | `2026-07-28T22:43:58+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/encode_guard.json` | 1,562 | `2026-07-28T22:43:58+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/archive.bin.cmix.temp` | 6,251,852 | `2026-07-28T22:12:31+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/encode_stdout.log` | 0 | `2026-07-28T22:12:31+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/wrt_store.bin` | 6,251,857 | `2026-07-28T22:12:31+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/store_stdout.log` | 45 | `2026-07-28T22:12:31+00:00` |
| `projects/enwiki9/results/endpoint428_pair_layer0_online_native_trace_10m_v1/store_stderr.log` | 17 | `2026-07-28T22:12:31+00:00` |

## Active RSS

- Max cmix PID: `3370150`
- Active cmix mode: `text_compress`
- Max cmix RSS KiB: `9,068,244`
- Active process tree RSS KiB: `9,134,360`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `1,417,516`
- Single-process decimal margin KiB: `697,381`
- Active process tree margin KiB (binary): `1,351,400`
- Active process tree decimal margin KiB: `631,265`
- Temp input path: `/home/x/enwiki9-nonproof/gamma/projects/enwiki9/data/enwik9_10000000.bin`
- Temp output path: `results/endpoint428_pair_layer0_online_native_trace_10m_v1/archive.bin`
- Temp output staging path: `results/endpoint428_pair_layer0_online_native_trace_10m_v1/archive.bin.cmix.temp`
- Temp input bytes: `10,000,000`
- Temp output bytes: `n/a`
- Temp output staging bytes: `n/a`
- Temp input modified UTC: `2026-07-12T13:04:25+00:00`
- Temp output modified UTC: `n/a`
- Temp output staging modified UTC: `n/a`
- Process read bytes: `73,728`
- Process write bytes: `44,589,056`

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `100,000,000`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_10m_archive: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_online_native_10m_v1`; status `exact-10m-counted-projection`; score `109,524,268`

## Claim Rule

No prefix row proves `10.95%`.
