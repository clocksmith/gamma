# NNCP v3.3 LibNC internal forward trajectory

Candidate: `nncp_v33_libnc_internal_forward_trajectory_v1`

Status: frozen zero-credit implementation-localization diagnostic.

## Purpose

Near-identical output probabilities coexist with large internal gradient
differences. RMSNorm can conceal radial differences in its input, so output
probability parity alone does not prove that the hidden trajectory is the same.

This gate recompiles the receipt-bound `nncp.c` with its existing `DUMP_HASH`
sites enabled and interposes only `nc_dump_tensor_hash` to serialize the labeled
tensor argument. It does not change the graph, tensor values, model, optimizer,
or archive code.

## Identity contract

The exact reconstructed command must reproduce both bound artifacts:

```text
archive SHA-256  8dd5482e51e5c85b92aab8e0ca9dffc8fc7d3458a2bfd2d669c2e9b1330646da
trace SHA-256    cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4
```

Two complete instrumented executions must also produce identical labeled
tensor files. Any identity or repeat failure is infrastructure-invalid.

## Compared trajectory

For each of four decoder states, compare complete F32 tensors at the seven
existing source labels:

```text
attn_out_bl
attn_out
ff1_out
ff2_in
ff_out_bl
ff_out
output
```

Report maximum and mean absolute error, both L2 norms, their ratio, the best
scalar mapping from the PyTorch tensor to LibNC, and the residual after that
scalar. The first source-ordered tensor above `2e-6` is the only authorized
forward localization.

## Decision

An exact, repeated, source-bound capture with a first divergence authorizes
one child correcting only that forward contract. If every tensor is within
`2e-6`, do not change another forward primitive; return to direct backward
intermediate evidence. No score or forecast credit is available from this
diagnostic. The planning forecast remains `109,389,323` bytes and the verified
full-1G score remains unknown.
