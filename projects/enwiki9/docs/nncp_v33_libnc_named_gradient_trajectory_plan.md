# NNCP v3.3 LibNC named gradient trajectory

Candidate: `nncp_v33_libnc_named_gradient_trajectory_v1`

Status: frozen zero-credit source-bound localization diagnostic.

## Purpose

The prior gradient interposer serialized correct bytes but could not resolve
parameter names because calls inside `libnc.so` did not traverse its public
optimizer-registration interposition. Positional names inferred afterward are
now quarantined: a direct LibNC tail and the matched PyTorch tail agree, yet
both miss the file previously assigned to `ff_bias2_0` by the same constant
offset.

This gate creates a temporary observational source build. Immediately before
the existing `nc_backward` call it exposes `s->param_list`; immediately before
each existing `sgd_opt_update_var` call it matches the callback's opaque
`NCParam *` directly to the live list and serializes the gradient under
`NCParam.name`. The pointer contract is bound by disassembly of this exact
`libnc.so`: `nc_new_param_str` passes the newly allocated `NCParam *` as the
second argument to `nc_set_param`.

## Identity contract

The temporary source changes no tensor, graph, optimizer, or arithmetic code.
Two complete executions must reproduce:

```text
archive SHA-256  8dd5482e51e5c85b92aab8e0ca9dffc8fc7d3458a2bfd2d669c2e9b1330646da
trace SHA-256    cde241e346ea4b1bc2d62822f1b5645c1d5f204a155293def4915b6c1715fef4
```

All named gradient files must repeat byte-identically. The callbacks must cover
the 18 manifest parameters exactly once, with no duplicate, missing, or
`UNMAPPED` name and with exact manifest dimensions. Each named file must also
be byte-identical to the same-index file in the prior positional receipt.

## Matched comparison

Rebuild the already frozen state-major PyTorch graph with the measured tanh
GELU and LibNC RMSNorm order. Two fresh runs must emit byte-identical
probabilities and gradient maps, and probabilities must match the bound trace
within `2e-6`.

Compare every source-named gradient in callback order. Report maximum and mean
absolute error, relative L2 error, sign mismatches, and the largest minimum
magnitude among sign-flipped coordinates. The first named tensor exceeding
`2e-6` or containing a sign mismatch is the only subgraph boundary authorized
for a direct child.

If all gradients match, do not change another backward implementation; inspect
the exact Adam update contract. Any source identity, naming, repeat, or receipt
failure is infrastructure-invalid. The gate carries no score or forecast
credit. The planning forecast remains `109,389,323` bytes and the verified
full-1G score remains unknown.
