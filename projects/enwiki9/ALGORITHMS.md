# enwiki9 Algorithm Reference

This document explains the custom compression algorithms in this folder and how
to read their benchmark results. It is intentionally evidence-first: rows marked
`MEASURED` come from `results/<program_id>/*.json` with `roundtrip_ok: true`.
Rows marked `SOURCE-ONLY` describe code that exists but does not have a matching
benchmark artifact in this checkout.

The main README explains the Hutter score math and run protocol. This file
answers the next question: what each algorithm is actually doing, which ones are
currently strongest, and what each measurement proves.

## Classification

The programs in this folder fall into three different classes. They should not
be compared without naming the class.

| Class | Meaning | Examples |
|---|---|---|
| LZMA preprocessor | Reversible transform first, then a strong LZMA/LZMA2 back-end. | `schema_title_streams_lzma2_1g_v1`, `ast_opcode_lzma_v1`, `blue_dolphin_tree_macro_v1` |
| Custom entropy back-end | The archive is produced by in-repo prediction, match coding, and arithmetic/range coding rather than by LZMA or cmix. | `typed_anchor_chain_ppmc_v1`, `yellow_tucan_structural_range_v5`, `purple_parrot_nncp_v1` |
| cmix/fx2 wrapper lane | Uses an external cmix/fx2-class substrate plus in-repo wrappers or structural transforms. | `fx2_geometry_sort_dictcmix_xz_v1`, `fx2cmix_wrapped_v1` |

The LZMA and cmix wrapper lanes usually win on score because their back-ends are
much stronger. The custom entropy back-end lane is still valuable because it
tests whether the repository's structural ideas can become a compressor rather
than only a preprocessor.

## Benchmark Snapshot

Audited rows from `results/`, grouped by what they prove:

| Program | Class | Scope | S | Archive bytes | Program bytes | b/B | Evidence |
|---|---|---:|---:|---:|---:|---:|---|
| `schema_title_streams_lzma2_1g_v1` | LZMA preprocessor | 1 GB | 196,474,397 | 196,456,145 | 18,252 | 1.571649 | `results/schema_title_streams_lzma2_1g_v1/2026-05-24T164441.json` |
| `ast_opcode_lzma_v1` | LZMA preprocessor | 1 GB | 196,775,973 | 196,773,596 | 2,377 | 1.574189 | `results/ast_opcode_lzma_v1/2026-05-09T141616.json` |
| `xz_lzma2_1g` | Raw LZMA2 baseline | 1 GB | 197,822,756 | 197,822,248 | 508 | n/a | `results/xz_lzma2_1g/2026-05-09T102756.json` |
| `typed_anchor_chain_ppmc_v1` | Custom entropy back-end | 1 GB | 227,854,414 | 227,850,747 | 3,667 | 1.822806 | `results/typed_anchor_chain_ppmc_v1/2026-05-11T175244.json` |
| `fx2_geometry_sort_dictcmix_xz_v1` | cmix/fx2 wrapper lane | 100 MB | 15,041,659 | 14,857,781 | 183,878 | 1.188622 | `results/fx2_geometry_sort_dictcmix_xz_v1/2026-06-03T172741.json` |
| `yellow_tucan_structural_range_v5` | Custom range coder | 1 MB | 462,035 | 455,242 | 6,793 | 3.641936 | `results/yellow_tucan_structural_range_v5/2026-05-09T153207.json` |

Current read:

- Best measured full-corpus score in this repo: `schema_title_streams_lzma2_1g_v1`.
- Best measured full-corpus custom entropy back-end: `typed_anchor_chain_ppmc_v1`.
- Best measured small parser-state range coder: `yellow_tucan_structural_range_v5`.
- `purple_parrot_nncp_v1` and `blue_dolphin_tree_macro_v1` have source code and lane notes, but no matching result JSON in this checkout. Do not present them as measured benchmark wins until those artifacts exist.

## How To Read A Row

Use `S` to decide the contest result. Use `b/B` to discuss the archive model.

`S = archive bytes + counted program bytes`

`b/B = archive bytes * 8 / input bytes`

Slice rows are diagnostic. A 1 MB or 100 MB prefix result can validate an idea,
but it is not a substitute for a full 1 GB row. The README's scope-discipline
section explains why prefix results do not scale linearly on `enwik9`.

## `schema_title_streams_lzma2_1g_v1`

Status: `MEASURED`, best full-corpus score in the current result set.

Class: LZMA preprocessor.

What it does:

