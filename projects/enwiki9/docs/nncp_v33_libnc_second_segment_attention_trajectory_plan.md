# NNCP v3.3 LibNC second-segment attention trajectory

Candidate: `nncp_v33_libnc_second_segment_attention_trajectory_v1`

## Frozen question

The exact source post-update-one state first differs from the analytic replay
at state-zero `attn_out_bl`. Which first arithmetic node inside the nonzero-
memory attention path explains that difference?

## One observation-only intervention

Retain the exact 32-byte source run, post-update state capture, and existing
forward observations. Add fixed `DUMP_HASH` observations only at state zero:

```text
embed
attention normalized input
query and current key/value projections
transformed persistent memory
complete decoder key/value buffers
content score
shifted relative score
masked scaled score
attention probability
attended value
concatenated heads
attention output projection
```

Run twice and require unchanged archive, teacher trace, update-state files, and
existing forward records. Replay the same nodes from the exact source state.
Tensor layout conversions are fixed from the declared LibNC dimensions, not
chosen by minimum error.

## Decision

The first aligned node above `2e-6` authorizes one operation-contract child.
If all added nodes match but `attn_out_bl` does not, localize the residual-add
operation. Changed outputs, nondeterministic dumps, unmatched labels/shapes, or
an unaccounted layout is an infrastructure failure.

No parameter, tolerance, width, optimizer, memory-length, or population sweep
is authorized. This diagnostic has zero score and forecast credit; the
forecast remains `109,389,323` bytes and the verified full-1G score remains
unknown.
