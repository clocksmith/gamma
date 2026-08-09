# NNCP Hierarchical 448-Position Memory QM0

Status: frozen 65,536-symbol constructive child; zero score credit.

## Question

Does representing NNCP's fixed-size hidden memory at two resolutions expose
useful causal history beyond the flat 256-state horizon?

## Frozen representation

Each layer and native stream retains exactly 256 bfloat16 memory vectors:

```text
64 summary slots * 4 historical states = 256 old positions
192 exact recent slots                 = 192 recent positions
nominal coverage                       = 448 causal positions
```

At each existing 64-symbol update, discard the oldest 16 summaries, retain the
newest 48, average the 64 exact states leaving the recent window into sixteen
consecutive four-state means, and retain the newest 192 exact states. The
tensor shape, parameters, optimizer, attention, relative-position machinery,
arithmetic alphabet, update schedule, and incremental-KV path remain fixed.
Encoder and decoder derive every summary from already reconstructed state.

This is not the retired one-slot EMA. It replaces a complete old-memory region
with a fixed two-resolution representation and has no recurrent decay.

## Gate

Compare against the receipt-bound faithful 96,142-byte archive over exactly
65,536 symbols. Require two encoders and one decoder to reproduce identical
archives, branch frequencies, symbols, losses, and complete states; require the
official NNCP inverse; and require allocated and reserved device memory below
decimal 10 GB.

Promotion additionally requires at least 800 actual archive bytes and positive
aligned ideal branch gain in every true corpus-chronological third. Compressed
incremental diagnostic source must not exceed 65,536 bytes.

A miss retires this exact 64-summary, four-state-mean, 192-exact geometry. There
is no summary-count, pooling-width, or horizon sweep. The gate cannot inherit
NNCP's published score and makes no full-corpus forecast.