1. Parses page-level XML and wikitext structure into typed streams.
2. Separates high-regularity fields from prose-like payloads.
3. Applies schema-specific word and atom coding where it helps.
4. Compresses the packed streams with LZMA2.

Why it wins in this repo:

- It keeps the transform reversible while giving LZMA2 cleaner local patterns.
- It spends more source bytes than `ast_opcode_lzma_v1`, but the archive gain
  more than pays for that at full-corpus scope.
- It is a preprocessor result, not proof that the custom entropy models have
  beaten LZMA-class back-ends.

Evidence:

- `S = 196,474,397` on the full 1 GB corpus.
- Beats raw `xz_lzma2_1g` by 1,348,359 score bytes at the same scope.
- `roundtrip_ok: true`.

## `ast_opcode_lzma_v1`

Status: `MEASURED`, second-best full-corpus score in the current result set.

Class: LZMA preprocessor.

What it does:

1. Rewrites repeated XML and MediaWiki syntax into compact opcodes.
2. Preserves local byte order instead of splitting into many independent files.
3. Feeds the transformed byte stream into an LZMA2 back-end.

Why it matters:

- It is the small, clean baseline for structural preprocessing.
- Its counted program is only 2,377 bytes, so it remains competitive even when
  its transform is less expressive than the schema-stream approach.

Evidence:

- `S = 196,775,973` on the full 1 GB corpus.
- Beats raw `xz_lzma2_1g` by 1,046,783 score bytes at the same scope.
- `roundtrip_ok: true`.

## `typed_anchor_chain_ppmc_v1`

Status: `MEASURED`, best full-corpus custom entropy back-end in this checkout.

Class: custom entropy back-end.

This program is easy to misread because `program.py` is a tiny loader that
decompresses sibling file `p`. That LZMA use is only source-code packing for the
counted decompressor. The archive returned by `compress()` is produced by the
custom coder inside `p`.

Mechanism:

1. `GST` tracks lightweight document state: XML field, brace/bracket mode,
   recent bytes, page class, slot type, column bucket, and word tail.
2. `PPM` encodes literal bytes with escape/exclusion over recent byte contexts.
3. Raw match mode finds LZ77-style matches by recent 4-byte hashes.
4. Chain match mode finds previous positions that shared a structural key from
   `GST.keys()`, then copies bytes from that semantically similar history.
5. A token model estimates event costs for literal, raw match, and chain match.
6. The encoder emits a match only when estimated gain is greater than 0.5 bits;
   otherwise it emits a literal through PPM.
7. Decoder rebuilds the same parser state, histories, and token models while it
   decodes, so no side tables are stored in the archive.

Why it matters:

- It is not a wrapper around LZMA or cmix for the compressed data.
- It proves that structural anchor-chain matches can scale to the full corpus
  with a valid roundtrip.
- Its b/B is behind the LZMA preprocessors, but it is the strongest measured
  in-repo custom back-end at full scope.

Evidence:

- `S = 227,854,414` on the full 1 GB corpus.
- `program_stats.events = [299180255, 37531437, 10326728]`, meaning the stream
  used literals, raw matches, and chain matches rather than a single fallback.
- `roundtrip_ok: true`.
- `determinism: null`, so this row is not yet a single-host determinism claim.

Main limits:

- The literal model is PPM-style, not a cmix-class mixer.
- Chain indices are selected from bounded recent lists, so old structural
  repetition is only captured when it remains in the chain window.
- Full cross-host determinism still needs an explicit reproduced artifact.

## `yellow_tucan_structural_range_v5`

Status: `MEASURED`, best small structural range-coder result in the yellow_tucan
line.

Class: custom range coder.

Mechanism:

1. A byte-level arithmetic coder writes one symbol at a time.
2. `State` tracks a compact parser state: XML-ish mode, entity mode, bracket
   depth, brace depth, digit flag, and the two previous bytes.
3. `Predictor` maintains three model families:
   - global order-0 byte counts,
   - previous-byte order-1 models,
   - structural-context models keyed by `State.key()`.
4. At each byte, the predictor selects the highest-context model that has enough
   training data. It does not emit an explicit PPM escape symbol in v5; all
   models start with nonzero counts for all 256 bytes.
5. After coding a byte, it updates the selected model plus the lower-order and
   structural models needed for later selections.

What the benchmark proves:

- Parser state is a real signal at 1 MB: v5 archive bytes are 455,242 versus
  460,812 for `yellow_tucan_range_order_v1`, a 5,570-byte archive gain at the
  same scope.
- The source-size reduction from v2 to v5 improves `S` without changing archive
  behavior.

What it does not prove:

