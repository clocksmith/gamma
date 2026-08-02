# NNCP v3.3 LibNC FF2-to-loss backward composition

Candidate: `nncp_v33_libnc_ff2_to_loss_backward_composition_v1`

Status: frozen zero-credit source-bound localization diagnostic.

## Purpose

Source-authoritative names place the first LibNC-versus-PyTorch gradient
divergence at `ff2_0`, immediately after an exact `embed_out` gradient. The
standalone decoder tail does not reproduce the bound `ff_bias2_0` gradient,
which implies that the missing numerical contract appears only when more of the
optimized graph is present.

This gate adds exactly the shared feed-forward output projection to that tail.
For each of four states it consumes exact source-captured tensors:

```text
captured ff2_in -> shared ff2_0 matmul -> shared ff_bias2_0
captured attn_out residual -> final exact decoder tail -> common loss
```

The four outputs pass through the same `nc_concat_optimization` call used by
the source before the indexed-log negative-mean loss.

## Identity contract

Two instrumented source executions must reproduce the bound archive and
teacher trace and repeat all 28 source tensors byte-for-byte. Two direct block
executions must repeat complete probabilities, `ff2_0` gradients, and
`ff_bias2_0` gradients byte-for-byte. Direct probabilities must match the
teacher within `2e-6`.

The authoritative named-gradient receipt binds positional files 1 and 6 to
`ff2_0` and `ff_bias2_0`; the gate refuses any other mapping.

## Frozen comparison

Run an identical PyTorch block from the same captured inputs and initial
weights. Compare direct LibNC and PyTorch against both bound gradients using
maximum and mean absolute error, relative L2 error, and sign mismatches.

`FF2_BLOCK_LOCALIZED` requires direct LibNC to match both bound tensors within
`2e-6` with no sign mismatch while PyTorch misses. This authorizes one bound
update replay using only the proved block contract.

If direct LibNC misses either gradient, retire this FF2-to-loss block as
sufficient and move the direct boundary earlier in the graph. Do not mutate a
proved forward primitive or infer a full-codec gain. The planning forecast
remains `109,389,323` bytes and the verified full-1G score remains unknown.
