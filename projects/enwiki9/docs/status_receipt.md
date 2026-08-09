# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-09T23:51:04+00:00`

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
- RSS samples: `1,300`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,348,732`
- Latest sampled single RSS KiB: `8,348,732`
- Tightest binary single-process margin KiB: `2,137,028`
- Tightest decimal single-process margin KiB: `1,416,893`
- Latest binary single-process margin KiB: `2,137,028`
- Latest decimal single-process margin KiB: `1,416,893`
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
- RSS guard JSON bytes: `970`
- RSS guard JSON modified UTC: `2026-08-09T23:50:59+00:00`
- RSS guard JSON SHA-256: `17536cd422d1afa1812c67677e2dd3e3a2dcaf4bf38e8d50de2e9ac848edd087`
- RSS samples: `1,300`
- Max sampled single RSS KiB: `8,348,732`
- Max sampled tree RSS KiB: `8,368,820`
- Single-process RSS margin KiB: `2,137,028`
- Single-process decimal `10GB` margin KiB: `1,416,893`
- Tree RSS margin KiB: `2,116,940`
- Tree decimal `10GB` margin KiB: `1,396,805`
- Latest sampled single RSS KiB: `8,348,732`
- Latest sampled tree RSS KiB: `8,368,792`
- Latest sampled single-process margin KiB: `2,137,028`
- Latest sampled single-process decimal `10GB` margin KiB: `1,416,893`
- Latest sampled tree margin KiB: `2,116,968`
- Latest sampled tree decimal `10GB` margin KiB: `1,396,833`

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
- Program directories: `747`
- Registered programs: `305`
- Untracked nonignored entries: `1`
- Modified tracked entries: `3`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=53, measured_negative=100, retired=543`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `process` | 523,095 | 2,229,505 | 21,692 | `python3 tools/enwiki9_lab.py run --candidate cmix_obias_full1g_bare_decode_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `rss_guard` | 523,195 | 523,095 | 16,780 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-li...` |
| `process` | 642,027 | 2,229,505 | 21,652 | `python3 tools/enwiki9_lab.py run --candidate nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `rss_guard` | 642,117 | 642,027 | 16,668 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 1,310,602 | 2,229,505 | 21,540 | `python3 tools/enwiki9_lab.py run --candidate cmix_obias_source_full1g_roundtrip_a_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `process` | 1,310,614 | 2,229,505 | 21,660 | `python3 tools/enwiki9_lab.py run --candidate cmix_obias_source_full1g_roundtrip_b_qm0_v1 --max-workers 1 --min-free-mib 50000` |
| `rss_guard` | 1,310,736 | 1,310,602 | 16,816 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `rss_guard` | 1,310,741 | 1,310,614 | 16,700 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 523,198 | 523,195 | 20,060 | `python3 tools/cmix_obias_full1g_bare_decode_qm0.py` |
| `process` | 523,323 | 523,198 | 8,348,732 | `./archive9` |
| `process` | 642,123 | 642,117 | 39,200 | `python3 tools/nncp_libnc_full_dictionary_midsegment32_65536_qm0.py` |
| `process` | 1,310,745 | 1,310,736 | 20,664 | `python3 tools/cmix_obias_source_full1g_roundtrip_a_qm0.py` |
| `process` | 1,310,746 | 1,310,741 | 20,444 | `python3 tools/cmix_obias_source_full1g_roundtrip_b_qm0.py` |
| `process` | 1,310,866 | 1,310,745 | 8,863,504 | `./cmix -e /home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9 out.cmix` |
| `process` | 1,310,867 | 1,310,746 | 8,863,356 | `./cmix -e /home/x/enwiki9-quarantine/mattmahoney-20260711/enwik9 out.cmix` |
| `process` | 1,600,978 | 642,123 | 6,380,124 | `/tmp/nncp-prod-midpoint-bridge-f2h71_nr/parent/nncp -q -T 4 d /home/x/deco/gamma/projects/enwiki9/results/nncp_libnc_full_dictionary_midsegment32_6...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix_obias_full1g_bare_decode_qm0_v1/decode.log` | 377,553 | `2026-08-09T23:51:04+00:00` |
| `projects/enwiki9/results/cmix_obias_full1g_bare_decode_qm0_v1/scratch_state.txt` | 62 | `2026-08-09T22:02:42+00:00` |

## Active RSS

- Max cmix PID: `n/a`
- Active cmix mode: `n/a`
- Max cmix RSS KiB: `n/a`
- Active process tree RSS KiB: `32,709,592`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `n/a`
- Single-process decimal margin KiB: `n/a`
- Active process tree margin KiB (binary): `-22,223,832`
- Active process tree decimal margin KiB: `-22,943,967`
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
