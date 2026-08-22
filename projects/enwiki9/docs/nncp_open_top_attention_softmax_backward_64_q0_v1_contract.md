# Open Top-Attention Softmax Backward 64 q0 v1

## Boundary

This zero-credit arithmetic gate implements only the layer-19 attention
softmax input adjoint:

```text
dS_i = P_i * (dP_i - sum(j=0..319, P_j * dP_j))
```

The frozen population contains `64 * 32 * 8 * 320 = 5,242,880` little-endian
BF16 words for each of `P`, `dP`, and the source `dS` comparator. Serialization
is state-major, stream-major, head-major, key-major. The reduction restarts for
each `(state, stream, head)` row and visits keys `0..319` sequentially.

The bound production graph multiplies attention scores by `1/sqrt(d_key)` and
applies the causal `-INFINITY` mask before calling `nc_soft_max(t0)`. The score
probe is attached to that already-scaled, already-masked `t0`. Consequently the
softmax-backward operation at this boundary has scale exactly `1.0`; applying
the attention scale again would be a rejected double-scaling implementation.

## Arithmetic

BF16 inputs widen exactly to FP32. Products, reduction additions, centering,
and final multiplication are rounded as scalar IEEE-754 FP32 under
`FE_TONEAREST`. FMA contraction, fast-math, vectorized reductions, FTZ, and DAZ
are disabled. Final outputs narrow to BF16 using round-to-nearest-even.

The treatment is executed twice. Promotion requires complete byte identity to
the independently captured source score adjoint and byte identity between both
open executions. A reverse-key association control and a negated-dP control
must each differ from the source comparator.

## Evidence boundary

The source score-adjoint oracle must pass before this gate is materialized or
executed. Its exact artifacts, experiment, candidate revision, compiler,
kernel, runner, command, return codes, logs, resource guard, and cleanup must be
hash-bound by a separately prospective experiment.

A pass proves this one softmax-backward edge only. It does not prove `dQ`,
`dK`, a complete attention backward pass, a complete open NNCP predictor,
archive savings, or Hutter eligibility. Objective and compression credit are
zero. Captured teacher tensors cannot ship in a final codec.
