# NNCP v3.3 ROCm constructive 65,536-symbol headroom Q1

Proposal and candidate:
`nncp_v33_rocm_constructive_65536_headroom_q1_v1`.

## Authorization

The causal-replay Q0 passed on one complete 2,048-symbol update block. Two
encoders and an independently seeded model decoder emitted identical branch
frequencies, archives, decoded symbols, post-update model hashes, and losses.
The official inverse was exact and peak allocated ROCm memory was
7,229,241,344 bytes.

## Frozen population and layout

Use exactly the first 65,536 symbols of the receipt-bound official NNCP
preprocessed stream. Treat them as one block divided into 32 contiguous
streams of 2,048 symbols. Each stream advances through 32 consecutive
64-symbol update segments. Arithmetic order is segment, state, then stream,
matching the native `process_block()` order.

For every state, both encoder and decoder recompute from completed per-stream
history plus zero future fillers. Persistent 256-symbol layer memories advance
only after a complete 64-symbol segment. The Adam update occurs after that
segment is fully reconstructed.

## Exact controls

Run two independently initialized encoders and one independently initialized
model-driven decoder. Require identity of:

```text
branch-frequency stream
terminated arithmetic archive
all decoded preprocessed symbols
per-segment losses
final model parameters
final Adam state
final persistent memories
official raw inverse
```

All branch frequencies must remain in `[1, 32767]`, and peak allocated memory
must remain below decimal 10 GB.

## Same-population reference

Map the last preprocessed symbol to its exact raw boundary. The boundary must
also be a complete WRT emission-group boundary in the recovered canonical 10M
JANUS-plus-quotient trace. Terminate a new joint arithmetic payload at exactly
that boundary and verify its decoder. This makes the primary gross comparison:

```text
terminated joint prefix bytes - terminated NNCP prefix bytes
```

No source, model, dictionary, framing, runtime, or forecast credit is granted
at Q1. Promotion requires an exact gross gain of at least 3,000 bytes per raw
million and every integrity/resource gate above. A miss retires this
self-consistent faithful-profile ROCm realization without architecture,
precision, stream-count, optimizer, block-layout, or future-filler sweeps.
