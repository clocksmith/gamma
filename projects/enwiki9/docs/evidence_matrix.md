# enwiki9 Evidence Matrix

Generated from result JSON files present in this checkout.

Claim rule:

```text
A row is artifact-backed only for its measured scope.
No prefix row proves 10.95%.
No forecast or inherited metadata is included here.
```

## Proof Boundary

- Result JSON files scanned: `912`
- Roundtrip-passing rows: `909`
- Verified full `1G` rows in this checkout: `0`
- `10.95%` target reached by this matrix: `False`
- Best full `1G` score: `none present`

## Best Exact Score By Scope

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `baseline_zlib` | baseline compressor | 1,024 | 495 | 334 | 161 | 2.609375 | true | `results/baseline_zlib/2026-07-20T152000.json` |
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 250,000 | 72,800 | 67,959 | 4,841 | 2.174688 | true | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T124407.json` |
| `vulcan_event_control_v0` | custom candidate | 600,747 | 377,494 | 367,924 | 9,570 | 4.89955339 | true | `results/vulcan_event_control_v0/2026-07-26T080355.json` |
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 1,000,000 | 266,493 | 261,652 | 4,841 | 2.093216 | true | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T150923.json` |
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 100,000,000 | 15,040,789 | 14,857,781 | 183,008 | 1.18862248 | true | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json` |

## Best Exact Archive By Scope

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | cmix21 memory-shaped context mixer | 1,024 | 304,496 | 243 | 304,253 | 1.8984375 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T163727.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | cmix21 memory-shaped context mixer | 250,000 | 349,231 | 44,978 | 304,253 | 1.439296 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T170257.json` |
| `vulcan_event_control_v0` | custom candidate | 600,747 | 377,494 | 367,924 | 9,570 | 4.89955339 | true | `results/vulcan_event_control_v0/2026-07-26T080355.json` |
| `cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 735,705 | 174,423 | 561,282 | 1.395384 | true | `results/cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1/2026-07-21T183101.json` |
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 100,000,000 | 15,040,789 | 14,857,781 | 183,008 | 1.18862248 | true | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-22T222147.json` |

## Top Score Rows At 10,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 10,000,000 | 2,720,457 | 2,720,256 | 201 | 2.1762048 | true | `results/baseline_lzma/2026-07-21T172645.json` |
| `blue_dolphin_tree_macro_v1` | custom candidate | 10,000,000 | 2,743,001 | 2,733,028 | 9,973 | 2.1864224 | true | `results/blue_dolphin_tree_macro_v1/2026-07-20T151748.json` |
| `blue_dolphin_mediawiki_inline_v1` | custom candidate | 10,000,000 | 2,744,980 | 2,741,292 | 3,688 | 2.1930336 | true | `results/blue_dolphin_mediawiki_inline_v1/2026-07-20T151743.json` |

## Top Archive Rows At 10,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 10,000,000 | 2,720,457 | 2,720,256 | 201 | 2.1762048 | true | `results/baseline_lzma/2026-07-21T172645.json` |
| `blue_dolphin_tree_macro_v1` | custom candidate | 10,000,000 | 2,743,001 | 2,733,028 | 9,973 | 2.1864224 | true | `results/blue_dolphin_tree_macro_v1/2026-07-20T151748.json` |
| `blue_dolphin_mediawiki_inline_v1` | custom candidate | 10,000,000 | 2,744,980 | 2,741,292 | 3,688 | 2.1930336 | true | `results/blue_dolphin_mediawiki_inline_v1/2026-07-20T151743.json` |

## Top Score Rows At 1,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 1,000,000 | 266,493 | 261,652 | 4,841 | 2.093216 | true | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T150923.json` |
| `opcode_typed_anchor_ppm_o5_v1` | syntax opcode preprocessor | 1,000,000 | 270,089 | 266,028 | 4,061 | 2.128224 | true | `results/opcode_typed_anchor_ppm_o5_v1/2026-07-21T144847.json` |
| `opcode_typed_anchor_ppm_o5_v1` | syntax opcode preprocessor | 1,000,000 | 270,089 | 266,028 | 4,061 | 2.128224 | true | `results/opcode_typed_anchor_ppm_o5_v1/2026-07-21T145001.json` |
| `article_receipt_family_tree_v1` | custom candidate | 1,000,000 | 270,449 | 264,371 | 6,078 | 2.114968 | true | `results/article_receipt_family_tree_v1/2026-07-21T150101.json` |
| `article_receipt_family_tree_v1` | custom candidate | 1,000,000 | 270,449 | 264,371 | 6,078 | 2.114968 | true | `results/article_receipt_family_tree_v1/2026-07-21T150208.json` |
| `chain_index_ppmc_shared_v3` | custom candidate | 1,000,000 | 272,888 | 269,400 | 3,488 | 2.1552 | true | `results/chain_index_ppmc_shared_v3/2026-07-21T144547.json` |
| `chain_index_ppmc_shared_v2` | custom candidate | 1,000,000 | 272,909 | 269,432 | 3,477 | 2.155456 | true | `results/chain_index_ppmc_shared_v2/2026-07-21T144544.json` |
| `chain_index_ppmc_shared_v1` | custom candidate | 1,000,000 | 273,191 | 269,784 | 3,407 | 2.158272 | true | `results/chain_index_ppmc_shared_v1/2026-07-21T144535.json` |

