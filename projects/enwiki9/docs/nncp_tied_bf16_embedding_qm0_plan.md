# NNCP Tied BF16 Symbol Embedding QM0

Status: frozen 65,536-symbol constructive child; zero score credit.

## Question

Does coupling the geometry used to read and predict NNCP symbols improve the
online model while reducing memory?

## Frozen representation

The faithful model has a float32 `16,392 x 1,024` input embedding and an
independent bfloat16 output embedding. The candidate creates one bfloat16
`Parameter` from the faithfully initialized input matrix and assigns that exact
object to both model fields. Parameter enumeration and Adam see it once.

This removes 67,141,632 parameter bytes before gradient and optimizer-state
effects. It adds no table, symbol, metadata, or model blob. Transformer blocks,
output bias, optimizer hyperparameters, updates, memory, arithmetic alphabet,
and official inverse remain unchanged. BF16 input lookup is part of the frozen
mechanism.

## Gate

Compare against the receipt-bound faithful 96,142-byte archive over exactly
65,536 symbols. Require two encoders and one decoder to reproduce identical
archives, branch frequencies, symbols, losses, and complete states; require the
official NNCP inverse; and require allocated and reserved device memory below
decimal 10 GB.

Promotion additionally requires at least 800 actual archive bytes and positive
aligned ideal branch gain in every true corpus-chronological third. Compressed
incremental diagnostic source must not exceed 65,536 bytes.

A miss retires this exact tied-BF16 representation without dtype, partial-
tying, scale, or projection sweeps. This gate cannot inherit NNCP's published
score and makes no full-corpus forecast.
