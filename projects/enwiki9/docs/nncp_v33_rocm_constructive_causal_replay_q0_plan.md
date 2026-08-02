# NNCP v3.3 ROCm constructive causal-replay Q0

Proposal and candidate:
`nncp_v33_rocm_constructive_causal_replay_q0_v1`.

## Parent failure

The parent Q0 reached the declared ROCm runtime and repeated identical inputs
exactly, but changing segment input position 9 changed earlier logits by
`0.009521484375`. Intermediate localization showed that the masked attention
probabilities were byte-identical while the BF16 attended-value reduction
changed by `7.62939453125e-06`; the difference first became visible in block
10 and amplified through later blocks. This reproduces the already recorded
failure of full-segment BF16 scoring. No arithmetic encode began, so it is a
malformed realization rather than a compression rejection.

## One frozen change

Retain the parent's model, weights, data, 32 contiguous streams, 64-symbol
segment, learned relative attention, optimizer, range coder, update, inverse,
and memory gate. Change only inference scheduling.

Before state `s`, encoder and decoder both construct the same length-64 input:

```text
positions 1..s       decoded symbols 0..s-1
position 0           frozen zero start symbol
positions s+1..63    frozen zero future filler
```

They then evaluate the model and use only logits at state `s`. Future truth is
never materialized. After all 64 states are reconstructed, both sides perform
one identical differentiable full-segment update using the now-complete
shifted input. The update may depend numerically on the complete segment
because it occurs only after that segment is decoded; it cannot affect symbols
inside the completed segment.

## Exact gate

Use the same first 2,048 receipt-bound official NNCP-preprocessed symbols as
the parent. Require:

- real ROCm compute under `rocm_gfx_override`;
- zero future-perturbation error under the state-major schedule;
- two seeded encoder archives and branch-frequency streams byte-identical;
- independent decoder branch frequencies identical to both encoders;
- exact decoded symbol identity;
- exact final model-state and loss identity after one update;
- exact official preprocessor inverse;
- legal nonzero 15-bit branch frequencies;
- peak allocated memory below decimal 10 GB.

A pass authorizes exactly one frozen 65,536-symbol headroom run. It earns zero
score credit and inherits neither LibNC equivalence nor NNCP's published score.
A valid identity or memory miss retires this causal-replay realization without
architecture, precision, stream-count, optimizer, or future-filler sweeps.
