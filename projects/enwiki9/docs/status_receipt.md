# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-21T21:45:03+00:00`

## Target State

- `10.95%` target score: `109,500,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `100,000,000`
- Gate verdict: `running`
- Gate next action: `wait_for_gate_completion`
- Heavy lock held: `false`
- Active scorer observed: `true`
- Active cmix mode: `text_compress`
- Driver result present: `false`
- RSS guard status: `running`
- RSS samples: `1`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `3,916`
- Latest sampled single RSS KiB: `3,916`
- Tightest binary single-process margin KiB: `10,481,844`
- Tightest decimal single-process margin KiB: `9,761,709`
- Latest binary single-process margin KiB: `10,481,844`
- Latest decimal single-process margin KiB: `9,761,709`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `false`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `false`
- Gate verdict: `running`
- Next action: `wait_for_gate_completion`
- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `100,000,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- RSS guard status: `running`
- RSS guard JSON bytes: `923`
- RSS guard JSON modified UTC: `2026-07-21T21:23:10+00:00`
- RSS guard JSON SHA-256: `bc9512b59b2c979a6ba0128b6d257adc6ce15f13592f8415027949a6d6f1f1fe`
- RSS samples: `1`
- Max sampled single RSS KiB: `3,916`
- Max sampled tree RSS KiB: `3,916`
- Single-process RSS margin KiB: `10,481,844`
- Single-process decimal `10GB` margin KiB: `9,761,709`
- Tree RSS margin KiB: `10,481,844`
- Tree decimal `10GB` margin KiB: `9,761,709`
- Latest sampled single RSS KiB: `3,916`
- Latest sampled tree RSS KiB: `3,916`
- Latest sampled single-process margin KiB: `10,481,844`
- Latest sampled single-process decimal `10GB` margin KiB: `9,761,709`
- Latest sampled tree margin KiB: `10,481,844`
- Latest sampled tree decimal `10GB` margin KiB: `9,761,709`

## Gate Evidence Status

- Claim status: `live_guard_monitor_only`
- Driver result terminal: `false`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `true`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected scope bytes: `100,000,000`
- Driver process count: `12`
- Active gate command observed: `true`
- Driver command mismatch count: `11`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| 331,314 | `false` | 1,024 | `false` | `true` |
| 1,582,562 | `false` | 1,000,000 | `false` | `true` |
| 1,626,894 | `false` | 1,000,000 | `false` | `true` |
| 1,783,414 | `false` | 1,000,000 | `false` | `true` |
| 2,999,317 | `false` | 1,000,000 | `false` | `true` |
| 3,264,266 | `true` | 100,000,000 | `true` | `true` |
| 3,403,409 | `false` | 1,000,000 | `false` | `true` |
| 3,419,115 | `false` | 1,000,000 | `false` | `true` |
| 3,472,447 | `false` | 1,000,000 | `false` | `true` |
| 3,472,466 | `false` | 1,000,000 | `false` | `true` |
| 3,475,108 | `false` | 1,000,000 | `false` | `true` |
| 3,475,277 | `false` | 1,000,000 | `false` | `true` |

## Observed Controller Command