## Top Archive Rows At 1,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 735,705 | 174,423 | 561,282 | 1.395384 | true | `results/cmix21_text_mmap_paq5_ppmd75m_fxcmrcm28safe_rcm32_bufthirtysecond_minmaps_v1/2026-07-21T183101.json` |
| `fx2_struct_top_mixer_v1` | custom candidate | 1,000,000 | 447,188 | 175,172 | 272,016 | 1.401376 | true | `results/fx2_struct_top_mixer_v1/2026-07-21T151947.json` |
| `fx2_structural_sidecar_v1` | fx2 sidecar or stream split | 1,000,000 | 531,814 | 175,177 | 356,637 | 1.401416 | true | `results/fx2_structural_sidecar_v1/2026-07-21T151039.json` |
| `fx2cmix_recovered_gcc_o3_xz_minwrap_v1` | custom candidate | 1,000,000 | 458,920 | 175,203 | 283,717 | 1.401624 | true | `results/fx2cmix_recovered_gcc_o3_xz_minwrap_v1/2026-07-21T174845.json` |
| `fx2cmix_recovered_gcc_o3_xz_v1` | custom candidate | 1,000,000 | 459,575 | 175,203 | 284,372 | 1.401624 | true | `results/fx2cmix_recovered_gcc_o3_xz_v1/2026-07-21T152648.json` |
| `fx2_sidecar_byte_split_direct_page_match_v1` | fx2 sidecar or stream split | 1,000,000 | 538,455 | 175,204 | 363,251 | 1.401632 | true | `results/fx2_sidecar_byte_split_direct_page_match_v1/2026-07-21T150920.json` |
| `fx2cmix_recovered_gcc_o3_meta_streak_add_xz_v1` | custom candidate | 1,000,000 | 459,272 | 175,207 | 284,065 | 1.401656 | true | `results/fx2cmix_recovered_gcc_o3_meta_streak_add_xz_v1/2026-07-21T152253.json` |
| `fx2cmix_recovered_gcc_o3_meta_streak_add_xz_v1` | custom candidate | 1,000,000 | 459,272 | 175,207 | 284,065 | 1.401656 | true | `results/fx2cmix_recovered_gcc_o3_meta_streak_add_xz_v1/2026-07-21T172147.json` |

## Top Score Rows At 250,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 250,000 | 72,800 | 67,959 | 4,841 | 2.174688 | true | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T124407.json` |
| `opcode_word_bz2_tiny_k4_v1` | syntax opcode preprocessor | 250,000 | 73,154 | 71,917 | 1,237 | 2.301344 | true | `results/opcode_word_bz2_tiny_k4_v1/2026-07-21T124139.json` |
| `ppm_residual_shape_pack_v1` | custom candidate | 250,000 | 73,308 | 71,352 | 1,956 | 2.283264 | true | `results/ppm_residual_shape_pack_v1/2026-07-21T124146.json` |
| `opcode_word_bz2_min_deflate_v1` | syntax opcode preprocessor | 250,000 | 73,335 | 71,887 | 1,448 | 2.300384 | true | `results/opcode_word_bz2_min_deflate_v1/2026-07-21T124141.json` |
| `opcode_word_bz2_deflate_v1` | syntax opcode preprocessor | 250,000 | 73,402 | 71,887 | 1,515 | 2.300384 | true | `results/opcode_word_bz2_deflate_v1/2026-07-21T124140.json` |
| `bayes_union_tree_deflate_v1` | custom candidate | 250,000 | 74,401 | 72,659 | 1,742 | 2.325088 | true | `results/bayes_union_tree_deflate_v1/2026-07-20T160147.json` |
| `bayes_union_tree_gz_v1` | custom candidate | 250,000 | 74,421 | 72,659 | 1,762 | 2.325088 | true | `results/bayes_union_tree_gz_v1/2026-07-20T160150.json` |
| `opcode_typed_anchor_ppm_o5_v1` | syntax opcode preprocessor | 250,000 | 74,999 | 70,938 | 4,061 | 2.270016 | true | `results/opcode_typed_anchor_ppm_o5_v1/2026-07-21T124224.json` |

## Top Archive Rows At 250,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | cmix21 memory-shaped context mixer | 250,000 | 349,231 | 44,978 | 304,253 | 1.439296 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T170257.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osxz_v1` | cmix21 memory-shaped context mixer | 250,000 | 375,839 | 44,978 | 330,861 | 1.439296 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osxz_v1/2026-07-20T170307.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_xzstrip_v1` | cmix21 memory-shaped context mixer | 250,000 | 498,961 | 45,184 | 453,777 | 1.445888 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_xzstrip_v1/2026-07-20T165204.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_xz_v1` | cmix21 memory-shaped context mixer | 250,000 | 519,265 | 45,184 | 474,081 | 1.445888 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_xz_v1/2026-07-20T165136.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 606,394 | 45,184 | 561,210 | 1.445888 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_v1/2026-07-20T162139.json` |
| `fx2_timestamp_direct_byte_split_extra_page_match_v1` | custom candidate | 250,000 | 586,796 | 45,195 | 541,601 | 1.44624 | true | `results/fx2_timestamp_direct_byte_split_extra_page_match_v1/2026-07-20T162732.json` |
| `fx2_timestamp_direct_byte_split_extra_page_match_v1` | custom candidate | 250,000 | 586,796 | 45,195 | 541,601 | 1.44624 | true | `results/fx2_timestamp_direct_byte_split_extra_page_match_v1/2026-07-20T170513.json` |
| `fx2_sidecar_byte_split_direct_page_match_v1` | fx2 sidecar or stream split | 250,000 | 408,512 | 45,261 | 363,251 | 1.448352 | true | `results/fx2_sidecar_byte_split_direct_page_match_v1/2026-07-20T155131.json` |
