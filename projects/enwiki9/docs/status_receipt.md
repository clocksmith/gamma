# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-26T12:42:28+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `None`
- Scope bytes: `n/a`
- Gate verdict: `orphaned_running_receipt`
- Gate next action: `reconcile_orphaned_gate_receipt`
- Heavy lock held: `false`
- Active scorer observed: `true`
- Active cmix mode: `decode`
- Driver result present: `true`
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

## Orphaned Gate Reconciliation

- Heavy lock held: `false`
- Gate verdict: `orphaned_running_receipt`
- Next action: `reconcile_orphaned_gate_receipt`
- Candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Scope bytes: `100,000,000`
- Driver result JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json`
- Driver result present: `true`
- RSS guard JSON: `projects/enwiki9/results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/gate_100000000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `true`
- Live gate: `false`
- Liveness classification: `orphaned_running_receipt`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
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

- Claim status: `orphaned_running_receipt`
- Driver result terminal: `true`
- RSS guard terminal: `false`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`
- Expected scope bytes: `100,000,000`
- Driver process count: `9`
- Active gate command observed: `false`
- Driver command mismatch count: `9`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| 331,314 | `false` | 1,024 | `false` | `true` |
| 1,582,562 | `false` | 1,000,000 | `false` | `true` |
| 1,626,894 | `false` | 1,000,000 | `false` | `true` |
| 1,783,414 | `false` | 1,000,000 | `false` | `true` |
| 2,999,317 | `false` | 1,000,000 | `false` | `true` |
| 3,419,115 | `false` | 1,000,000 | `false` | `true` |
| 3,472,447 | `false` | 1,000,000 | `false` | `true` |
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
- Action: `reconcile_orphaned_gate_receipt`
- Reason: `persisted running state has no live owner and must be cleared or terminalized before another heavy gate is launched`
- Allowed work: `inspect and repair the orphaned receipt; run non-heavy oracle and shadow experiments; claim and publish independent non-heavy work`
- Forbidden work: `report the orphaned receipt as active; launch another heavy gate`

## Handoff

- Terminal verdict present: `false`
- Heavy gate mutation allowed: `false`
- Recommended action: `reconcile_orphaned_gate_receipt`
- Command source: `none while gate is non-terminal`
- Claim rule: `No prefix row proves 10.95%.`

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260721T151206Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `544`
- Registered programs: `227`
- Untracked nonignored entries: `0`
- Modified tracked entries: `1`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=3, measured_negative=91, retired=397`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| `driver` | 331,314 | 1 | 10,280 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1 --limit ...` |
| `process` | 331,479 | 331,314 | 3,366,800 | `/tmp/g331314b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1/d /tmp/g331314d` |
| `driver` | 1,582,562 | 1 | 12,916 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_topic_sort_dictcmix_xz_v1 --limit 1000000 --check-determinism` |
| `process` | 1,582,617 | 1,582,562 | 3,415,052 | `/tmp/fx2ts1582562b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_topic_sort_dictcmix_xz_v1/english.dic.cmix /tmp/fx2ts1582562d` |
| `driver` | 1,626,894 | 1 | 13,248 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1 --limit ...` |
| `process` | 1,626,954 | 1,626,894 | 2,322,052 | `/tmp/g1626894b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_mh4_revtitle_title_size_dictcmix_zlibpy_v1/d /tmp/g1626...` |
| `driver` | 1,783,414 | 1 | 12,908 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_topic_sort_dictcmix_xz_min_v1 --limit 1000000 --check-determinism` |
| `process` | 1,783,481 | 1,783,414 | 2,497,212 | `/tmp/fx2t1783414b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_topic_sort_dictcmix_xz_min_v1/english.dic.cmix /tmp/fx2t1783414d` |
| `driver` | 2,999,317 | 1 | 13,224 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_titlesuffix_mh2_size_dictcmix_zlibpy_v1 --limit 100...` |
| `process` | 2,999,386 | 2,999,317 | 1,939,016 | `/tmp/g2999317b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_titlesuffix_mh2_size_dictcmix_zlibpy_v1/d /tmp/g2999317d` |
| `driver` | 3,419,115 | 1 | 14,508 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_core_tune_title_m0p100_m1p95_lstm1p00_sse1000_ctx10000_v1 --limit 1000000 --...` |
| `driver` | 3,472,447 | 1 | 16,452 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufsixtyfourth_minmaps_v1 --li...` |
| `process` | 3,474,690 | 3,419,115 | 3,327,732 | `/tmp/g3419115b -c /tmp/g3419115d /tmp/g3419115i /tmp/g3419115o` |
| `driver` | 3,475,108 | 1 | 18,224 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_gepa_kind_template_topic_title_prefix_suffix_dictcmix_zlibpy_v1 --limit 1000...` |
| `process` | 3,475,208 | 3,475,108 | 1,788,952 | `/tmp/g3475108b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_gepa_kind_template_topic_title_prefix_suffix_dictcmix_zlibpy_v1/d /tmp/g3475108d` |
| `driver` | 3,475,277 | 1 | 15,784 | `/usr/bin/python3 /home/x/deco/gamma/projects/enwiki9/lib/driver.py fx2_struct_top_dictcmix_xz_min_v1 --limit 1000000 --check-determinism` |
| `process` | 3,475,349 | 3,475,277 | 4,181,340 | `/tmp/fx2m3475277b -d /home/x/deco/gamma/projects/enwiki9/programs/fx2_struct_top_dictcmix_xz_min_v1/english.dic.cmix /tmp/fx2m3475277d` |
| `native_cmix` | 3,652,411 | 3,472,447 | 10,707,440 | `/tmp/cmix21-mmap-bin-grxgqplc -d /tmp/cmix21-mmap-dict-1er0_i_t /tmp/tmpgy8sktrw/in /tmp/tmpgy8sktrw/out` |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| n/a | n/a | n/a |

## Active RSS

- Max cmix PID: `3652411`
- Active cmix mode: `decode`
- Max cmix RSS KiB: `10,707,440`
- Active process tree RSS KiB: `33,673,140`
- Local binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Single-process binary margin KiB: `-221,680`
- Single-process decimal margin KiB: `-941,815`
- Active process tree margin KiB (binary): `-23,187,380`
- Active process tree decimal margin KiB: `-23,907,515`
- Temp input path: `/tmp/tmpgy8sktrw/in`
- Temp output path: `/tmp/tmpgy8sktrw/out`
- Temp output staging path: `/tmp/tmpgy8sktrw/out.cmix.temp`
- Temp input bytes: `174,422`
- Temp output bytes: `937,984`
- Temp output staging bytes: `593,350`
- Temp input modified UTC: `2026-07-21T21:58:24+00:00`
- Temp output modified UTC: `2026-07-21T22:12:27+00:00`
- Temp output staging modified UTC: `2026-07-21T22:12:27+00:00`
- Process read bytes: `0`
- Process write bytes: `0`
- Decode scope progress: `593,350` / `100,000,000` bytes (`0.593%`)
- Decode remaining scope bytes: `99,406,650`
- Active process tree warning: `active process tree RSS crossed the local numeric guard; the running kill guard is single-process`

## Proof Boundary

- best_exact_10m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_10m_archive: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `1,825,866`
- best_exact_100m: `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1`; status `exact artifact-backed`; score `15,040,789`
- best_full_1g: `not verified`; status `not verified`; score `n/a`
- best_forecast: `endpoint428_pair_layer0_online_native_10m_v1`; status `exact-10m-counted-projection`; score `109,524,268`

## Claim Rule

No prefix row proves `10.95%`.
