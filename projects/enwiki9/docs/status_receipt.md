# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-27T22:24:06+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Scope bytes: `10,000,000`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Heavy lock held: `true`
- Active scorer observed: `true`
- Active cmix mode: `text_compress`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `8,474`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `9,607,364`
- Latest sampled single RSS KiB: `9,602,756`
- Tightest binary single-process margin KiB: `878,396`
- Tightest decimal single-process margin KiB: `158,261`
- Latest binary single-process margin KiB: `883,004`
- Latest decimal single-process margin KiB: `162,869`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `true`
- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Scope bytes: `10,000,000`
- Driver result JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/receipt.json`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmassoc10_10000000_exact_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `true`
- Liveness classification: `live_observed_owner`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `true`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
- RSS guard status: `running`
- RSS guard JSON bytes: `1,392`
- RSS guard JSON modified UTC: `2026-07-27T22:24:05+00:00`
- RSS guard JSON SHA-256: `68ae809f0fa61f03511621f91276a6e827885a2002f1715a4cfb8a09780c3306`
- RSS samples: `8,474`
- Max sampled single RSS KiB: `9,607,364`
- Max sampled tree RSS KiB: `9,643,656`
- Single-process RSS margin KiB: `878,396`
- Single-process decimal `10GB` margin KiB: `158,261`
- Tree RSS margin KiB: `842,104`
- Tree decimal `10GB` margin KiB: `121,969`
- Latest sampled single RSS KiB: `9,602,756`
- Latest sampled tree RSS KiB: `9,643,656`
- Latest sampled single-process margin KiB: `883,004`
- Latest sampled single-process decimal `10GB` margin KiB: `162,869`
- Latest sampled tree margin KiB: `842,104`
- Latest sampled tree decimal `10GB` margin KiB: `121,969`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Expected scope bytes: `10,000,000`
- Driver process count: `1`
- Active gate command observed: `true`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| 265,690 | `true` | 10,000,000 | `true` | `true` |

## Observed Controller Command

- Expected active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
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
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260709T122555Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `584`
- Registered programs: `242`
- Untracked nonignored entries: `13`
- Modified tracked entries: `4`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=18, measured_negative=89, retired=422, track_source_before_evolution=2`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `lock_wrapper` | 265,685 | 3,250,165 | 1,792 | `flock -n /tmp/enwiki9-heavy.lock python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decim...` |
| `rss_guard` | 265,689 | 265,685 | 14,080 | `python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-limit-kib 9765625 --guard-json...` |
| `driver` | 265,690 | 265,689 | 40,900 | `python3 projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmap...` |
| `lock_wrapper` | 308,375 | 3,250,165 | 1,664 | `flock /tmp/enwiki9-heavy.lock python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --limit-mode max_single --official-decimal-...` |
| `native_cmix` | 332,698 | 265,690 | 9,602,756 | `/tmp/cmix21-mmap-bin-56pc3n75 -t /tmp/cmix21-mmap-dict-zmmck3q4 /tmp/tmpvcizoafb/in /tmp/tmpvcizoafb/out` |
| `lock_wrapper` | 371,486 | 3,250,165 | 3,456 | `/bin/bash -lc mkdir -p projects/enwiki9/results/nncp_branch_frequency_trace_1k_v1 while [ -e projects/enwiki9/operations/adaptive/pending/043_20260...` |
| `process` | 375,975 | 371,486 | 1,792 | `sleep 30` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmassoc10_10000000_exact_rss_guard.json` | 1,392 | `2026-07-27T22:24:05+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmassoc10_1000000_screen_rss_guard.json` | 1,149 | `2026-07-27T10:36:55+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-27T063653.json` | 1,607 | `2026-07-27T10:36:53+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/fxcmassoc10_250000_determinism_rss_guard.json` | 1,150 | `2026-07-27T10:09:49+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-27T060947.json` | 1,918 | `2026-07-27T10:09:47+00:00` |

## Active RSS

- Max cmix PID: `332698`
- Active cmix mode: `text_compress`
- Max cmix RSS KiB: `9,602,756`
- Active process tree RSS KiB: `9,666,440`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `883,004`
- Single-process decimal margin KiB: `162,869`
- Active process tree margin KiB (binary): `819,320`
- Active process tree decimal margin KiB: `99,185`
- Temp input path: `/tmp/tmpvcizoafb/in`
- Temp output path: `/tmp/tmpvcizoafb/out`
- Temp output staging path: `/tmp/tmpvcizoafb/out.cmix.temp`
- Temp input bytes: `10,000,000`
- Temp output bytes: `1,146,880`
- Temp output staging bytes: `6,186,040`
- Temp input modified UTC: `2026-07-27T19:23:27+00:00`
- Temp output modified UTC: `2026-07-27T22:24:03+00:00`
- Temp output staging modified UTC: `2026-07-27T19:23:28+00:00`
- Process read bytes: `2,416,640`
- Process write bytes: `13,524,992`

## Contingencies

- If current gate passes: `promote unchanged`
- Pass next scope: `100,000,000`
- If RSS fails: `record RSS failure and package lower PPMD cap`
- Lower candidate: `cmix21_text_mmap_paq5_ppmd20224k_fxcmassoc10_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
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
