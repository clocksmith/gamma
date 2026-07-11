# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-11T17:00:00+00:00`

## Target State

- `10.95%` target score: `109,500,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Scope bytes: `10,000,000`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Heavy lock held: `true`
- Active scorer observed: `true`
- Active cmix mode: `text_compress`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `238`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,521,000`
- Latest sampled single RSS KiB: `8,521,000`
- Tightest binary single-process margin KiB: `1,964,760`
- Tightest decimal single-process margin KiB: `1,244,625`
- Latest binary single-process margin KiB: `1,964,760`
- Latest decimal single-process margin KiB: `1,244,625`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `true`
- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Scope bytes: `10,000,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_10000000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- RSS guard status: `running`
- RSS guard JSON bytes: `1,122`
- RSS guard JSON modified UTC: `2026-07-11T17:00:00+00:00`
- RSS guard JSON SHA-256: `432bfdaa9a1dcf4d752754ebae25f18b401c3a14b0dae53a8b934a6294d9e194`
- RSS samples: `238`
- Max sampled single RSS KiB: `8,521,000`
- Max sampled tree RSS KiB: `8,549,804`
- Single-process RSS margin KiB: `1,964,760`
- Single-process decimal `10GB` margin KiB: `1,244,625`
- Tree RSS margin KiB: `1,935,956`
- Tree decimal `10GB` margin KiB: `1,215,821`
- Latest sampled single RSS KiB: `8,521,000`
- Latest sampled tree RSS KiB: `8,549,804`
- Latest sampled single-process margin KiB: `1,964,760`
- Latest sampled single-process decimal `10GB` margin KiB: `1,244,625`
- Latest sampled tree margin KiB: `1,935,956`
- Latest sampled tree decimal `10GB` margin KiB: `1,215,821`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Expected scope bytes: `10,000,000`
- Driver process count: `1`
- Active gate command observed: `true`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| 1,270,634 | `true` | 10,000,000 | `true` | `true` |

## Observed Controller Command

- Expected active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
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
- Program directories: `532`
- Registered programs: `225`
- Untracked nonignored entries: `55`
- Modified tracked entries: `55`
- Candidate statuses: `active=24, blocked_dependency=12, candidate=69, measured_negative=77, retired=340, track_source_before_evolution=10`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `lock_wrapper` | 1,270,629 | 744,787 | 1,792 | `flock -n /tmp/enwiki9-heavy.lock python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --s...` |
| `rss_guard` | 1,270,633 | 1,270,629 | 14,080 | `python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json pro...` |
| `driver` | 1,270,634 | 1,270,633 | 28,804 | `python3 projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1 --limit 10000000 --chec...` |
| `native_cmix` | 1,270,635 | 1,270,634 | 8,522,024 | `/tmp/cmix21-mmap-bin-0evn9jw_ -t /tmp/cmix21-mmap-dict-jt5dpfr7 /tmp/tmp43c82s03/in /tmp/tmp43c82s03/out` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_10000000_determinism_rss_guard.json` | 1,122 | `2026-07-11T17:00:01+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_1000000_determinism_rss_guard.json` | 970 | `2026-07-11T16:55:37+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/2026-07-11T125536.json` | 1,421 | `2026-07-11T16:55:36+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/fxcm2_buffull_250000_determinism_rss_guard.json` | 960 | `2026-07-11T15:41:29+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/2026-07-11T114129.json` | 1,418 | `2026-07-11T15:41:29+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/fxcm2_buffull_1024_determinism_rss_guard.json` | 954 | `2026-07-11T15:18:59+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/2026-07-11T111858.json` | 1,413 | `2026-07-11T15:18:58+00:00` |

## Active RSS

- Max cmix PID: `1270635`
- Active cmix mode: `text_compress`
- Max cmix RSS KiB: `8,522,024`
- Active process tree RSS KiB: `8,566,700`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `1,963,736`
- Single-process decimal margin KiB: `1,243,601`
- Active process tree margin KiB (binary): `1,919,060`
- Active process tree decimal margin KiB: `1,198,925`
- Temp input path: `/tmp/tmp43c82s03/in`
- Temp output path: `/tmp/tmp43c82s03/out`
- Temp output staging path: `/tmp/tmp43c82s03/out.cmix.temp`
- Temp input bytes: `10,000,000`
- Temp output bytes: `16,384`
- Temp output staging bytes: `6,186,040`
- Temp input modified UTC: `2026-07-11T16:56:03+00:00`
- Temp output modified UTC: `2026-07-11T16:59:28+00:00`
- Temp output staging modified UTC: `2026-07-11T16:56:03+00:00`
- Process read bytes: `0`
- Process write bytes: `12,394,496`

## Contingencies

- If current gate passes: `promote unchanged`
- Pass next scope: `100,000,000`
- If RSS fails: `record RSS failure and package lower PPMD cap`
- Lower candidate: `cmix21_text_mmap_paq5_ppmd20224k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Lower PPMD KiB: `20,224`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1`; status `exact artifact-backed`; score `1,882,615`
- best_exact_10m_archive: `cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`; status `exact artifact-backed`; score `2,202,351`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `fx2-calibrated-from-exact-100m`; score `110,181,114`

## Claim Rule

No prefix row proves `10.95%`.
