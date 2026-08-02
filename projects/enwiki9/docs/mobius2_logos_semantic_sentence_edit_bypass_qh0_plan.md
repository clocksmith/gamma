# MÖBIUS-2 LOGOS semantic sentence edit-bypass QH0

Proposal: `mobius2_logos_semantic_sentence_edit_bypass_v1`.

Candidate: `mobius2_logos_semantic_sentence_edit_bypass_qh0_v1`.

## Hypothesis

Embedding retrieval over complete sentence-like Wikipedia spans identifies
earlier, semantically related WRT spans whose exact reusable fragments are
cheaper to describe as one prior-span reference plus alternating COPY and
LITERAL regions than to code on the exact JANUS-plus-quotient trajectory.

This is not a semantic logit calibrator, a prompted ontology, a page-level
prototype retry, or another static prose-token table.  It changes the coded
operation at clause scale.  Every copied byte is reconstructed from already
decoded WRT and is subsequently visible to the unchanged parent update path.
The trace gate uses the frozen joint P1 rows as the state-preservation stand-in.

EmbeddingGemma is an encoder-side search instrument only.  Its weights,
tokenizer, floating-point execution, and nearest-neighbor computation are not
part of the decoder.  The chosen prior span and exact edit program are
transmitted and counted.  The decoder needs only the finite copy program and
the parent predictor.

## Frozen population

Use the canonical 10M WRT store and the final complete page ending before raw
byte 1,000,000:

```text
complete pages        171
raw-equivalent bytes  984,835
WRT bytes             591,230
P1 rows               4,729,840
```

Pages are split chronologically 60/20/20 into development, selection, and
sealed confirmation.  Sentence-like spans are formed only inside page text,
at `.`, `!`, `?`, `;`, or newline boundaries.  After trimming whitespace, an
eligible span has 6 through 128 WRT emission groups, 24 through 512 raw bytes,
at least 12 ASCII letters, and no XML or prohibited template/reference shell.
The boundaries and filters are frozen before the result is read.

## Frozen semantic search

Use the local, hash-recorded `google/embeddinggemma-300m` snapshot with:

```text
prompt             task: clustering | query:
maximum tokens     128
pooling            attention-mask mean
projection         shipped 768 -> 3072 -> 768 dense modules
dimension          first 128 MRL coordinates, renormalized
serialization      round-to-nearest signed int16
neighbors          eight earlier eligible spans
```

Run under the repository ROCm environment with
`HSA_OVERRIDE_GFX_VERSION=11.0.0`.  Before model inference, record Python,
PyTorch, HIP, device, architecture, a real GPU matrix-product hash, and input
model hashes.  Build the quantized embedding blob twice and require byte
identity.

The semantic candidate set for target span `i` is its top eight cosine
neighbors among spans `0..i-1`; similarity ties choose the lower source index.
Only the chosen source reference is transmitted.  The decoder never repeats
the embedding search.

## Exact edit program

For each candidate source, find exact WRT matches at every target byte.  One
dynamic program may alternate multiple copies and literal holes against that
single source span:

```text
SPAN(target_start, target_length, source_start, source_length)
COPY(target_offset, source_offset, length)
LITERAL(all uncovered target bytes)
```

The minimum copy is eight WRT bytes.  Canonical ULEB128 integers and fixed
little-endian counts pay target/source offsets, lengths, copy commands, plan
counts, framing, and termination.  Dynamic programming maximizes rounded
Q256 parent codelength displaced minus actual command bytes.  A span falls
back to literal when no positive program exists.  All chosen target spans are
nonoverlapping and every source ends before its target begins.

The residual payload is an actually terminated 32-bit range stream containing
all truth bits outside copied intervals.  Decoding must reproduce the complete
WRT prefix.  For the official inverse check, replace the receipt-bound prefix
in the full canonical WRT store with the reconstructed prefix, append the
unchanged receipt-bound suffix, and require the exact 10M raw hash.  This
proves the prefix reconstruction but does not turn QH0 into a constructive
10M archive.

## Controls

```text
P0   exactly terminated joint-P1 prefix parent
LEX  eight earlier spans from a fixed hashed lexical bag-of-words signature
SEM  eight earlier spans from the frozen semantic embedding
ROT  SEM neighbor identities shifted forward by a causal lag of 31 spans
```

LEX, SEM, and ROT use identical edit search, command format, literal fallback,
range coder, and opportunity count.  ROT never references a future span.

## Gate

At this population, 3,000 B/M requires at least 2,955 exact bytes after all
candidate framing and commands.  Promotion requires:

```text
joint antecedent and all input hashes             exact
real ROCm matrix product                          pass
repeated quantized embedding blob                 byte-identical
all source spans                                  strictly prior
all commands                                      canonical and decodable
all residual arithmetic streams                   exact
complete prefix WRT reconstruction                exact
full-store official raw inverse                   exact
second candidate archives                         byte-identical

SEM development gain                              positive
SEM selection gain                                positive
SEM sealed-confirmation gain                      positive
SEM gain over joint                               >= 3,000 B/M
SEM total                                         < LEX total
SEM total                                         < ROT total
```

A pass authorizes one canonical 10M replay with the frozen representation.  It
does not authorize native integration or change the forecast.

A valid miss retires this exact sentence segmentation, EmbeddingGemma prompt
and projection, eight-neighbor semantic search, one-prior-span edit program,
minimum copy length, lexical control, and lag-31 null.  Do not sweep prompt,
embedding dimension, neighbor count, copy length, sentence width, or retrieval
model.  A successor must change the coded event or information source.

## Claim boundary

QH0 is an exact, zero-score-credit representation ceiling.  The encoder-side
semantic model and implementation are supplied free, while all decoder-visible
commands and arithmetic bytes are paid.  Predictor-state hashes, a counted
native decoder, source package, larger-scope transfer, and a full-1G score
remain unproved.  Forecast remains `109,389,323` bytes and verified full-1G
score remains unknown.
