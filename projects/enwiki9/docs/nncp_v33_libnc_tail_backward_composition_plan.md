# NNCP v3.3 LibNC tail backward composition

Candidate: `nncp_v33_libnc_tail_backward_composition_v1`

Status: frozen zero-credit source-bound localization diagnostic.

## Purpose

The receipt-bound four-symbol miniature has an exact LibNC forward trajectory,
yet its first Adam update differs from the matched PyTorch replay at internal
parameters. The first material gradient difference is `ff_bias2_0`; output
projection and final-normalization parameter gradients are already close.

This gate isolates the complete downstream graph rather than another primitive.
It supplies the four exact source-captured `ff_out_bl` states to LibNC, adds one
shared zero-valued parameter, and evaluates the original tail:

```text
RMSNorm -> gain/bias -> output projection/bias -> F32 -> softmax
four-state concat optimization -> indexed log -> negative mean
```

The gradient of the shared zero parameter must equal the gradient that reached
`ff_bias2_0` in the complete bound graph.

## Identity contract

Two instrumented source executions must reproduce:

```text
archive SHA-256  8dd5482e51e5c85b92aab8e0ca9dffc8fc7d3458a2bfd2d669c2e9b1330646da
trace SHA-256    cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4
```

All 28 source tensors must repeat byte-identically. Two direct tail executions
must also repeat their complete probabilities and shared gradient
byte-identically. Direct tail probabilities must match the bound teacher within
`2e-6`.

## Frozen comparison

Compare the direct LibNC shared gradient and the matched PyTorch tail gradient
to `run_07_bound/gradients/unknown_0006.bin`, whose prior source-order mapping
is `ff_bias2_0`. Report maximum and mean absolute error, relative L2 error, and
sign mismatches.

`TAIL_BACKWARD_LOCALIZED` requires the direct LibNC gradient to match within
`2e-6` with no sign mismatch while PyTorch misses. This authorizes only a
source-bound operation-order localization inside the composed tail.

If both implementations match, classify the full replay failure as forward
rounding amplification rather than inventing a new backward rule. If direct
LibNC does not match, reject the assumed mapping or the isolated graph. In no
case may this diagnostic alter a proved forward primitive or receive score or
forecast credit.

The planning forecast remains `109,389,323` bytes and the verified full-1G
score remains unknown.
