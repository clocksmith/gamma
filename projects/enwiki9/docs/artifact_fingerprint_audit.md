# enwiki9 Artifact Fingerprint Audit

This lock-safe audit checks candidate `meta.json` receipt references.
It does not launch compression and does not score a candidate.

- Artifact checks: `305`
- Present artifact integrity OK: `true`
- Local artifact set complete: `false`
- Rule: `Present artifacts with recorded receipt hashes must match. Missing local artifacts remain explicit provenance gaps and cannot support proof claims, but do not block regeneration of views from a partial checkout. Rows without hashes are legacy evidence and should be repaired when re-recorded.`

## Status Counts

| Status | Count |
|---|---:|
| `match` | 303 |
| `missing_artifact` | 2 |

## Hash Mismatches

| Candidate | Label | Field | Path |
|---|---|---|---|
| n/a | n/a | n/a | n/a |

## Missing Artifacts

| Candidate | Label | Field | Path |
|---|---|---|---|
| `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | `100000000_guard_returncode_fail` | `rss_guard_json` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_100000000_determinism_rss_guard.json` |
| `cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1` | `100000000_guard_returncode_fail` | `guard_path` | `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20352k_fxcm2_fxcmrcm20_ppmdguard2_rcm32_buffull_minmaps_v1/ppmd20352k_100000000_determinism_rss_guard.json` |

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
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd1024k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd1024k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd11776k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd11776k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd19968k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd19968k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20096k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20096k_250000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd20224k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd20224k_250000_determinism_rss_guard.json` | 2 |
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
