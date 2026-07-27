# Streaming Retrieval Block Regime Audit

This is offline teacher evidence, not an admissible decoder feature table.

- Source receipt: `results/streaming_retrieval_shadow/raw65536k_v1_order2_aggregate_sketch_b640000_s8_complete_blocks.json`
- Block bytes: `16,384`
- Regression blocks: `3`
- Total visible regression: `42.305` bytes
- Teacher manifest rows: `4,000`
- Teacher manifest: `docs/streaming_retrieval_block_teacher_manifest.jsonl`
- Source recovery: preserved teacher manifest `docs/streaming_retrieval_block_teacher_manifest.jsonl` (`4,000` rows)

| Label | Block | Gain Bytes | Nearby Titles | Links | Templates | URLs | Headings | Pages |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| `regression` | 1491 | -22.397 | Base pair; Baltimore Ravens; British National Party | 112 | 0 | 25 | 13 | 0 |
| `regression` | 2534 | -13.628 | Cofinality; Chibi-Usa; Citadel; Chainmail | 140 | 2 | 10 | 8 | 2 |
| `regression` | 3316 | -6.279 | Divination; Doctor Strangelove, or How I Learnt to Stop Worrying and Love the Bomb; Diet of Nuremberg; Dr. Strangelove or: How I Learned to Stop Worrying and Love the Bomb | 81 | 3 | 1 | 8 | 0 |
| `weak_positive_control` | 1013 | 1.750 | Durrani Empire; Aimak; Arcturus; Absinthe | 132 | 0 | 9 | 8 | 0 |
| `weak_positive_control` | 302 | 6.458 | Apartheid; Azerbaijan/History | 139 | 2 | 3 | 9 | 0 |
| `weak_positive_control` | 1427 | 8.157 | Boeing 767; Bill Walsh (football coach) | 101 | 7 | 2 | 7 | 0 |

## Readout

The regressions are not confined to one XML delimiter mode. They include
long prose spans with dense headings and links as well as a page-boundary
block. Use these labels for teacher discovery, but distill only causal
prefix rules and compare them against the block-posterior loss router.
The JSONL manifest exposes all block offsets and continuous gain labels
with one regression in each contiguous train/validation/test split.

Claim boundary: full-block labels, titles, headings, and counts are teacher-only; a final router may use only prefix checkpoints or a distilled decoder-rebuilt rule validated by exact replay