- It does not compete with LZMA or Bzip2 at the same 1 MB scope.
- It is a context selector, not a neural mixer and not a full PPM-C
  escape/exclusion implementation.
- It has no full-corpus result in this checkout.

Evidence:

- `S = 462,035` on a 1 MB prefix.
- `roundtrip_ok: true`.
- Single-host determinism is present in the result JSON.

## `purple_parrot_nncp_v1`

Status: `SOURCE-ONLY` in this checkout. There is source code and lane
documentation, but no `results/purple_parrot_nncp_v1/*.json` artifact here.

Class: custom neural entropy back-end.

Mechanism:

1. Encoder and decoder initialize the same char-level LSTM from seed `0x5EED`.
2. For each byte, both sides run `prev_byte -> LSTM -> softmax`.
3. Softmax probabilities are converted to integer arithmetic-coder counts with
   fixed precision.
4. Encoder codes the true byte; decoder recovers the byte from the same
   interval.
5. Both sides run the same one-step SGD update after the byte is known.

Why it matters:

- It tests the NNCP-style idea that online learning can be free in Hutter score
  because the model state is reproduced by the decoder rather than shipped.
- The implementation has zero pretrained weights and counts only the LSTM code
  plus NumPy dependency metadata.

Presentation rule:

- Present this as an architecture and lockstep-protocol reference until a result
  JSON exists.
- Do not claim the 1 MB score previously shown in chat unless the corresponding
  `results/purple_parrot_nncp_v1/*.json` file is added or regenerated.

Main limits:

- v1 backpropagates one byte at a time with no truncated BPTT.
- Float32 NumPy can be same-host deterministic but is not a cross-architecture
  contest proof.
- Throughput is dominated by sequential per-byte matrix operations.

## `blue_dolphin_tree_macro_v1`

Status: `SOURCE-ONLY` in this checkout. The source exists, but there is no
`results/blue_dolphin_tree_macro_v1/*.json` artifact here.

Class: LZMA preprocessor.

Mechanism:

1. Scans MediaWiki templates of the form `{{name|arg1|arg2}}`, including nested
   brace depth handling.
2. Parses the template into a name plus argument byte strings.
3. Computes a stable shape hash from template name, sorted argument keys, and
   argument count. Argument values remain literal.
4. Rewrites eligible templates as rule definitions or rule references.
5. Compresses the rewritten stream with LZMA.
6. Decoder rebuilds templates from rule metadata plus literal argument bytes.

Implementation review:

- Earlier lane notes described a true empirical savings gate. The current
  source and metadata now describe the implemented behavior directly.
- The implementation selects `eligible` shapes by `count >= MIN_FREQ`.
  It does not compute a per-shape raw-stream savings gate before admission.
- That is the key implementation limit: present it as frequency-gated template
  macro substitution unless the code is changed to compute and enforce savings.

Presentation rule:

- Present this as a parsed-template macro prototype, not as a measured 100 MB
  result, until a result JSON exists.
- If a benchmark row is added later, include scope, `S`, archive bytes, program
  bytes, b/B, `roundtrip_ok`, and the exact result path.

Main limits:

- LZMA may already capture many repeated template byte patterns, so explicit
  macro metadata can lose unless the admitted shapes amortize their rule bytes.
- Shape hashing ignores argument values by design; this is correct for skeleton
  reuse but means argument payloads still dominate many templates.
- The frequency-only gate can admit shapes that do not reduce the pre-LZMA
  stream size.

## What To Improve Next

Documentation fixes:

1. Keep benchmark tables artifact-backed. If there is no result JSON, mark the
   row `SOURCE-ONLY`.
2. Separate full-corpus rows from prefix rows.
3. Separate LZMA/cmix wrapper wins from custom entropy back-end wins.
4. For each algorithm, state the decoder contract: what state is rebuilt, what
   bytes are stored, and what external back-end is used.

Algorithm fixes:

1. Add a true savings gate to `blue_dolphin_tree_macro_v1` if the tree-macro
   lane is promoted beyond frequency-gated admission.
2. Add result artifacts for `purple_parrot_nncp_v1` and
   `blue_dolphin_tree_macro_v1` before reporting them in summary tables.
3. For `typed_anchor_chain_ppmc_v1`, add a same-host determinism result and a
   cross-host reproduction row if it is meant to be contest-grade.
4. For `yellow_tucan`, the next real model improvement is not more prose around
   v5. It is a stronger backoff or mixer that can beat v5 on the same 1 MB
   prefix with `roundtrip_ok` and determinism recorded.
