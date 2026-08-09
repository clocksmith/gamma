# NNCP CP8 Symbol Readout Qm0

Status: frozen exact constructive representation gate

## Hypothesis

NNCP currently predicts `16,392` symbols with an independent
`16,392 × 1,024` BF16 output matrix. Symbol IDs decompose exactly into 65 high
bytes and 256 low bytes. A readout that shares high-class, low-identity, and a
rank-8 high/low interaction may learn faster and removes most output parameters
and Adam state without tying the input representation.

For hidden vector `x`, symbol `s = 256h + l` receives

```text
dot(x, A[h]) + dot(x, B[l])
+ sum_r dot(x, W[r]) U[h,r] V[l,r]
+ bias[s]
```

The exact symbol-specific bias, input embedding, transformer, online update
schedule, arithmetic alphabet, and official inverse remain unchanged. No
table or label is transmitted; encoder and decoder construct the factorization
from the same fixed dimensions and seed.

## Frozen gate

Use high=`id >> 8`, low=`id & 255`, rank=`8`, BF16 factors, and the faithful
initialization scale. Run the existing exact 65,536-symbol harness twice for
encoding and once for decoding. Require archive identity, decoded symbol and
complete-state identity, official raw inversion, decimal-memory compliance,
positive ideal gain in every true chronological third, at least `800` actual
bytes over the faithful `96,142`-byte archive, and no more than `65,536` bytes
of compressed incremental source.

A miss retires this factorization without rank, partition, dtype, bias,
initialization, or interaction-form sweeps. It does not reopen tied embeddings
or hierarchical PPM.