- Expected active candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected active scope bytes: `100,000,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `false`
- Action: `wait_for_gate_receipts`
- Reason: `the gate state is incomplete and cannot drive a mutation yet`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `false`
- Heavy gate mutation allowed: `false`
- Recommended action: `wait_for_gate_receipts`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `540`
- Registered programs: `225`
- Untracked nonignored entries: `7`
- Modified tracked entries: `111`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=2, measured_negative=88, retired=397`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `driver` | 331,314 | 1 | 10,280 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1 --limit ...` |
| `process` | 331,479 | 331,314 | 3,366,800 | `/tmp/g331314b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1/d /tmp/g331314d` |
| `driver` | 1,582,562 | 1,582,408 | 12,916 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_topic_sort_dictcmix_xz_v1 --limit 1000000 --check-determinism` |
| `process` | 1,582,617 | 1,582,562 | 3,415,052 | `/tmp/fx2ts1582562b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_topic_sort_dictcmix_xz_v1/english.dic.cmix /tmp/fx2ts1582562d` |
| `driver` | 1,626,894 | 1,626,760 | 13,248 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1 --limit ...` |
| `process` | 1,626,954 | 1,626,894 | 2,322,052 | `/tmp/g1626894b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1/d /tmp/g1626...` |
| `driver` | 1,783,414 | 1,783,080 | 12,908 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_topic_sort_dictcmix_xz_min_v1 --limit 1000000 --check-determinism` |
| `process` | 1,783,481 | 1,783,414 | 2,497,212 | `/tmp/fx2t1783414b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_topic_sort_dictcmix_xz_min_v1/english.dic.cmix /tmp/fx2t1783414d` |
| `driver` | 2,999,317 | 2,999,307 | 13,224 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_titlesuffix_mh2_size_dictcmix_zlibpy_v1 --limit 100...` |
| `process` | 2,999,386 | 2,999,317 | 1,939,016 | `/tmp/g2999317b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_titlesuffix_mh2_size_dictcmix_zlibpy_v1/d /tmp/g2999317d` |
| `driver` | 3,264,266 | 1 | 306,404 | `python3 gamma/projects/enwiki9/lib/driver.py fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1 --limit 100000000 --check-determinism` |
| `process` | 3,294,491 | 3,264,266 | 5,914,600 | `/tmp/g3264266b -c /tmp/g3264266d /tmp/g3264266i /tmp/g3264266o` |
| `driver` | 3,403,409 | 3,403,401 | 18,008 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2cmix_recovered_gcc_o3_xz_minwrap_v1 --limit 1000000 --check-determinism` |
| `driver` | 3,419,115 | 3,419,106 | 14,508 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_core_tune_title_m0p100_m1p95_lstm1p00_sse1000_ctx10000_v1 --limit 1000000 --...` |
| `driver` | 3,472,447 | 3,472,183 | 12,004 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufsixtyfourth_minmaps_v1 --li...` |
| `driver` | 3,472,466 | 3,472,186 | 12,004 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1 --l...` |
| `native_cmix` | 3,472,506 | 3,472,447 | 10,285,768 | `/tmp/cmix21-mmap-bin-grxgqplc -t /tmp/cmix21-mmap-dict-1er0_i_t /tmp/tmppyxuo5o5/in /tmp/tmppyxuo5o5/out` |
| `native_cmix` | 3,472,545 | 3,472,466 | 10,183,504 | `/tmp/cmix21-mmap-bin-_jeq375z -t /tmp/cmix21-mmap-dict-lq2qk7l8 /tmp/tmprjicne3k/in /tmp/tmprjicne3k/out` |
| `process` | 3,474,690 | 3,419,115 | 3,327,988 | `/tmp/g3419115b -c /tmp/g3419115d /tmp/g3419115i /tmp/g3419115o` |
| `driver` | 3,475,108 | 3,474,821 | 18,224 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_title_prefix_suffix_dictcmix_zlibpy_v1 --limit 1000...` |
| `process` | 3,475,208 | 3,475,108 | 1,788,952 | `/tmp/g3475108b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_title_prefix_suffix_dictcmix_zlibpy_v1/d /tmp/g3475108d` |
| `driver` | 3,475,277 | 3,474,963 | 15,784 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_struct_top_dictcmix_xz_min_v1 --limit 1000000 --check-determinism` |
| `process` | 3,475,349 | 3,475,277 | 6,149,756 | `/tmp/fx2m3475277b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_struct_top_dictcmix_xz_min_v1/english.dic.cmix /tmp/fx2m3475277d` |
| `process` | 3,501,927 | 3,403,409 | 5,461,016 | `/tmp/fx2mw3403409/c -c /tmp/fx2mw3403409/d /tmp/tmpi5eed8a8/i /tmp/tmpi5eed8a8/o` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json` | 923 | `2026-07-21T21:23:10+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_10000000_determinism_rss_guard.json` | 874 | `2026-07-20T19:57:07+00:00` |
| `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` | 1,012 | `2026-07-20T19:57:07+00:00` |

## Active RSS

- Max cmix PID: `3472506`
- Active cmix mode: `text_compress`
- Max cmix RSS KiB: `10,285,768`
- Active process tree RSS KiB: `57,111,228`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `199,992`
- Single-process decimal margin KiB: `-520,143`
- Active process tree margin KiB (binary): `-46,625,468`
- Active process tree decimal margin KiB: `-47,345,603`
- Temp input path: `/tmp/tmppyxuo5o5/in`
- Temp output path: `/tmp/tmppyxuo5o5/out`
- Temp output staging path: `/tmp/tmppyxuo5o5/out.cmix.temp`
- Temp input bytes: `1,000,000`
- Temp output bytes: `16,384`
- Temp output staging bytes: `593,350`
- Temp input modified UTC: `2026-07-21T21:41:38+00:00`
- Temp output modified UTC: `2026-07-21T21:44:29+00:00`
- Temp output staging modified UTC: `2026-07-21T21:41:38+00:00`
- Process read bytes: `62,447,616`
- Process write bytes: `0`
- Active process tree warning: `active process tree RSS crossed the local numeric guard; the running kill guard is single-process`

## Contingencies

- If current gate passes: `record pass and apply candidate target-gate promotion rule`
- Pass next scope: `1,000,000,000`
- If RSS fails: `record RSS failure and retire or repackage this integration shape`
- Lower candidate: `unknown`
- Lower PPMD KiB: `n/a`
- If roundtrip or determinism fails: `record failure and do not promote`

## Proof Boundary

- best_exact_10m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_10m_archive: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `metadata-inherited`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_runtime_successor_minified_package_v1`; status `exact-10m-counted-projection`; score `109,389,323`

## Claim Rule

No prefix row proves `10.95%`.
