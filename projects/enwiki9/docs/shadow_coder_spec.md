# Shadow Coder And Residual/SSE Specification

This document defines the non-heavy residual/SSE work that can proceed while a
cmix21 gate owns `/tmp/enwiki9-heavy.lock`. It must not launch another
compressor benchmark or mutate the active candidate source.

## Goal

Measure whether causal structural state can improve a mature compressor's final
probability estimate enough to pay for its implementation bytes.

The pass condition is MDL, not intuition:

```text
held_out_shadow_saved_bytes > added_code_bytes + added_table_bytes
```

## Required Log Fields

The passive probability logger should emit one record per predicted bit:

```text
byte_offset
bit_position
base_probability_integer
true_bit
parser_state_id
block_id
page_id_or_page_counter
```

Optional fields:

```text
xml_mode
wiki_mode
template_depth_bucket
url_state
table_state
list_state
numeric_state
title_prose_ref_phase
line_class
recent_token_class
```

The logger must not change the compressed archive when disabled or when running
in observation mode.

## Trace Format V1

Use JSONL so a shadow scorer can stream without loading the whole trace:

```json
{"trace_version":"fx2_shadow_trace_v1","record_type":"header","compressor_id":"","candidate_id":"","scope_bytes":0,"data_sha256":"","probability_scale":"uint16_0_4095","state_schema_hash":"","split_policy":"block_modulo_v1"}
{"record_type":"bit","seq":0,"byte_offset":0,"bit_position":0,"base_probability_integer":2048,"true_bit":0,"parser_state_id":0,"block_id":0,"page_id_or_page_counter":0,"split":"train"}
```

Required header fields:

```text
trace_version
compressor_id
candidate_id
scope_bytes
data_sha256
probability_scale
state_schema_hash
split_policy
```

Required bit-record fields:

```text
seq
byte_offset
bit_position
base_probability_integer
true_bit
parser_state_id
block_id
page_id_or_page_counter
split
```

Rules:

- `seq` increases by exactly one for each predicted bit.
- `byte_offset` must equal `seq // 8` when the trace covers every bit.
- `bit_position` uses the compressor's actual bit order and must be documented
  in the header if it is not high-bit-first.
- `base_probability_integer` must be the exact probability consumed by the
  arithmetic coder or an explicitly named pre-SSE probability.
- probability clamp behavior must be named in the header and reproduced by the
  shadow coder.
- `true_bit` must match the input corpus byte at `byte_offset` and
  `bit_position`.
- `split` must be assigned from byte/block coordinates, not from outcome bits.
- `state_schema_hash` must change whenever parser-state definitions change.
- Observation mode must produce byte-identical archive output versus the same
  compressor with logging disabled.

## Trace Sanity Checks

Before training any residual table from a trace, run these checks:

| Check | Failure meaning |
|---|---|
| `seq` is contiguous from zero | Missing or duplicated probability event. |
| `byte_offset, bit_position` reconstruct the same `true_bit` as the corpus | Trace is not aligned to the coded stream. |
| all probabilities are inside the coder's legal clamp range | Shadow coder cannot reproduce archive-safe probabilities. |
| observed bit order matches the declared bit order | Residual keys are learned against the wrong target. |
| observation-mode archive hash matches logging-disabled archive hash | Logger changed the compressor state or output. |
| train/held-out split is independent of `true_bit` and residual sign | Evaluation leaks outcome information. |

If any sanity check fails, the trace is a debugging artifact only. Do not
create residual score rows from it.

## Safe Causal States

A state is safe only if it is a deterministic function of already decoded bytes:

```text
state_t = f(bytes_0_to_t_minus_1)
```

Allowed examples:

- current XML mode;
- current Wiki/text mode;
- template depth bucket;
- URL mode;
- table/list mode;
- numeric/date mode;
- title/prose/reference phase after the boundary has been decoded;
- page-local counters accumulated so far;
- move-to-front rank of reference names already seen;
- recent title tokens already decoded.

Forbidden examples:

- final current-page length before the page is complete;
- final link count for the current page before it is complete;
- future section headings;
- future template schema summaries;
- offline embedding cluster IDs unless the cluster rule is shipped and counted
  or recomputable without future bytes.

## Block Validation

Do not accept a correction because one prefix improves. Split evaluation into
blocks and record:

