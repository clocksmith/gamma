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

- Receipts scanned: `104`
- Positive net receipts: `10`
- Promotion-ready shadow receipts: `5`
- Max block regression cap: `0` bytes
- Max online state cap: `64,000,000` bytes
- Best net receipt: `results/streaming_retrieval_shadow/raw32768k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json`
- Best net saved bytes: `433,554`
- Best held-out saved bytes: `445,842`
- Best receipt blockers: `block_regression_within_cap`

## Blocker Counts

| Blocker | Receipts |
|---|---:|
| `alignment_ok` | 21 |
| `block_regression_within_cap` | 45 |
| `complete_block_audit` | 76 |
| `has_heldout` | 7 |
| `positive_heldout` | 73 |
| `positive_net` | 94 |
| `raw_data_source` | 72 |

## Substrate Summary

This separates SRSTC as a standalone raw-byte model from SRSTC as
a correction layer on an existing probability trace.

| Substrate | Receipts | Positive Net | Ready | Best Net | Best Held-out | Best Receipt |
|---|---:|---:|---:|---:|---:|---|
| `streaming_retrieval_raw_shadow_v1 / raw_enwik9_bits_msb` | 32 | 10 | 5 | 433,554 | 445,842 | `results/streaming_retrieval_shadow/raw32768k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_probe/search_250k_stride1_500k_shifthard_p1p650_p2p300/stderr.log` | 18 | 0 | 0 | -12,287 | 1 | `results/streaming_retrieval_shadow/fx2_500k_rawlog_order2_best_band_abstain_sketch_b20000_s8.json` |
| `streaming_retrieval_shadow_v1 / projects/enwiki9/results/fx2_residual_cache/apm1m_500k.tsv` | 22 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/apm1m_120k_train5k_b10000_s16.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/apm1m_500k.tsv` | 29 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/apm1m_120k_train5k_v2_abstain_regret_m128_sketch_b25000_s8.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/apm64k_120k.tsv` | 1 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/apm64k_120k_v2_sketch_b25000_s8.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_cache/manifold_rich_120k.tsv` | 1 | 0 | 0 | -12,288 | 0 | `results/streaming_retrieval_shadow/manifold_rich_120k_v2_sketch_b25000_s8.json` |
| `streaming_retrieval_shadow_v2 / projects/enwiki9/results/fx2_residual_probe/search_250k_stride1_500k_shifthard_p1p650_p2p300/residual_scored.jsonl` | 1 | 0 | 0 | n/a | n/a | `n/a` |

## Top Rows

| Receipt | Net Saved | Held-out Saved | State Bytes | Block Audit | Largest Regression | Ready | Blockers |
|---|---:|---:|---:|---|---:|---|---|
| `results/streaming_retrieval_shadow/raw16384k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 213,375 | 225,663 | 22,400,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw8192k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 99,924 | 112,212 | 22,400,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw4096k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 46,576 | 58,864 | 22,400,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw2048k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 15,982 | 28,270 | 12,800,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw1024k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 1,693 | 13,981 | 12,800,000 | `complete` | 0 | `true` | `none` |
| `results/streaming_retrieval_shadow/raw32768k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json` | 433,554 | 445,842 | 22,400,000 | `complete` | 22.397 | `false` | `block_regression_within_cap` |
| `results/streaming_retrieval_shadow/raw8192k_v1_order2_aggregate_sketch_b640000_s8.json` | 99,924 | 112,212 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw4096k_v1_order2_aggregate_sketch_b640000_s8.json` | 46,576 | 58,864 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw2048k_v1_order2_aggregate_sketch_b640000_s8.json` | 15,982 | 28,270 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw1024k_v1_order2_aggregate_sketch_b640000_s8.json` | 1,693 | 13,981 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b640000_s8.json` | -6,069 | 6,219 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b320000_s8.json` | -7,300 | 4,988 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b160000_s8.json` | -9,174 | 3,114 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b1000000_s8.json` | -9,807 | 2,481 | 12,800,000 | `worst_blocks_only` | 162.928 | `false` | `positive_net, block_regression_within_cap, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b80000_s8.json` | -10,512 | 1,776 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b40000_s8.json` | -11,322 | 966 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b20000_s8.json` | -11,778 | 510 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw512k_v1_order2_aggregate_sketch_b10000_s8.json` | -12,024 | 264 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw256k_v1_order2_aggregate_sketch_b10000_s8.json` | -12,176 | 112 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |
| `results/streaming_retrieval_shadow/raw256k_v1_order2_aggregate_sketch_b5000_s8.json` | -12,231 | 57 | 12,800,000 | `worst_blocks_only` | 0 | `false` | `positive_net, complete_block_audit` |

## Readout

- A positive net receipt can justify more shadow work.
- A promotion-ready receipt requires complete block evidence before any compressor integration.
- Existing receipts without full block rows should be regenerated with complete block diagnostics before packaging.
