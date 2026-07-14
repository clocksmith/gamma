# enwiki9 Artifact Fingerprint Audit

This lock-safe audit checks candidate `meta.json` receipt references.
It does not launch compression and does not score a candidate.

- Artifact checks: `289`
- OK: `false`
- Rule: `Rows with recorded receipt hashes must match their artifact files. Rows without hashes are legacy evidence and should be repaired when re-recorded.`

## Status Counts

| Status | Count |
|---|---:|
| `match` | 2 |
| `missing_artifact` | 287 |

## Hash Mismatches

| Candidate | Label | Field | Path |
|---|---|---|---|
| n/a | n/a | n/a | n/a |

## Missing Artifacts

| Candidate | Label | Field | Path |
|---|---|---|---|
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T145351.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1024` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T131851.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `250000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T134110.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T055557.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1024` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T042102.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `250000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T044302.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T102554.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1024` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T085020.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `250000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T091229.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T210059.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1024` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T192628.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `250000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T194833.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1/2026-06-14T234158.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | `1m_driver_determinism_gate` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1/2026-06-14T234158.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | `250k_driver_gate` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1/2026-06-14T222820.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T012804.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1024` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T235331.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `250000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T001527.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1000000` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T163015.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_stemguard_rcm32_bufthirtysecond_minmaps_v1` | `1024` | `result_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T145439.json` |

## Legacy Rows Missing Recorded Hashes

| Candidate | Label | Field | Path |
|---|---|---|---|
| n/a | n/a | n/a | n/a |

## Legacy Repair Queue By Candidate

| Candidate | Missing Hash Rows |
|---|---:|
| n/a | 0 |

## Duplicate Artifact References

These are not failures; they show receipt files reused by multiple meta labels.

| Path | Reference Count |
|---|---:|
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1/2026-06-14T234158.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20352k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20480k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20480k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20608k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20608k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20736k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20736k_10000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20864k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20864k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20992k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20992k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21120k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21120k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21248k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21376k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21504k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21632k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21760k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21888k_100000000_determinism_rss_guard.json` | 2 |
