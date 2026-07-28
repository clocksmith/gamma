# Hutter Upper-Bound Certificate

## Constructive Theorem

If roundtrip_ok is true for archive A and decoder D on target corpus x, then |A| + |D| is a constructive upper bound for x in this testbed.

## Target

- Full input bytes: `1,000,000,000`
- 10.95% target score: `108,000,000`
- Calibrated baseline score: `110,181,114`
- Required net gain from calibrated baseline: `2,181,114` bytes
- Required archive slope before program cost: `0.017448912` bits/byte

## Proof Status

- Full-corpus constructive result present: `False`
- 10.95 constructive upper bound present: `False`

## Top Status

| Claim | Program | Scope | Score | Evidence | Status |
|---|---|---:|---:|---|---|
| best exact 10M | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 10,000,000 | 1,825,866 | exact result JSON with roundtrip_ok true | exact artifact-backed |
| best exact 10M archive | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 10,000,000 | 1,825,866 | exact result JSON with roundtrip_ok true; archive-slope reference only | exact artifact-backed |
| best exact 100M | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 100,000,000 | 15,040,789 | exact result JSON with roundtrip_ok true | exact artifact-backed |
| best full 1G | `n/a` | 1,000,000,000 | n/a | no verified full-corpus result JSON is present in this checkout | not verified |
| best forecast | `endpoint428_pair_layer0_online_native_10m_v1` | 10,000,000 | 109,524,268 | exact guarded 10M archive screen with counted program economics; terminal verdict retire_unchanged_exact_10m_economics_miss; forecast only, not a constructive full-corpus proof | exact-10m-counted-projection |
| active candidate | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 100,000,000 | 15,040,789 | exact 100,000,000 byte replay passed with roundtrip and determinism; promotion state is derived from the latest guard receipt | exact 100,000,000 byte gate passed |
| blocker | `n/a` | n/a | n/a | active 1,000,000,000 byte deterministic replay has not produced terminal driver and RSS receipts yet | open |
| active gate | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 1,000,000,000 | n/a | unchanged 1,000,000,000 byte RSS-guarded determinism replay; wait for terminal receipts | pending |

## Best Full-Corpus Result

No verified full-corpus result JSON is present in this workspace.

## Best Exact Upper Bounds By Scope

| data_size | program | score | archive | program_size | percent | result |
|---:|---|---:|---:|---:|---:|---|
| 1,024 | `baseline_zlib` | 495 | 334 | 161 | 48.33984375 | `results/baseline_zlib/2026-07-20T152000.json` |
| 10,000 | `baseline_lzma` | 3,857 | 3,656 | 201 | 38.57 | `results/baseline_lzma/2026-07-27T213049.json` |
| 250,000 | `opcode_typed_anchor_bitmix_v1` | 72,800 | 67,959 | 4,841 | 29.12 | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T124407.json` |
| 600,747 | `vulcan_event_control_v0` | 377,494 | 367,924 | 9,570 | 62.837434061 | `results/vulcan_event_control_v0/2026-07-26T080355.json` |
| 1,000,000 | `opcode_typed_anchor_bitmix_v1` | 266,493 | 261,652 | 4,841 | 26.6493 | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T150923.json` |
| 10,000,000 | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 1,825,866 | 1,642,858 | 183,008 | 18.25866 | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| 100,000,000 | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 15,040,789 | 14,857,781 | 183,008 | 15.040789 | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json` |

## Best Exact Archive By Scope

| data_size | program | archive | score | program_size | archive_bpb | result |
|---:|---|---:|---:|---:|---:|---|
| 1,024 | `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | 243 | 304,496 | 304,253 | 1.8984375 | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T163727.json` |
| 10,000 | `baseline_lzma` | 3,656 | 3,857 | 201 | 2.9248 | `results/baseline_lzma/2026-07-27T213049.json` |
| 250,000 | `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | 44,978 | 349,231 | 304,253 | 1.439296 | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T170257.json` |
| 600,747 | `vulcan_event_control_v0` | 367,924 | 377,494 | 9,570 | 4.899553389 | `results/vulcan_event_control_v0/2026-07-26T080355.json` |
| 1,000,000 | `cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1` | 174,423 | 735,705 | 561,282 | 1.395384 | `results/cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1/2026-07-21T183101.json` |
| 10,000,000 | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 1,642,858 | 1,825,866 | 183,008 | 1.3142864 | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| 100,000,000 | `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | 14,857,781 | 15,040,789 | 183,008 | 1.18862248 | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json` |

## Notes

- Prefix results prove upper bounds only for that prefix, not for enwik9.
- Projected 1GB scores are search evidence and are excluded from proof_status.
- A 10.80 proof requires a full 1GB result with score <= 108000000.
