# Hutter Upper-Bound Certificate

## Constructive Theorem

If roundtrip_ok is true for archive A and decoder D on target corpus x, then |A| + |D| is a constructive upper bound for x in this testbed.

## Target

- Full input bytes: `1,000,000,000`
- 10.95% target score: `109,500,000`
- Calibrated baseline score: `110,181,114`
- Required net gain from calibrated baseline: `681,114` bytes
- Required archive slope before program cost: `0.005448912` bits/byte

## Proof Status

- Full-corpus constructive result present: `False`
- 10.95 constructive upper bound present: `False`

## Best Full-Corpus Result

No verified full-corpus result JSON is present in this workspace.

## Best Exact Upper Bounds By Scope

| data_size | program | score | archive | program_size | percent | result |
|---:|---|---:|---:|---:|---:|---|
| 1,000 | `fx2_geometry_title_sidecar_byte_split_direct_extra_page_match_v1` | 365,803 | 260 | 365,543 | 36580.3 | `results/fx2_geometry_title_sidecar_byte_split_direct_extra_page_match_v1/2026-06-06T225521.json` |
| 1,024 | `baseline_bz2` | 567 | 401 | 166 | 55.37109375 | `results/baseline_bz2/2026-06-07T184036.json` |
| 65,536 | `baseline_lzma` | 22,805 | 22,604 | 201 | 34.797668457 | `results/baseline_lzma/2026-06-07T152335.json` |
| 250,000 | `opcode_typed_anchor_bitmix_v1` | 72,800 | 67,959 | 4,841 | 29.12 | `results/opcode_typed_anchor_bitmix_v1/2026-06-08T114728.json` |
| 1,000,000 | `opcode_typed_anchor_bitmix_v1` | 266,493 | 261,652 | 4,841 | 26.6493 | `results/opcode_typed_anchor_bitmix_v1/2026-06-08T120140.json` |
| 1,048,576 | `fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1` | 438,939 | 182,361 | 256,578 | 41.860485077 | `results/fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1/2026-06-07T175351.json` |
| 10,000,000 | `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | 1,882,615 | 1,643,289 | 239,326 | 18.82615 | `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1/2026-06-08T201540.json` |

## Best Exact Archive By Scope

| data_size | program | archive | score | program_size | archive_bpb | result |
|---:|---|---:|---:|---:|---:|---|
| 1,000 | `fx2_timestamp_direct_only_byte_split_extra_page_match_v1` | 243 | 383,619 | 383,376 | 1.944 | `results/fx2_timestamp_direct_only_byte_split_extra_page_match_v1/2026-06-07T000100.json` |
| 1,024 | `cmix21_text_mmap_paq5_ppmd70m_fxcmrcm16_rcm32_bufthirtysecond_minmaps_v1` | 246 | 561,459 | 561,213 | 1.921875 | `results/cmix21_text_mmap_paq5_ppmd70m_fxcmrcm16_rcm32_bufthirtysecond_minmaps_v1/2026-06-15T044111.json` |
| 65,536 | `fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1` | 13,573 | 270,151 | 256,578 | 1.656860352 | `results/fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1/2026-06-07T174031.json` |
| 250,000 | `fx2_timestamp_direct_only_byte_split_extra_page_match_v1` | 44,976 | 428,352 | 383,376 | 1.439232 | `results/fx2_timestamp_direct_only_byte_split_extra_page_match_v1/2026-06-07T002058.json` |
| 1,000,000 | `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | 174,415 | 735,625 | 561,210 | 1.39532 | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1/2026-06-14T234158.json` |
| 1,048,576 | `fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1` | 182,361 | 438,939 | 256,578 | 1.391304016 | `results/fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1/2026-06-07T175351.json` |
| 10,000,000 | `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | 1,643,289 | 1,882,615 | 239,326 | 1.3146312 | `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1/2026-06-08T201540.json` |

## Notes

- Prefix results prove upper bounds only for that prefix, not for enwik9.
- Projected 1GB scores are search evidence and are excluded from proof_status.
- A 10.95 proof requires a full 1GB result with score <= 109500000.
