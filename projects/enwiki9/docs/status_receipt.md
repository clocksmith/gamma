# enwiki9 Status Receipt

Generated from the current certificate, gate receipts, lock state, and process table.

- Generated at UTC: `2026-07-27T01:38:41+00:00`

## Target State

- `10.8000000%` target score: `108,000,000`
- Full-corpus constructive result present: `false`
- `10.95%` constructive upper bound present: `false`

## Operator Summary

- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Scope bytes: `250,000`
- Gate verdict: `rss_fail`
- Gate next action: `bracket_lower_from_recorded_rss_failure`
- Heavy lock held: `false`
- Active scorer observed: `false`
- Active cmix mode: `n/a`
- Driver result present: `false`
- RSS guard status: `aborted_official_decimal_memory_limit`
- RSS samples: `173`
- Binary `10GiB` guard KiB: `10,485,760`
- Decimal `10GB` guard KiB: `9,765,625`
- Max sampled single RSS KiB: `9,768,612`
- Latest sampled single RSS KiB: `9,768,612`
- Tightest binary single-process margin KiB: `717,148`
- Tightest decimal single-process margin KiB: `-2,987`
- Latest binary single-process margin KiB: `717,148`
- Latest decimal single-process margin KiB: `-2,987`
- Safe to launch heavy gate: `false`
- Terminal verdict present: `true`
- Command source: `cmix21_gate_decider.apply_terminal_command`
- Claim rule: `No prefix row proves 10.95%.`

## Active Gate

- Heavy lock held: `false`
- Gate verdict: `rss_fail`
- Next action: `bracket_lower_from_recorded_rss_failure`
- Candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Scope bytes: `250,000`
- Driver result JSON: `not present`
- Driver result present: `false`
- RSS guard JSON: `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20352k_250000_determinism_rss_guard.json`
- RSS guard present: `true`
- Active scorer observed: `false`
- Live gate: `false`
- Liveness classification: `not_persisted_running`
- Matching adaptive jobs: `0`
- Matching controllers: `0`
- Matching driver observed: `false`
- Liveness claim rule: `A persisted running receipt is live only with an exact driver, an owning controller, or a matching adaptive running job backed by the host-local heavy lock. The lock alone never identifies a gate.`
- RSS guard status: `aborted_official_decimal_memory_limit`
- RSS guard JSON bytes: `1,237`
- RSS guard JSON modified UTC: `2026-07-11T15:13:39+00:00`
- RSS guard JSON SHA-256: `e83b46f7d57fa85bff44d2222700d43f098bf74378174e4ec12d19c74032502f`
- RSS samples: `173`
- Max sampled single RSS KiB: `9,768,612`
- Max sampled tree RSS KiB: `9,787,964`
- Single-process RSS margin KiB: `717,148`
- Single-process decimal `10GB` margin KiB: `-2,987`
- Tree RSS margin KiB: `697,796`
- Tree decimal `10GB` margin KiB: `-22,339`
- Latest sampled single RSS KiB: `9,768,612`
- Latest sampled tree RSS KiB: `9,787,964`
- Latest sampled single-process margin KiB: `717,148`
- Latest sampled single-process decimal `10GB` margin KiB: `-2,987`
- Latest sampled tree margin KiB: `697,796`
- Latest sampled tree decimal `10GB` margin KiB: `-22,339`

## Terminal Gate Command

```bash
python3 projects/enwiki9/tools/cmix21_gate_decider.py cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1 --scope 250000 --apply-terminal --normalize --package-lower
```

## Gate Evidence Status

- Claim status: `guard_without_driver_result`
- Driver result terminal: `false`
- RSS guard terminal: `true`
- Scored gate result present: `false`
- Live guard only: `false`
- Claim rule: `Only a terminal driver result with roundtrip evidence can become a benchmark row.`

## Observed Gate Command

- Expected candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Expected scope bytes: `250,000`
- Driver process count: `0`
- Active gate command observed: `false`
- Driver command mismatch count: `0`

| PID | Candidate Match | Scope Bytes | Scope Match | Determinism Flag |
|---:|---|---:|---|---|
| n/a | n/a | n/a | n/a | n/a |

## Observed Controller Command

- Expected active candidate: `cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
- Expected active scope bytes: `250,000`
- Controller process count: `0`
- Scope note: `Controller scope may be the completed parent gate that launched the active child; the observed driver command is authoritative for the active gate scope.`

| PID | Candidate Match | Controller Scope | Scope Match Active Gate | Apply Terminal | Launch Next | Package Lower |
|---:|---|---:|---|---|---|---|
| n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Operator Action

- Safe to launch heavy gate: `false`
- Action: `record_rss_failure_then_package_lower_candidate`
- Reason: `RSS failure must be recorded before the next memory-valve candidate is built`
- Allowed work: `n/a`
- Forbidden work: `n/a`

## Handoff

- Terminal verdict present: `true`
- Heavy gate mutation allowed: `true`
- Recommended action: `record_rss_failure_then_package_lower_candidate`
- Command source: `cmix21_gate_decider.apply_terminal_command`
- Claim rule: `No prefix row proves 10.95%.`
- Apply terminal command:
```bash
python3 projects/enwiki9/tools/cmix21_gate_decider.py cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1 --scope 250000 --apply-terminal --normalize --package-lower
```

## Operator Logs

- Latest delayed status log: `projects/enwiki9/run_logs/enwiki9_delayed_status_latest.log`
- Latest delayed status log present: `true`
- Latest delayed status resolved log: `projects/enwiki9/run_logs/enwiki9_delayed_status_20260709T122555Z.log`

## Candidate Audit

- Audit return code: `0`
- Program directories: `546`
- Registered programs: `229`
- Untracked nonignored entries: `0`
- Modified tracked entries: `14`
- Candidate statuses: `active=22, blocked_dependency=31, candidate=5, measured_negative=89, retired=399`

## Active Runner Process Table

| Role | PID | PPID | RSS KiB | Command |
|---|---:|---:|---:|---|
| n/a | n/a | n/a | n/a | n/a |

## Active Candidate Recent Artifacts

| Path | Bytes | Modified UTC |
|---|---:|---|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20352k_250000_determinism_rss_guard.json` | 1,237 | `2026-07-11T15:13:39+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20352k_1024_determinism_rss_guard.json` | 978 | `2026-07-11T15:10:12+00:00` |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-11T111011.json` | 1,430 | `2026-07-11T15:10:11+00:00` |

## Contingencies

- If current gate passes: `promote unchanged`
- Pass next scope: `1,000,000`
- If RSS fails: `record RSS failure and package lower PPMD cap`
- Lower candidate: `cmix21_text_mmap_paq5_ppmd20224k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1`
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
