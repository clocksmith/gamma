# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-13T21:08:15+00:00`

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
- Active cmix mode: `text_compress`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `72,982`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `8,896,924`
- Latest sampled single RSS KiB: `8,896,924`
- Tightest binary single-process margin KiB: `1,588,836`
- Tightest decimal single-process margin KiB: `868,701`
- Latest binary single-process margin KiB: `1,588,836`
- Latest decimal single-process margin KiB: `868,701`
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
- RSS guard JSON bytes: `1,130`
- RSS guard JSON modified UTC: `2026-07-13T21:08:15+00:00`
- RSS guard JSON SHA-256: `e45e2d79754c27d443057545969930df55606c42fd890ee374b3a6444a6f9b2b`
- RSS samples: `72,982`
- Max sampled single RSS KiB: `8,896,924`
- Max sampled tree RSS KiB: `9,017,552`
- Single-process RSS margin KiB: `1,588,836`
- Single-process decimal `10GB` margin KiB: `868,701`
- Tree RSS margin KiB: `1,468,208`
- Tree decimal `10GB` margin KiB: `748,073`
- Latest sampled single RSS KiB: `8,896,924`
- Latest sampled tree RSS KiB: `9,017,552`
- Latest sampled single-process margin KiB: `1,588,836`
- Latest sampled single-process decimal `10GB` margin KiB: `868,701`
- Latest sampled tree margin KiB: `1,468,208`
- Latest sampled tree decimal `10GB` margin KiB: `748,073`

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

- Audit return code: `1`
- Audit error: `Traceback (most recent call last):
  File "/home/x/deco/gamma/projects/enwiki9/tools/candidate_audit.py", line 614, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/x/deco/gamma/projects/enwiki9/tools/candidate_audit.py", line 598, in main
    inventory = audit()
  File "/home/x/deco/gamma/projects/enwiki9/tools/candidate_audit.py", line 372, in audit
    program_size = driver_program_size(program_dir)
  File "/home/x/deco/gamma/projects/enwiki9/tools/candidate_audit.py", line 126, in driver_program_size
    size += child.stat().st_size
            ~~~~~~~~~~^^
  File "/usr/lib/python3.14/pathlib/__init__.py", line 655, in stat
    return os.stat(self, follow_symlinks=follow_symlinks)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: '/home/x/deco/gamma/projects/enwiki9/programs/enwiki9_zip_model_control_v1/model.enwik9.zip'`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `lock_wrapper` | 3,688,674 | 2,787,113 | 2,064 | `flock -n /tmp/enwiki9-heavy.lock python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --s...` |
| `rss_guard` | 3,688,676 | 3,688,674 | 16,868 | `python3 projects/enwiki9/tools/run_with_rss_guard.py --limit-kib 10485760 --official-decimal-limit-kib 9765625 --sample-interval 1 --guard-json pro...` |
| `driver` | 3,688,683 | 3,688,676 | 120,628 | `python3 projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1 --limit 100000000 --che...` |
| `native_cmix` | 3,688,798 | 3,688,683 | 8,896,924 | `/tmp/cmix21-mmap-bin-55x0e2g1 -t /tmp/cmix21-mmap-dict-kiumjrbu /tmp/tmpfd24qtbz/in /tmp/tmpfd24qtbz/out` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_100000000_determinism_rss_guard.json` | 1,130 | `2026-07-13T21:08:15+00:00` |

## Active RSS

- Max cmix PID: `3688798`
- Active cmix mode: `text_compress`
- Max cmix RSS KiB: `8,896,924`
- Active process tree RSS KiB: `9,036,484`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `1,588,836`
- Single-process decimal margin KiB: `868,701`
- Active process tree margin KiB (binary): `1,449,276`
- Active process tree decimal margin KiB: `729,141`
- Temp input path: `/tmp/tmpfd24qtbz/in`
- Temp output path: `/tmp/tmpfd24qtbz/out`
- Temp output staging path: `/tmp/tmpfd24qtbz/out.cmix.temp`
- Temp input bytes: `100,000,000`
- Temp output bytes: `11,591,680`
- Temp output staging bytes: `60,830,193`
- Temp input modified UTC: `2026-07-13T00:50:32+00:00`
- Temp output modified UTC: `2026-07-13T21:07:42+00:00`
- Temp output staging modified UTC: `2026-07-13T00:50:34+00:00`
- Process read bytes: `0`
- Process write bytes: `0`

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
