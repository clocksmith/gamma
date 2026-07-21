# enwiki9 Evidence Matrix

Generated from result JSON files present in this checkout.

Claim rule:

```text
A row is artifact-backed only for its measured scope.
No prefix row proves 10.95%.
No forecast or inherited metadata is included here.
```

## Proof Boundary

- Result JSON files scanned: `679`
- Roundtrip-passing rows: `679`
- Verified full `1G` rows in this checkout: `0`
- `10.95%` target reached by this matrix: `False`
- Best full `1G` score: `none present`

## Best Exact Score By Scope

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `baseline_zlib` | baseline compressor | 1,024 | 495 | 334 | 161 | 2.609375 | true | `results/baseline_zlib/2026-07-20T152000.json` |
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 250,000 | 72,800 | 67,959 | 4,841 | 2.174688 | true | `results/opcode_typed_anchor_bitmix_v1/2026-07-21T124407.json` |
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,933 | 290,732 | 201 | 2.325856 | true | `results/baseline_lzma/2026-07-18T135552.json` |
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |

## Best Exact Archive By Scope

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | cmix21 memory-shaped context mixer | 1,024 | 304,496 | 243 | 304,253 | 1.8984375 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T163727.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1` | cmix21 memory-shaped context mixer | 250,000 | 349,231 | 44,978 | 304,253 | 1.439296 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_rcm32_bufthirtysecond_minmaps_osminxz_v1/2026-07-20T170257.json` |
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,933 | 290,732 | 201 | 2.325856 | true | `results/baseline_lzma/2026-07-18T135552.json` |
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |

## Top Score Rows At 10,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| `blue_dolphin_tree_macro_v1` | custom candidate | 10,000,000 | 2,743,001 | 2,733,028 | 9,973 | 2.1864224 | true | `results/blue_dolphin_tree_macro_v1/2026-07-20T151748.json` |
| `blue_dolphin_mediawiki_inline_v1` | custom candidate | 10,000,000 | 2,744,980 | 2,741,292 | 3,688 | 2.1930336 | true | `results/blue_dolphin_mediawiki_inline_v1/2026-07-20T151743.json` |

## Top Archive Rows At 10,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1` | fx2 geometry/order wrapper | 10,000,000 | 1,825,866 | 1,642,858 | 183,008 | 1.3142864 | not recorded | `results/fx2_geometry_sort_dictcmix_xz_zlibpy_min_v1/2026-07-20T155707.json` |
| `blue_dolphin_tree_macro_v1` | custom candidate | 10,000,000 | 2,743,001 | 2,733,028 | 9,973 | 2.1864224 | true | `results/blue_dolphin_tree_macro_v1/2026-07-20T151748.json` |
| `blue_dolphin_mediawiki_inline_v1` | custom candidate | 10,000,000 | 2,744,980 | 2,741,292 | 3,688 | 2.1930336 | true | `results/blue_dolphin_mediawiki_inline_v1/2026-07-20T151743.json` |

## Top Score Rows At 1,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,933 | 290,732 | 201 | 2.325856 | true | `results/baseline_lzma/2026-07-18T135552.json` |
| `wikiir_template_grammar_v1` | custom candidate | 1,000,000 | 302,838 | 290,733 | 12,105 | 2.325864 | true | `results/wikiir_template_grammar_v1/2026-07-18T140017.json` |
| `wikiir_webgraph_v1` | custom candidate | 1,000,000 | 302,853 | 290,733 | 12,120 | 2.325864 | true | `results/wikiir_webgraph_v1/2026-07-18T144208.json` |
| `wikiir_title_vertex_v1` | custom candidate | 1,000,000 | 303,066 | 290,733 | 12,333 | 2.325864 | true | `results/wikiir_title_vertex_v1/2026-07-18T150122.json` |
| `blue_dolphin_tree_macro_savings_v1` | custom candidate | 1,000,000 | 304,172 | 292,112 | 12,060 | 2.336896 | true | `results/blue_dolphin_tree_macro_savings_v1/2026-07-18T135528.json` |
| `wikiir_prior_page_delta_v1` | custom candidate | 1,000,000 | 304,967 | 290,733 | 14,234 | 2.325864 | true | `results/wikiir_prior_page_delta_v1/2026-07-18T140358.json` |

## Top Archive Rows At 1,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,933 | 290,732 | 201 | 2.325856 | true | `results/baseline_lzma/2026-07-18T135552.json` |
| `wikiir_template_grammar_v1` | custom candidate | 1,000,000 | 302,838 | 290,733 | 12,105 | 2.325864 | true | `results/wikiir_template_grammar_v1/2026-07-18T140017.json` |
| `wikiir_webgraph_v1` | custom candidate | 1,000,000 | 302,853 | 290,733 | 12,120 | 2.325864 | true | `results/wikiir_webgraph_v1/2026-07-18T144208.json` |
| `wikiir_title_vertex_v1` | custom candidate | 1,000,000 | 303,066 | 290,733 | 12,333 | 2.325864 | true | `results/wikiir_title_vertex_v1/2026-07-18T150122.json` |
| `wikiir_prior_page_delta_v1` | custom candidate | 1,000,000 | 304,967 | 290,733 | 14,234 | 2.325864 | true | `results/wikiir_prior_page_delta_v1/2026-07-18T140358.json` |
| `blue_dolphin_tree_macro_savings_v1` | custom candidate | 1,000,000 | 304,172 | 292,112 | 12,060 | 2.336896 | true | `results/blue_dolphin_tree_macro_savings_v1/2026-07-18T135528.json` |

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
