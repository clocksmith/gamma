# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-27T05:12:00+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Scope bytes: `1,000,000`
- Gate verdict: `roundtrip_fail`
- Gate next action: `record_roundtrip_failure`
- Heavy lock held: `false`
- Active scorer observed: `false`
- Active cmix mode: `n/a`
- Driver result present: `true`
- RSS guard status: `complete`
- RSS samples: `1,587`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `9,614,792`
- Latest sampled single RSS KiB: `0`
- Tightest binary single-process margin KiB: `870,968`
- Tightest decimal single-process margin KiB: `150,833`
- Latest binary single-process margin KiB: `10,485,760`
- Latest decimal single-process margin KiB: `9,765,625`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `true`
- Command source: `cmix21_gate_decider.apply_terminal_command`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `false`
- Gate verdict: `roundtrip_fail`
- Next action: `record_roundtrip_failure`
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Scope bytes: `1,000,000`
- Driver result JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-27T010740.json`
- Driver result present: `true`
- RSS guard JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmidx5_7_17div2_1000000_screen_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `false`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
- RSS guard status: `complete`
- RSS guard JSON bytes: `1,150`
- RSS guard JSON modified UTC: `2026-07-27T05:07:40+00:00`
- RSS guard JSON SHA-256: `d5f9f3f9a274873b2b455227636379b8df38068744d5c0c32b90ec5e21b5897f`
- RSS samples: `1,587`
- Max sampled single RSS KiB: `9,614,792`
- Max sampled tree RSS KiB: `9,635,504`
- Single-process RSS margin KiB: `870,968`
- Single-process decimal `10GB` margin KiB: `150,833`
- Tree RSS margin KiB: `850,256`
- Tree decimal `10GB` margin KiB: `130,121`
- Latest sampled single RSS KiB: `0`
- Latest sampled tree RSS KiB: `0`
- Latest sampled single-process margin KiB: `10,485,760`
- Latest sampled single-process decimal `10GB` margin KiB: `9,765,625`
- Latest sampled tree margin KiB: `10,485,760`
- Latest sampled tree decimal `10GB` margin KiB: `9,765,625`

## Gate Result Diagnostics

- Archive bytes: `174,531`
- Program bytes: `564,273`
- Local score: `738,804`
- Archive b/B: `1.3962480`
- Required full archive bytes for `10.95%`: `107,435,727`
- Linear archive projection score: `175,095,273`
- Diagnostic note: `linear projection is not a proof; use it only to compare slope pressure`

## Terminal Gate Command

```bash
python3 projects/enwiki9/tools/cmix21_gate_decider.py cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1 --scope 1000000 --apply-terminal --normalize
```

## Gate Evidence Status

- Claim status: `scored_gate_result_present`
- Driver result terminal: `true`
- RSS guard terminal: `true`
- Scored gate result present: `true`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Expected scope bytes: `1,000,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Expected active scope bytes: `1,000,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `false`
- Action: `record_failure_and_stop_promotion`
- Reason: `a failed constructive gate cannot be promoted`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `true`
- Heavy gate mutation allowed: `true`
- Recommended action: `record_failure_and_stop_promotion`
- Command source: `cmix21_gate_decider.apply_terminal_command`
- Claim rule: `No prefix row proves 10.95%.`
- Apply terminal command:
```bash
python3 projects/enwiki9/tools/cmix21_gate_decider.py cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1 --scope 1000000 --apply-terminal --normalize
```

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260709T122555Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `552`
- Registered programs: `229`
- Untracked nonignored entries: `91`
- Modified tracked entries: `15`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=5, measured_negative=89, retired=399, track_source_before_evolution=6`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| n/a | n/a | n/a | n/a | n/a |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmidx5_7_17div2_10000000_screen.log` | 0 | `2026-07-27T05:08:11+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmidx5_7_17div2_10000000_screen.pid` | 7 | `2026-07-27T05:08:11+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmidx5_7_17div2_1000000_screen_rss_guard.json` | 1,150 | `2026-07-27T05:07:40+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-27T010740.json` | 1,591 | `2026-07-27T05:07:40+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmidx5_7_17div2_250000_determinism_rss_guard.json` | 1,021 | `2026-07-27T04:40:23+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-27T004022.json` | 1,852 | `2026-07-27T04:40:22+00:00` |

## Contingencies

- If current gate passes: `promote unchanged`
- Pass next scope: `10,000,000`
- If RSS fails: `record RSS failure and package lower PPMD cap`
- Lower candidate: `cmix21_text_mmap_paq5_ppmd20224k_fxcmidx5_7_17div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Lower PPMD KiB: `20,224`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1`; status `exact artifact-backed`; score `1,882,615`
- best_exact_10m_archive: `cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`; status `exact artifact-backed`; score `2,202,351`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `15,462,586`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `fx2-calibrated-from-exact-100m`; score `110,181,114`

## Claim Rule

No prefix row proves `10.95%`.
