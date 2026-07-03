# enwiki9 Evidence Matrix

Generated from result JSON files present in this checkout.

Claim rule:

```text
A row is artifact-backed only for its measured scope.
No prefix row proves 10.95%.
No forecast or inherited metadata is included here.
```

## Proof Boundary

- Result JSON files scanned: `670`
- Roundtrip-passing rows: `648`
- Verified full `1G` rows in this checkout: `0`
- `10.95%` target reached by this matrix: `False`
- Best full `1G` score: `none present`

## Best Exact Score By Scope

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_geometry_title_sidecar_byte_split_direct_extra_page_match_v1` | fx2 geometry/order wrapper | 1,000 | 365,803 | 260 | 365,543 | 2.08 | true | `results/fx2_geometry_title_sidecar_byte_split_direct_extra_page_match_v1/2026-06-06T225521.json` |
| `baseline_bz2` | baseline compressor | 1,024 | 567 | 401 | 166 | 3.1328125 | true | `results/baseline_bz2/2026-06-07T184036.json` |
| `baseline_lzma` | LZMA/LZMA2 baseline or preprocessor | 65,536 | 22,805 | 22,604 | 201 | 2.75927734 | true | `results/baseline_lzma/2026-06-07T152335.json` |
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 250,000 | 72,800 | 67,959 | 4,841 | 2.174688 | true | `results/opcode_typed_anchor_bitmix_v1/2026-06-08T114728.json` |
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 1,000,000 | 266,493 | 261,652 | 4,841 | 2.093216 | true | `results/opcode_typed_anchor_bitmix_v1/2026-06-08T120140.json` |
| `fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1` | fx2 sidecar or stream split | 1,048,576 | 438,939 | 182,361 | 256,578 | 1.39130402 | not recorded | `results/fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1/2026-06-07T175351.json` |
| `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | fx2/cmix tuned wrapper | 10,000,000 | 1,882,615 | 1,643,289 | 239,326 | 1.3146312 | true | `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1/2026-06-08T201540.json` |

## Best Exact Archive By Scope

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_timestamp_direct_only_byte_split_extra_page_match_v1` | custom candidate | 1,000 | 383,619 | 243 | 383,376 | 1.944 | true | `results/fx2_timestamp_direct_only_byte_split_extra_page_match_v1/2026-06-07T000100.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,024 | 562,732 | 246 | 562,486 | 1.921875 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T042102.json` |
| `fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1` | fx2 sidecar or stream split | 65,536 | 270,151 | 13,573 | 256,578 | 1.65686035 | true | `results/fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1/2026-06-07T174031.json` |
| `fx2_timestamp_direct_only_byte_split_extra_page_match_v1` | custom candidate | 250,000 | 428,352 | 44,976 | 383,376 | 1.439232 | not recorded | `results/fx2_timestamp_direct_only_byte_split_extra_page_match_v1/2026-06-07T002058.json` |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,961 | 174,395 | 562,566 | 1.39516 | not recorded | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1/2026-06-20T155023.json` |
| `fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1` | fx2 sidecar or stream split | 1,048,576 | 438,939 | 182,361 | 256,578 | 1.39130402 | not recorded | `results/fx2_sidecar_byte_split_direct_extra_page_match_dictcmix_xz_min_v1/2026-06-07T175351.json` |
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,359 | 1,638,083 | 564,276 | 1.3104664 | true | `results/cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-28T005909.json` |

