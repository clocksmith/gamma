# Streaming Retrieval Receipt Audit

This report audits cached SRSTC shadow receipts. It is not a compressor
benchmark and does not mutate the active cmix21 runner.

Promotion rule:

```text
positive_net_shadow is evidence, not promotion.
promotion requires held-out gain, no alignment warning, bounded state,
and complete block-regression evidence.
```

## Summary

- Receipts scanned: `136`
- Positive net receipts: `15`
- Promotion-ready shadow receipts: `9`
- Max block regression cap: `0` bytes
- Max online state cap: `64,000,000` bytes
- Best net receipt: `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks_blockposterior_v1.json`
- Best net saved bytes: `900,464`
- Best held-out saved bytes: `916,540`
- Best receipt blockers: `none`

## Objective Selection

This is the SRSTC generator-verifier-selector loop in receipt form:
candidate receipts are generated separately, verified by held-out
same-coder bytes, then selected by net bytes after counted costs
and promotion blockers.

- Current winner score: `110,793,128`
- Best forecast score: `110,181,114`
- Target score: `109,500,000`
- Public-record gap to target: `1,293,128` bytes
- Forecast gap to target: `681,114` bytes
- Recommended action: `package_promotion_ready_shadow_piece`
- Reason: `a promotion-ready shadow receipt closes the forecast-to-target byte gap`
- Best target-closing receipt: `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks_blockposterior_v1.json`
- Target-closing net saved bytes: `900,464`
- Forecast gap remaining after best target-closing receipt: `-219,350`
- Target-closing blockers: `none`
- Best promotion-ready fallback: `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks_blockposterior_v1.json`
- Ready fallback net saved bytes: `900,464`
- Forecast gap remaining after ready fallback: `-219,350`

| Receipt | Net Saved | Forecast Gap Remaining | Ready | Largest Regression | Blockers |
|---|---:|---:|---|---:|---|
| `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks_blockposterior_v1.json` | 900,464 | -219,350 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 884,774 | -203,660 | `false` | 22.397 | `block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw16384k_richkeys_cap300k_v1.json` | 260,560 | 420,554 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw16384k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 213,375 | 467,739 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw8192k_richkeys_cap300k_v1.json` | 125,529 | 555,585 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw8192k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 99,924 | 581,190 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw4096k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 46,576 | 634,538 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw2048k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 15,982 | 665,132 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw1m_richkeys_cap300k_v1.json` | 4,418 | 676,696 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw1024k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 1,693 | 679,421 | `true` | 0 | `none` |
| `results/streaming_retrieval_shadow/raw32768k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 433,554 | 247,560 | `false` | 22.397 | `block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw8192k_v1_order2_aggregate_sketch_b640000_s8.json` | 99,924 | 581,190 | `false` | 0 | `complete_block_audit` |

## Blocker Counts

| Blocker | Receipts |
|---|---:|
| `alignment_ok` | 26 |
| `block_regression_within_cap` | 64 |
| `complete_block_audit` | 76 |
| `has_heldout` | 7 |
| `positive_heldout` | 79 |
| `positive_net` | 121 |
| `raw_data_source` | 78 |

## Substrate Summary

This separates SRSTC as a standalone raw-byte model from SRSTC as
a correction layer on an existing probability trace.

| Substrate | Receipts | Positive Net | Ready | Best Net | Best Held-out | Best Receipt |
|---|---:|---:|---:|---:|---:|---|
| `streaming_retrieval_raw_shadow_v1 / raw_enwik9_bits_msb` | 58 | 15 | 9 | 900,464 | 916,540 | `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks_blockposterior_v1.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_probe/search_250k_stride1_500k_shifthard_p1p650_p2p300/stderr.log` | 19 | 0 | 0 | -12,287 | 1 | `results/streaming_retrieval_shadow/fx2_500k_rawlog_order2_best_band_abstain_sketch_b20000_s8.json` |
| `streaming_retrieval_shadow_v1 / projects/enwiki9/results/fx2_residual_cache/apm1m_500k.tsv` | 22 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/apm1m_120k_train5k_b10000_s16.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/apm1m_500k.tsv` | 29 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/apm1m_120k_train5k_v2_abstain_regret_m128_sketch_b25000_s8.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/apm1m_full_4805936.tsv` | 4 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/fx2_apm1m_cache_rowfeatures_v1_order2_best_band_abstain_sketch_b20000_s8_rows4805936.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/apm64k_120k.tsv` | 1 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/apm64k_120k_v2_sketch_b25000_s8.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/manifold_rich_120k.tsv` | 1 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/manifold_rich_120k_v2_sketch_b25000_s8.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_probe/residual_apm_1m_mode_charclass_b050/stderr.log` | 1 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/residual_apm_1m_mode_charclass_b050_row_rich_aggregate_b20000.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_probe/search_250k_stride1_500k_shifthard_p1p650_p2p300/residual_scored.jsonl` | 1 | 0 | 0 | n/a | n/a | `n/a` |

## Top Rows

| Receipt | Net Saved | Held-out Saved | State Bytes | Block Audit | Largest Regression | Ready | Blockers |
|---|---:|---:|---:|---|---:|---|---|
| `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks_blockposterior_v1.json` | 900,464 | 916,540 | 22,400,032 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw16384k_richkeys_cap300k_v1.json` | 260,560 | 272,848 | 33,600,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw16384k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 213,375 | 225,663 | 22,400,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw8192k_richkeys_cap300k_v1.json` | 125,529 | 137,817 | 33,600,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw8192k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 99,924 | 112,212 | 22,400,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw4096k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 46,576 | 58,864 | 22,400,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw2048k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 15,982 | 28,270 | 12,800,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw1m_richkeys_cap300k_v1.json` | 4,418 | 16,706 | 33,600,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw1024k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 1,693 | 13,981 | 12,800,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 884,774 | 897,062 | 22,400,000 | `complete` | 22.397 | `false` | `block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw32768k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 433,554 | 445,842 | 22,400,000 | `complete` | 22.397 | `false` | `block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw8192k_v1_order2_aggregate_sketch_b640000_s8.json` | 99,924 | 112,212 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw4096k_v1_order2_aggregate_sketch_b640000_s8.json` | 46,576 | 58,864 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw2048k_v1_order2_aggregate_sketch_b640000_s8.json` | 15,982 | 28,270 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw1024k_v1_order2_aggregate_sketch_b640000_s8.json` | 1,693 | 13,981 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b640000_s8.json` | -6,069 | 6,219 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b320000_s8.json` | -7,300 | 4,988 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw1m_copy_no_regret_logodds_mdl_v1.json` | -8,123 | 4,165 | 48,000,000 | `complete` | 2.404 | `false` | `positive_net, block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw1m_attribution_copy_current_cap300k_v1.json` | -8,161 | 4,127 | 40,000,000 | `complete` | 2.404 | `false` | `positive_net, block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw1m_attribution_nocopy_current_cap300k_v1.json` | -8,175 | 4,113 | 33,600,000 | `complete` | 2.404 | `false` | `positive_net, block_regression_within_cap` |

## Readout

- A positive net receipt can justify more shadow work.
- A promotion-ready receipt requires complete block evidence before any compressor integration.
- Existing receipts without full block rows should be regenerated with complete block diagnostics before packaging.
