# enwiki9 Artifact Fingerprint Audit

This lock-safe audit checks candidate `meta.json` receipt references.
It does not launch compression and does not score a candidate.

- Artifact checks: `231`
- OK: `true`
- Rule: `Rows with recorded receipt hashes must match their artifact files. Rows without hashes are legacy evidence and should be repaired when re-recorded.`

## Status Counts

| Status | Count |
|---|---:|
| `match` | 231 |

## Hash Mismatches

| Candidate | Label | Field | Path |
|---|---|---|---|
| n/a | n/a | n/a | n/a |

## Missing Artifacts

| Candidate | Label | Field | Path |
|---|---|---|---|
| n/a | n/a | n/a | n/a |

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
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21248k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21248k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21376k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21504k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21632k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21632k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21760k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21760k_100000000_determinism_rss_guard.json` | 2 |
| `projects/enwiki9/results/cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/ppmd21888k_100000000_determinism_rss_guard.json` | 2 |