## Top Score Rows At 10,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1` | fx2/cmix tuned wrapper | 10,000,000 | 1,882,615 | 1,643,289 | 239,326 | 1.3146312 | true | `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftmiddeep_v1/2026-06-08T201540.json` |
| `fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftdeep_safe_v1` | fx2/cmix tuned wrapper | 10,000,000 | 1,882,649 | 1,643,346 | 239,303 | 1.3146768 | true | `results/fx2_core_tune_title_mctx8000_m0p100_m1p95_lstm1p00_sse1000_decay_shiftdeep_safe_v1/2026-06-09T004038.json` |
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,359 | 1,638,083 | 564,276 | 1.3104664 | true | `results/cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-28T005909.json` |
| `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,372 | 1,638,098 | 564,274 | 1.3104784 | true | `results/cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-03T062324.json` |
| `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,376 | 1,638,101 | 564,275 | 1.3104808 | true | `results/cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-26T114711.json` |
| `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,389 | 1,638,114 | 564,275 | 1.3104912 | true | `results/cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-29T012252.json` |
| `cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,407 | 1,638,134 | 564,273 | 1.3105072 | true | `results/cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-24T101836.json` |
| `cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,426 | 1,638,153 | 564,273 | 1.3105224 | true | `results/cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-23T203949.json` |

## Top Archive Rows At 10,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,359 | 1,638,083 | 564,276 | 1.3104664 | true | `results/cmix21_text_mmap_paq5_ppmd22400k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-28T005909.json` |
| `cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,372 | 1,638,098 | 564,274 | 1.3104784 | true | `results/cmix21_text_mmap_paq5_ppmd21376k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-03T062324.json` |
| `cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,376 | 1,638,101 | 564,275 | 1.3104808 | true | `results/cmix21_text_mmap_paq5_ppmd22m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-26T114711.json` |
| `cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,389 | 1,638,114 | 564,275 | 1.3104912 | true | `results/cmix21_text_mmap_paq5_ppmd22272k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-29T012252.json` |
| `cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,407 | 1,638,134 | 564,273 | 1.3105072 | true | `results/cmix21_text_mmap_paq5_ppmd23m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-24T101836.json` |
| `cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,426 | 1,638,153 | 564,273 | 1.3105224 | true | `results/cmix21_text_mmap_paq5_ppmd24m_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-23T203949.json` |
| `cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,438 | 1,638,165 | 564,273 | 1.310532 | true | `results/cmix21_text_mmap_paq5_ppmd21504k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-07-02T060615.json` |
| `cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 10,000,000 | 2,202,456 | 1,638,182 | 564,274 | 1.3105456 | true | `results/cmix21_text_mmap_paq5_ppmd21888k_fxcmidx13div2_fxcmrcm20_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-29T183814.json` |

## Top Score Rows At 1,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 1,000,000 | 266,493 | 261,652 | 4,841 | 2.093216 | true | `results/opcode_typed_anchor_bitmix_v1/2026-06-08T120140.json` |
| `opcode_word_bz2_tiny_v1` | syntax opcode preprocessor | 1,000,000 | 275,150 | 273,898 | 1,252 | 2.191184 | true | `results/opcode_word_bz2_tiny_v1/2026-06-08T161413.json` |
| `xml_skel_wordcode_bz2_min_z_v1` | custom candidate | 1,000,000 | 277,140 | 275,444 | 1,696 | 2.203552 | true | `results/xml_skel_wordcode_bz2_min_z_v1/2026-06-08T165120.json` |
| `yellow_tucan_markup_opcode_lzma_v2` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,160 | 289,240 | 920 | 2.31392 | true | `results/yellow_tucan_markup_opcode_lzma_v2/2026-06-08T161753.json` |
| `xml_scaffold__macro_residual__punct_media__lzma_extreme__min__v04` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,171 | 288,221 | 1,950 | 2.305768 | true | `results/xml_scaffold__macro_residual__punct_media__lzma_extreme__min__v04/2026-06-07T163510.json` |
| `xml_scaffold__macro_residual__style_title__lzma_extreme__min__v05` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,173 | 288,197 | 1,976 | 2.305576 | true | `results/xml_scaffold__macro_residual__style_title__lzma_extreme__min__v05/2026-06-07T164405.json` |
| `xml_scaffold__macro_residual__wiki_tokens__lzma_extreme__min__v02` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,322 | 288,465 | 1,857 | 2.30772 | true | `results/xml_scaffold__macro_residual__wiki_tokens__lzma_extreme__min__v02/2026-06-07T155117.json` |
| `xml_scaffold__macro_residual__wiki_layout__lzma_extreme__min__v03` | LZMA/LZMA2 baseline or preprocessor | 1,000,000 | 290,362 | 288,433 | 1,929 | 2.307464 | true | `results/xml_scaffold__macro_residual__wiki_layout__lzma_extreme__min__v03/2026-06-07T155738.json` |

