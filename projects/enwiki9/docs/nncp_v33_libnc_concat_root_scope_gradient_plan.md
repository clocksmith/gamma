# NNCP v3.3 LibNC concat root-scope gradient

Candidate: `nncp_v33_libnc_concat_root_scope_gradient_v1`

Status: frozen zero-credit source-bound graph-contract diagnostic.

## Purpose

Exact isolated LibNC graphs from the pre-final tail and from `ff2_in` through
loss agree with matched PyTorch but do not reproduce the complete source graph
gradients. The remaining concrete distinction is that the source calls
`nc_concat_optimization` with three root families after rewiring causal
attention nodes: key, value, and output.

This gate changes only which frozen roots are supplied to that call inside a
temporary copy of the exact source:

```text
output_only   output
key_output    key + output
value_output  value + output
full          key + value + output
```

All graph construction, node rewiring, forward arithmetic, parameters, loss,
and optimizer settings remain unchanged.

## Identity contract

Each variant runs twice. Every run must reproduce the bound archive and teacher
trace, cover all 18 source-named gradients exactly once, and repeat its complete
named-gradient directory byte-for-byte. The `full` variant must reproduce every
prior named gradient byte exactly. Any failure is infrastructure-invalid.

The matched state-major PyTorch replay supplies the reduced-graph control and
must retain its bound probability identity.

## Decision

For each root set, compare `ff2_0` and `ff_bias2_0` against both the full bound
gradients and PyTorch. Report full-trajectory byte equality as an additional
control.

`ROOT_SCOPE_LOCALIZED` requires:

1. `full` matches both bound gradients.
2. `output_only` matches both PyTorch gradients but not the bound gradients.
3. Adding a frozen key/value root set reproduces both bound gradients.

The first bound-matching set in `key_output`, `value_output`, `full` identifies
the minimal authorized root contract. If output-only and full are equivalent,
or no deterministic transition is isolated, retire concat root scope as the
cause. No score or forecast credit is available. The planning forecast remains
`109,389,323` bytes and the verified full-1G score remains unknown.
