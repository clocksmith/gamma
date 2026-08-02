# NNCP v3.3 LibNC FF2 upstream connectivity gradient

Candidate: `nncp_v33_libnc_ff2_upstream_connectivity_gradient_v1`

Status: frozen zero-credit source-bound graph-connectivity diagnostic.

## Purpose

The output-only complete source graph reproduces bound FF2 gradients, while a
synthetic output-only graph beginning at exact captured FF2 inputs agrees with
PyTorch and misses those gradients. Root-set membership is not responsible.
The remaining distinction is whether the FF2 hidden input and residual retain
their upstream graph nodes while recursive concat optimization traverses the
output root.

This gate inserts an explicit constant tensor copy in a temporary source copy
without changing any forward value. This is used instead of `nc_stop_grad`,
which mutates a uniquely owned graph node in place and is unsafe in the saved
concat-optimized source graph:

```text
none           no cut
hidden_stop    cut the activated FF2 input graph
residual_stop  cut the residual graph
both_stop      cut both upstream graphs
```

All original key/value/output concat roots remain enabled.

## Identity contract

Every variant runs twice and must reproduce the exact bound archive and teacher
trace and repeat its complete named-gradient directory. The uncut variant must
reproduce every prior named gradient byte. Cut variants may omit callbacks for
disconnected upstream parameters, but must name the complete downstream set,
including `ff2_0` and `ff_bias2_0`, without duplicates.

## Decision

Compare each variant's FF2 matrix and bias gradients against both the bound
source and matched PyTorch. `CONNECTIVITY_LOCALIZED` requires the uncut source
to match bound, both-stop to match PyTorch but not bound, and at least one
frozen stop set to isolate the transition. The earliest passing set in
`hidden_stop`, `residual_stop`, `both_stop` identifies the authorized
connectivity contract.

If both-stop retains the bound gradients or fails to match PyTorch, upstream
connectivity is retired as the isolated cause. No forward primitive may change.
The gate carries zero score and forecast credit; the planning forecast remains
`109,389,323` bytes and the verified full-1G score remains unknown.