```text
base_bits_block
candidate_bits_block
delta_bits_block = base_bits_block - candidate_bits_block
```

Promotion requires:

- positive total held-out delta after code/table cost;
- no large block regressions;
- similar behavior across page regimes;
- exact arithmetic-coder byte count, not only log-loss projection.

## Constructive Residual Promotion Gate

A residual/SSE row is promotable only when all of these are true:

1. The base trace passed every trace sanity check.
2. The corrected probability stream is encoded by the same finite-precision
   arithmetic-coder model that the candidate would ship.
3. The receipt reports exact `base_shadow_bytes`,
   `candidate_shadow_bytes`, `added_code_bytes_estimate`, and
   `added_table_bytes`.
4. `net_saved_bytes = base_shadow_bytes - candidate_shadow_bytes -
   added_code_bytes_estimate - added_table_bytes` is positive on held-out
   blocks.
5. The largest losing block is bounded and explained by content class.
6. The correction is causal and deterministic from already-decoded bytes.
7. The implementation plan names the exact C++/Python files and tables that
   would be counted in the decompressor ledger.

Rows that save shadow bytes but fail any item above stay labeled
`positive_shadow_only`. They can guide research, but they cannot be promoted
to the active Hutter proof lane.

## Candidate Corrections

First corrections should be tiny:

- outer SSE bucket from `base_probability_integer` plus one causal mode;
- APM-style correction table with bounded entries;
- deterministic expert router using causal past loss only;
- streaming retrieval mixer using deterministic sketches and history-derived
  continuation tables;
- small I-SSA bucket as an additional coordinate, not a replacement model.

Avoid:

- hard probability masks;
- broad primary context hash mutation;
- stream rewriting;
- future-derived page features;
- large static side tables.

## First State-Family Queue

Evaluate state families in this order so regressions are attributable:

| Family | Coordinates | Why first | Promotion threshold |
|---|---|---|---|
| probability calibration control | `p_bucket, bit_position` | Establishes shadow-coder parity and table overhead. | Positive held-out bytes after counted table bytes. |
| character-class mode | `p_bucket, bit_position, recent_token_class` | Cached rows show small positive signal. | Positive held-out bytes across several blocks. |
| XML/wiki mode | `p_bucket, bit_position, xml_mode, wiki_mode` | Directly targets structural boundaries without primary hash changes. | Beats the control and avoids block regressions. |
| template-depth bucket | `p_bucket, bit_position, template_depth_bucket` | Tests nested template structure with bounded cardinality. | Positive held-out bytes and bounded table size. |
| streaming retrieval mixer | `base_probability, current_sketch, retrieved_continuation_distribution` | Tests cosine-style similarity as a deterministic history-derived probability source. | Positive held-out net bytes after counted code/table cost and bounded block regressions. |
| I-SSA bucket | `p_bucket, bit_position, issa_bucket` | Robust parser alternative for malformed markup. | Beats explicit parser buckets or proves lower code/table cost. |
| MWCC router | `p_bucket, bit_position, causal_best_expert` | Tests expert routing without transmitted tokens. | Net held-out bytes after expert code cost. |

Do not combine families until each single-family row has a receipt. Combination
search without attribution recreates the earlier parameter-churn problem.

Current compact XML/Wiki screen result:

```text
receipt: results/fx2_residual_probe/fx2_xml_residual_screen_v1/receipt.json
best key: mode_char
held-out saved bytes: 5
net held-out bytes after code estimate: -6,139
promotion: no native gate; design a stronger target-substrate mechanism first
```

## Receipt Template

```json
{
  "candidate": "",
  "base_trace": "",
  "scope_bytes": null,
  "train_blocks": [],
  "heldout_blocks": [],
  "base_shadow_bytes": null,
  "candidate_shadow_bytes": null,
  "shadow_saved_bytes": null,
  "added_code_bytes_estimate": null,
  "added_table_bytes": null,
  "trace_version": "fx2_shadow_trace_v1",
  "state_schema_hash": "",
  "split_policy": "",
  "block_delta_bytes": [],
  "largest_block_regression_bytes": null,
  "net_saved_bytes": null,
  "causal_states": [],
  "forbidden_state_audit_passed": false,
  "archive_byte_parity_with_logging_disabled": false,
  "verdict": "incomplete"
}
```
