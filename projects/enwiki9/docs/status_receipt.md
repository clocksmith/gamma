# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, resource guards, and process table.

- Generated at UTC: `2026-08-09T02:31:16+00:00`

## Target State

- `10.5000000%` target score: `105,000,000`
- Full-corpus constructive result present: `false`
- `10.5000000%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix_obias_helical_xmlsafe_qm4_baseline_encode`
- Scope bytes: `n/a`
- Gate verdict: `receipt_incomplete`
- Gate next action: `wait_for_gate_receipts`
- Active scorer observed: `true`
- Active cmix mode: `no_preprocess_compress`
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
- Pending adaptive jobs: `27`
- Held pending adaptive jobs: `27`
- Claimable pending adaptive jobs: `0`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves the 10.5000000% full-corpus target.`

## Active Gate

- Gate verdict: `receipt_incomplete`
- Next action: `wait_for_gate_receipts`
- Candidate: `cmix_obias_helical_xmlsafe_qm4_baseline_encode`
- Scope bytes: `n/a`
- Driver result JSON: `receipt.json`
- Driver result present: `false`
- RSS guard JSON: `encode.guard.json`
- RSS guard present: `false`
- Active scorer observed: `true`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `0`
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

- Expected candidate: `cmix_obias_helical_xmlsafe_qm4_baseline_encode`
- Expected scope bytes: `n/a`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `cmix_obias_helical_xmlsafe_qm4_baseline_encode`
- Expected active scope bytes: `n/a`
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
- Program directories: `712`
- Registered programs: `280`
- Untracked nonignored entries: `1`
- Modified tracked entries: `5`
- Candidate statuses: `active=18, blocked_dependency=33, candidate=29, measured_negative=100, retired=532`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `rss_guard` | 1,768,216 | 2,193,714 | 3,928 | `/bin/bash -lc set -euo pipefail CAND=/home/x/enwiki9-nonproof/results/cmix_obias_helical_xmlsafe_prefix_qm4_v1 PKG=/home/x/enwiki9-nonproof/cmix-ob...` |
| `rss_guard` | 1,768,314 | 1,768,216 | 16,836 | `python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --label cmix_obias_helical_xmlsafe_qm4_baseline_encode --limit-kib 10485760...` |
| `process` | 2,427,744 | 2,229,505 | 21,636 | `python3 tools/enwiki9_lab.py run --candidate nncp_libnc_trainlen32_mature_1998848_qm2_v1 --max-workers 1 --min-free-mib 12000` |
| `rss_guard` | 2,427,829 | 2,427,744 | 16,784 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 3,459,502 | 2,229,505 | 21,660 | `python3 tools/enwiki9_lab.py run --candidate nncp_libnc_exact_midsegment32_65536_qm3_v1 --max-workers 1 --min-free-mib 12000` |
| `rss_guard` | 3,459,586 | 3,459,502 | 16,840 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 3,581,156 | 2,229,505 | 21,644 | `python3 tools/enwiki9_lab.py run --candidate nncp_symbiont16_p64_cmix21_qm0_v1 --max-workers 1 --min-free-mib 12000` |
| `rss_guard` | 3,581,248 | 3,581,156 | 16,740 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 9765625 --limit-mode max_single --official-decimal-lim...` |
| `process` | 1,768,319 | 1,768,314 | 8,746,196 | `./cmix -e /home/x/enwiki9-nonproof/results/cmix_obias_helical_xmlsafe_prefix_qm4_v1/original.bin out.cmix` |
| `process` | 2,427,832 | 2,427,829 | 20,440 | `python3 tools/nncp_libnc_trainlen32_mature_1998848_qm2.py` |
| `process` | 2,427,873 | 2,427,832 | 5,691,312 | `/home/x/enwiki9-nonproof/external/nncp-2024-06-05/nncp -q -T 4 --profile enwik9 --encode_only --n_symb 16392 --dict /home/x/enwiki9-nonproof/result...` |
| `process` | 3,459,587 | 3,459,586 | 21,040 | `python3 tools/nncp_libnc_exact_midsegment32_65536_qm3.py` |
| `process` | 3,459,798 | 3,459,587 | 5,778,764 | `/tmp/nncp-exact-midsegment32-65536-ybc819hu/nncp-2024-06-05/nncp -q -T 4 --profile enwik9 --preprocess 16384,512 --max_size 65536 c /home/x/enwiki9...` |
| `process` | 3,581,255 | 3,581,248 | 35,500 | `python3 tools/nncp_symbiont16_p64_cmix21_qm0.py` |
| `process` | 3,581,334 | 3,581,255 | 9,496,500 | `/tmp/symbiont-cmix-bin-orq4hvyw/cmix -n /tmp/symbiont-I16-1-6l3upl5d/in /tmp/symbiont-I16-1-6l3upl5d/out` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| n/a | n/a | n/a |

## Active RSS

- Max cmix PID: `3581334`
- Active cmix mode: `no_preprocess_compress`
- Max cmix RSS KiB: `9,496,500`
- Active process tree RSS KiB: `29,925,820`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `989,260`
- Single-process decimal margin KiB: `269,125`
- Active process tree margin KiB (binary): `-19,440,060`
- Active process tree decimal margin KiB: `-20,160,195`
- Temp input path: `/tmp/symbiont-I16-1-6l3upl5d/in`
- Temp output path: `/tmp/symbiont-I16-1-6l3upl5d/out`
- Temp output staging path: `/tmp/symbiont-I16-1-6l3upl5d/out.cmix.temp`
- Temp input bytes: `2,097,152`
- Temp output bytes: `335,872`
- Temp output staging bytes: `2,097,157`
- Temp input modified UTC: `2026-08-09T02:09:19+00:00`
- Temp output modified UTC: `2026-08-09T02:31:06+00:00`
- Temp output staging modified UTC: `2026-08-09T02:09:19+00:00`
- Process read bytes: `0`
- Process write bytes: `0`
- Active process tree warning: `active process tree RSS crossed the local numeric guard; the running kill guard is single-process`

## Proof Boundary

- best_exact_10m: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact artifact-backed`; score `1,895,625`
- best_exact_10m_archive: `endpoint428_pair_layer0_runtime_successor_10m_v1`; status `exact artifact-backed`; score `1,914,647`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_gate_dot_fuse_output_update_loop_v1`; status `source-bound-canonical-forecast`; score `109,389,323`

## Claim Rule

No prefix row proves the `10.5000000%` full-corpus target.
