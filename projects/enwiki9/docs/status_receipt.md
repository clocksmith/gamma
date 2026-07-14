# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-14T03:10:45+00:00`

## Target State

- `10.95%` target score: `109,500,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Scope bytes: `100,000,000`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Heavy lock held: `true`
- Active scorer observed: `true`
- Active cmix mode: `decode`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `94,713`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,897,320`
- Latest sampled single RSS KiB: `7,546,424`
- Tightest binary single-process margin KiB: `1,588,440`
- Tightest decimal single-process margin KiB: `868,305`
- Latest binary single-process margin KiB: `2,939,336`
- Latest decimal single-process margin KiB: `2,219,201`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `true`
- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Scope bytes: `100,000,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_100000000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- RSS guard status: `running`
- RSS guard JSON bytes: `1,127`
- RSS guard JSON modified UTC: `2026-07-14T03:10:45+00:00`
- RSS guard JSON SHA-256: `07232b2d5f7718de21b0977b3b72c699edb77759775b0bb779c0ef0400faf927`
- RSS samples: `94,713`
- Max sampled single RSS KiB: `8,897,320`
- Max sampled tree RSS KiB: `9,017,948`
- Single-process RSS margin KiB: `1,588,440`
- Single-process decimal `10GB` margin KiB: `868,305`
- Tree RSS margin KiB: `1,467,812`
- Tree decimal `10GB` margin KiB: `747,677`
- Latest sampled single RSS KiB: `7,546,424`
- Latest sampled tree RSS KiB: `7,553,676`
- Latest sampled single-process margin KiB: `2,939,336`
- Latest sampled single-process decimal `10GB` margin KiB: `2,219,201`
- Latest sampled tree margin KiB: `2,932,084`
- Latest sampled tree decimal `10GB` margin KiB: `2,211,949`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Expected scope bytes: `100,000,000`
- Driver process count: `1`
- Active gate command observed: `true`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| 3,688,683 | `true` | 100,000,000 | `true` | `true` |

## Observed Controller Command

- Expected active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Expected active scope bytes: `100,000,000`
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
- Latest delayed status log present: `false`

## Candidate Audit

- Audit return code: `0`
- Program directories: `532`
- Registered programs: `225`
- Untracked nonignored entries: `0`
- Modified tracked entries: `2`
- Candidate statuses: `active=7, blocked_dependency=12, candidate=144, measured_negative=20, retired=349`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `native_cmix` | 3,327,202 | 3,688,683 | 7,546,484 | `/tmp/cmix21-mmap-bin-55x0e2g1 -d /tmp/cmix21-mmap-dict-kiumjrbu /tmp/tmphin8pkox/in /tmp/tmphin8pkox/out` |
| `lock_wrapper` | 3,688,674 | 2,787,113 | 1,944 | `flock -n /tmp/enwiki9-heavy.lock python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --s...` |
| `rss_guard` | 3,688,676 | 3,688,674 | 5,764 | `python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json pro...` |
| `driver` | 3,688,683 | 3,688,676 | 7,252 | `python3 projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1 --limit 100000000 --che...` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_100000000_determinism_rss_guard.json` | 1,127 | `2026-07-14T03:10:45+00:00` |

## Active RSS

- Max cmix PID: `3327202`
- Active cmix mode: `decode`
- Max cmix RSS KiB: `7,546,484`
- Active process tree RSS KiB: `7,561,444`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `2,939,276`
- Single-process decimal margin KiB: `2,219,141`
- Active process tree margin KiB (binary): `2,924,316`
- Active process tree decimal margin KiB: `2,204,181`
- Temp input path: `/tmp/tmphin8pkox/in`
- Temp output path: `/tmp/tmphin8pkox/out`
- Temp output staging path: `/tmp/tmphin8pkox/out.cmix.temp`
- Temp input bytes: `14,864,716`
- Temp output bytes: `n/a`
- Temp output staging bytes: `4,136,960`
- Temp input modified UTC: `2026-07-14T01:40:31+00:00`
- Temp output modified UTC: `n/a`
- Temp output staging modified UTC: `2026-07-14T03:10:37+00:00`
- Process read bytes: `900,284,416`
- Process write bytes: `0`
- Decode scope progress: `4,136,960` / `100,000,000` bytes (`4.137%`)
- Decode remaining scope bytes: `95,863,040`

## Contingencies

- If current gate passes: `promote unchanged`
- Pass next scope: `1,000,000,000`
- If RSS fails: `record RSS failure and package lower PPMD cap`
- Lower candidate: `cmix21_text_mmap_paq5_ppmd20224k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1`
- Lower PPMD KiB: `20,224`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `missing`; status `missing`; score `n/a`
- best_exact_10m_archive: `missing`; status `missing`; score `n/a`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `fx2-calibrated-from-exact-100m`; score `110,181,114`

## Claim Rule

No prefix row proves `10.95%`.
