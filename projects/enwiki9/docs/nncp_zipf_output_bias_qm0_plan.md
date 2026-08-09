# NNCP Zero-Table Zipf Output Bias QM0

Status: frozen 65,536-symbol constructive child; zero score credit.

## Question

Does NNCP's symbol ID contain enough decoder-visible frequency geometry to
replace its uniform initial output prior without transmitting a frequency
table?

## Frozen mechanism

After the faithful deterministic parameter initialization, set the existing
trainable output bias to:

```text
bias[i] = -0.435 * ln(i + 1)
```

The exponent is frozen from the full receipt-bound symbol population. The
candidate adds no parameter or table. Input embeddings, output embeddings,
Transformer weights, optimizer, online updates, memory, arithmetic alphabet,
and inverse remain unchanged. The ordinary Adam update continues training the
existing bias after every native 64-symbol segment.

The static full-population oracle saves 6,925,664 bytes versus a uniform prior;
the same law saves 1,764 ideal bytes versus uniform on the first 65,536
symbols. Those figures do not compare against the trained NNCP trajectory and
grant no score credit.

## Gate

Compare against the receipt-bound faithful 96,142-byte archive over exactly
65,536 symbols. Require two encoders and one decoder to reproduce identical
archives, branch frequencies, symbols, losses, and complete states; require the
official NNCP inverse; and require allocated and reserved device memory below
decimal 10 GB.

Promotion additionally requires at least 800 actual archive bytes and positive
aligned ideal branch gain in every true corpus-chronological third. Compressed
incremental diagnostic source must not exceed 65,536 bytes.

A miss retires alpha 0.435 and rank-law initialization without exponent,
offset, piecewise-law, or frequency-table sweeps. This gate cannot inherit
NNCP's published score and makes no full-corpus forecast.
