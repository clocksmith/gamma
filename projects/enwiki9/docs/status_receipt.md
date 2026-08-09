# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-09T09:34:35+00:00`

## Target State

- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Scope bytes: `1,998,848`
- Gate verdict: `incomplete`
- Gate next action: `wait_for_gate_receipts`
- Active scorer observed: `true`
- Active cmix mode: `n/a`
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
- Safe to launch candidate gate: `true`
- Terminal verdict present: `false`
- Pending adaptive jobs: `27`
- Held pending adaptive jobs: `27`
- Claimable pending adaptive jobs: `0`
- Command source: `operator_action.next_gate_command`
- Claim rule: `No prefix row proves the 10.5000000% full-corpus target.`

## Active Gate

- Gate verdict: `incomplete`
- Next action: `wait_for_gate_receipts`
- Candidate: `nncp_libnc_trainlen32_mature_1998848_qm2_v1`
- Scope bytes: `1,998,848`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/nncp_libnc_trainlen32_mature_1998848_qm2_v1/gate_1998848_determinism_rss_guard.json`
- RSS guard present: `false`
- Active scorer observed: `true`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `1`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive worker PID and command.`
- Live guard note: `guard JSON is absent while the scorer is observed; keep waiting for final receipts and use process-table RSS meanwhile`

## Gate Evidence Status

- Claim status: `awaiting_gate_receipts`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
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

- Safe to launch candidate gate: `true`
- Action: `launch_active_gate`
- Reason: `the active candidate and scope have no guard or driver receipt yet`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Gate mutation allowed: `true`
- Recommended action: `launch_active_gate`
- Command source: `operator_action.next_gate_command`
- Claim rule: `No prefix row proves the 10.5000000% full-corpus target.`
- Next gate command:
```bash
python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json projects/enwiki9/results/nncp_libnc_trainlen32_mature_1998848_qm2_v1/gate_1998848_determinism_rss_guard.json --label cmix21_gate_fxcmrcm20_1998848_determinism -- python3 projects/enwiki9/lib/driver.py nncp_libnc_trainlen32_mature_1998848_qm2_v1 --limit 1998848 --check-determinism
```

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `717`
- Registered programs: `282`
- Untracked nonignored entries: `1`
- Modified tracked entries: `4`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=31, measured_negative=100, retired=535`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 2,013,691 | 2,193,714 | 21,716 | `python3 projects/enwiki9/tools/enwiki9_lab.py run --candidate cmix_obias_helical_xmlsafe_residual_backend_qm4_v1 --max-workers 1` |
| `rss_guard` | 2,013,778 | 2,013,691 | 16,836 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-li...` |
| `process` | 2,427,744 | 2,229,505 | 10,144 | `python3 tools/enwiki9_lab.py run --candidate nncp_libnc_trainlen32_mature_1998848_qm2_v1 --max-workers 1 --min-free-mib 12000` |
| `rss_guard` | 2,427,829 | 2,427,744 | 10,224 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 2,013,786 | 2,013,778 | 19,120 | `python3 tools/cmix_obias_helical_xmlsafe_residual_backend_qm4.py` |
| `process` | 2,013,815 | 2,013,786 | 9,179,220 | `./cmix -e /home/x/enwiki9-nonproof/results/cmix_obias_helical_xmlsafe_prefix_qm4_v1/residual.bin out.cmix` |
| `process` | 2,427,832 | 2,427,829 | 12,588 | `python3 tools/nncp_libnc_trainlen32_mature_1998848_qm2.py` |
| `process` | 2,427,873 | 2,427,832 | 5,680,176 | `/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp -q -T 4 --profile enwik9 --encode_only --n_symb 16392 --dict /home/x/enwiki9-nonproof/result...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/nncp_libnc_trainlen32_mature_1998848_qm2_v1/candidate_encode_only.nncp` | 1,490,944 | `2026-08-09T09:14:13+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `14,950,024`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `-4,464,264`
- Active process tree decimal margin KiB: `-5,184,399`
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
