# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-08-02T18:04:47+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.8000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1`
- Scope bytes: `2,233,775`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Heavy lock held: `true`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `30,722`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `7,790,872`
- Latest sampled single RSS KiB: `7,790,872`
- Tightest binary single-process margin KiB: `2,694,888`
- Tightest decimal single-process margin KiB: `1,974,753`
- Latest binary single-process margin KiB: `2,694,888`
- Latest decimal single-process margin KiB: `1,974,753`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Pending adaptive jobs: `28`
- Held pending adaptive jobs: `28`
- Claimable pending adaptive jobs: `0`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves the 10.8000000% full-corpus target.`

## Active Gate

- Heavy lock held: `true`
- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1`
- Scope bytes: `2,233,775`
- Driver result JSON: `/home/x/deco/gamma/projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/receipt.json`
- Driver result present: `false`
- RSS guard JSON: `/home/x/deco/gamma/projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/teacher_guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive worker PID and command. The host-local heavy lock alone never identifies a gate.`
- RSS guard status: `running`
- RSS guard JSON bytes: `1,336`
- RSS guard JSON modified UTC: `2026-08-02T18:04:47+00:00`
- RSS guard JSON SHA-256: `58a43e03af7f70725adbc537708e451ae22c8484c6f666dbf3e029834730e62e`
- RSS samples: `30,722`
- Max sampled single RSS KiB: `7,790,872`
- Max sampled tree RSS KiB: `7,790,872`
- Single-process RSS margin KiB: `2,694,888`
- Single-process decimal `10GB` margin KiB: `1,974,753`
- Tree RSS margin KiB: `2,694,888`
- Tree decimal `10GB` margin KiB: `1,974,753`
- Latest sampled single RSS KiB: `7,790,872`
- Latest sampled tree RSS KiB: `7,790,872`
- Latest sampled single-process margin KiB: `2,694,888`
- Latest sampled single-process decimal `10GB` margin KiB: `1,974,753`
- Latest sampled tree margin KiB: `2,694,888`
- Latest sampled tree decimal `10GB` margin KiB: `1,974,753`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1`
- Expected scope bytes: `2,233,775`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1`
- Expected active scope bytes: `2,233,775`
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
- Claim rule: `No prefix row proves the 10.8000000% full-corpus target.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `659`
- Registered programs: `266`
- Untracked nonignored entries: `1`
- Modified tracked entries: `50`
- Candidate statuses: `active=18, blocked_dependency=32, candidate=28, measured_negative=99, retired=482`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 2,870,168 | 1,342,133 | 23,972 | `python3 tools/enwiki9_lab.py run --adaptive --max-workers 1 --candidate nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1` |
| `lock_wrapper` | 2,870,184 | 2,870,168 | 2,104 | `flock /tmp/enwiki9-heavy.lock /usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/nncp_v33_libnc_cpu_encode_only_closed_block_q1.py` |
| `process` | 2,870,186 | 2,870,184 | 52,652 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/nncp_v33_libnc_cpu_encode_only_closed_block_q1.py` |
| `rss_guard` | 2,908,762 | 2,870,186 | 16,868 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode tree --official-decimal-limit-kib...` |
| `process` | 2,908,765 | 2,908,762 | 7,790,872 | `/tmp/nncp-closed-block-q1-hcx6copw/nncp-2024-06-05/nncp -q -T 4 --profile enwik9 --encode_only --n_symb 16392 --dict /home/x/enwiki9-nonproof/resul...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/teacher_guard.json` | 1,336 | `2026-08-02T18:04:47+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/teacher_native_trace.bin` | 112,934,912 | `2026-08-02T16:47:22+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/teacher_complete_block.nncp` | 1,163,264 | `2026-08-02T16:46:24+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_native_trace.bin` | 1,130,064 | `2026-08-02T13:47:58+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_patched_on.stdout` | 112 | `2026-08-02T13:47:58+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_patched_on.nncp` | 68,176 | `2026-08-02T13:47:58+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_patched_on.stderr` | 0 | `2026-08-02T13:46:54+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_patched_off.nncp` | 68,176 | `2026-08-02T13:46:54+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_patched_off.stdout` | 112 | `2026-08-02T13:46:54+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_patched_off.stderr` | 0 | `2026-08-02T13:45:50+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_original.nncp` | 68,176 | `2026-08-02T13:45:49+00:00` |
| `projects/enwiki9/results/nncp_v33_libnc_cpu_encode_only_closed_block_q1_v1/smoke_original.stdout` | 112 | `2026-08-02T13:45:49+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `7,886,468`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `2,599,292`
- Active process tree decimal margin KiB: `1,879,157`

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `n/a`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `missing`; status `missing`; score `n/a`
- best_exact_10m_archive: `missing`; status `missing`; score `n/a`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `10.8000000%` full-corpus target.
