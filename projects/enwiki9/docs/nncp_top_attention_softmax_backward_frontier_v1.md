# NNCP Top-Attention Softmax-Backward Frontier v1

## Claim boundary

This document prepares two zero-credit arithmetic gates after
`nncp_open_top_attention_value_transpose_64_q0_v1`. Neither gate is an open
predictor, compressor, archive improvement, or Hutter Prize result.

The frozen dP gate establishes only:

```text
Y  = P V
dP = dY V^T
```

The next backward edge is:

```text
row_dot = sum_k P_k * dP_k
dS_k    = P_k * (dP_k - row_dot)
```

where `S` is the masked/scaled attention-score tensor immediately supplied to
`nc_soft_max`, and each softmax row contains 320 keys.

## Gate A: source score-adjoint oracle

Candidate:

```text
nncp_libnc_top_attention_softmax_input_adjoint_oracle_64_q0_v1
```

The source-only probe
`tools/nncp_libnc_top_attention_softmax_input_adjoint_probe_q0.c` extends the
existing top-attention identity-marker probe with `GAMMA_TOP_ATTN_SCORE`. The
source patch must attach the score marker to `t0` immediately before this exact
operation:

```c
t1 = nc_soft_max(t0);
```

The existing probability marker remains attached to `t1` immediately after the
softmax, and the attended marker remains attached before `w_o`. No graph edge,
value, shape, optimizer call, fixture byte, or update order may otherwise
change.

For layer 19, block index 256, states 0 through 63, capture two independent
complete executions of:

```text
score input       BF16, dimensions 320,1,8,32
score adjoint     BF16, dimensions 320,1,8,32
probability input BF16, dimensions 320,1,8,32
probability adj.  BF16, dimensions 320,1,8,32
```

Serialization is state-major, head-major, stream-major, key-major after the
existing observed-axis assembly. Each complete population contains 5,242,880
BF16 words. The score oracle passes only if both captures and manifests are
byte-identical, every tensor is live, the non-probe fixture is unchanged, wrong
layout controls mismatch, resource/cleanup guards pass, and no captured tensor
is admitted to a codec package.

## Gate B: open softmax backward

Candidate:

```text
nncp_open_top_attention_softmax_backward_64_q0_v1
```

Inputs are the exact open probability population, the exact open dP output from
the preceding transpose gate, and Gate A's score-adjoint tensor used only as an
independent comparator. The implementation must be LibNC-free and must bind the
source operation order, BF16 widening/rounding points, row reduction order,
thread count, FMA contraction behavior, and masked-key behavior before running.

Required controls:

```text
treatment       source-coordinate formula and reduction order
key-reversed    reverse the 320-key row reduction; require mismatch
wrong-layout    stream/head transposition; require mismatch
sign-negated    negate dP; require mismatch
replay          repeat complete treatment and controls byte-for-byte
```

Promotion requires all 5,242,880 treatment BF16 words to match the independent
score-adjoint comparator exactly, all controls to be live, no undeclared runtime
dependency, complete source closure, and disk/RSS guards. Tolerance, coordinate
repair, fitting to mismatches, LibNC execution in the open gate, and compression
credit are forbidden.

## Subsequent authorized arithmetic

Only after exact dS parity may the campaign separately freeze:

```text
dQ = dS K / sqrt(128)
dK = dS^T Q / sqrt(128)
```

Those gates require exact open Q/K tensors and independent source comparators.
They do not become authorized merely because dP or dS passes.