## Top Archive Rows At 1,000,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,961 | 174,395 | 562,566 | 1.39516 | not recorded | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1/2026-06-20T155023.json` |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,961 | 174,396 | 562,565 | 1.395168 | true | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1/2026-06-20T202147.json` |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 737,781 | 174,396 | 563,385 | 1.395168 | true | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1/2026-06-21T013117.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,901 | 174,398 | 562,503 | 1.395184 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T102554.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,974 | 174,398 | 562,576 | 1.395184 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_abovecellguard_match2guard_dualsparseguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T145351.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,734 | 174,399 | 562,335 | 1.395192 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_sparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T012804.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,748 | 174,399 | 562,349 | 1.395192 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-17T210059.json` |
| `cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 1,000,000 | 736,885 | 174,399 | 562,486 | 1.395192 | true | `results/cmix21_text_mmap_paq5_ppmd100m_fxcm2_dualsparseguard_matchguard_stemguard_rcm32_bufthirtysecond_minmaps_v1/2026-06-18T055557.json` |

## Top Score Rows At 250,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `opcode_typed_anchor_bitmix_v1` | syntax opcode preprocessor | 250,000 | 72,800 | 67,959 | 4,841 | 2.174688 | true | `results/opcode_typed_anchor_bitmix_v1/2026-06-08T114728.json` |
| `baseline_bz2` | baseline compressor | 250,000 | 72,824 | 72,658 | 166 | 2.325056 | true | `results/baseline_bz2/2026-06-07T184037.json` |
| `opcode_word_bz2_tiny_v1` | syntax opcode preprocessor | 250,000 | 73,139 | 71,887 | 1,252 | 2.300384 | true | `results/opcode_word_bz2_tiny_v1/2026-06-08T161349.json` |
| `opcode_word_bz2_tiny_k_v1` | syntax opcode preprocessor | 250,000 | 73,145 | 71,887 | 1,258 | 2.300384 | true | `results/opcode_word_bz2_tiny_k_v1/2026-06-08T161449.json` |
| `opcode_word_bz2_tiny_k4_v1` | syntax opcode preprocessor | 250,000 | 73,154 | 71,917 | 1,237 | 2.301344 | true | `results/opcode_word_bz2_tiny_k4_v1/2026-06-08T114828.json` |
| `ppm_residual_shape_pack_v1` | custom candidate | 250,000 | 73,308 | 71,352 | 1,956 | 2.283264 | true | `results/ppm_residual_shape_pack_v1/2026-06-07T183349.json` |
| `opcode_word_bz2_min_deflate_v1` | syntax opcode preprocessor | 250,000 | 73,335 | 71,887 | 1,448 | 2.300384 | true | `results/opcode_word_bz2_min_deflate_v1/2026-06-08T114825.json` |
| `opcode_word_bz2_deflate_v1` | syntax opcode preprocessor | 250,000 | 73,402 | 71,887 | 1,515 | 2.300384 | true | `results/opcode_word_bz2_deflate_v1/2026-06-08T114822.json` |

## Top Archive Rows At 250,000 Bytes

| Program | Mechanism | Scope | Score | Archive | Program | b/B | Determinism | Result |
|---|---|---:|---:|---:|---:|---:|---|---|
| `fx2_timestamp_direct_only_byte_split_extra_page_match_v1` | custom candidate | 250,000 | 428,352 | 44,976 | 383,376 | 1.439232 | not recorded | `results/fx2_timestamp_direct_only_byte_split_extra_page_match_v1/2026-06-07T002058.json` |
| `cmix21_text_mmap_paq5_ppmd2g_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 604,936 | 45,177 | 559,759 | 1.445664 | not recorded | `results/cmix21_text_mmap_paq5_ppmd2g_minmaps_v1/2026-06-14T171759.json` |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 607,743 | 45,178 | 562,565 | 1.445696 | true | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_minmaps_v1/2026-06-20T184307.json` |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 607,744 | 45,178 | 562,566 | 1.445696 | not recorded | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_rcm32_bufsixtyfourth_minmaps_v1/2026-06-20T150203.json` |
| `cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 608,563 | 45,178 | 563,385 | 1.445696 | true | `results/cmix21_text_mmap_paq5_ppmd40m_fxcmidx13div2_fxcmrcm20_rcm32_bufsixtyfourth_ppmdguard_minmaps_v1/2026-06-21T001850.json` |
| `cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_ppmdsq_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 609,030 | 45,178 | 563,852 | 1.445696 | true | `results/cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_ppmdsq_rcm32_bufthirtysecond_minmaps_v1/2026-06-22T162313.json` |
| `cmix21_text_mmap_paq5_ppmd35m_fxcmidx13div2_ppmdsq_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 609,030 | 45,178 | 563,852 | 1.445696 | true | `results/cmix21_text_mmap_paq5_ppmd35m_fxcmidx13div2_ppmdsq_rcm32_bufthirtysecond_minmaps_v1/2026-06-22T131833.json` |
| `cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1` | cmix21 memory-shaped context mixer | 250,000 | 609,449 | 45,178 | 564,271 | 1.445696 | true | `results/cmix21_text_mmap_paq5_ppmd25m_fxcmidx13div2_ppmdguard2_rcm32_bufthirtysecond_minmaps_v1/2026-06-22T192318.json` |
