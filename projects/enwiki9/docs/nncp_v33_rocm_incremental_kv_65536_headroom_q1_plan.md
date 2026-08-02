# NNCP v3.3 ROCm incremental-KV 65,536-symbol headroom Q1

Proposal and candidate:
`nncp_v33_rocm_incremental_kv_65536_headroom_q1_v1`.

## Authorization

The incremental-KV Q0 reconstructed 2,048 symbols exactly with two identical
encoders and one independent decoder. Archive size remained 3,613 bytes,
model/update state was identical to the full-prefix parent, peak reserved ROCm
memory was 7,822,376,960 bytes, and median execution fell 81.3338 percent.
Smaller GEMM shapes changed the arithmetic bytes and branch frequencies, so
Q0 authorizes only this changed-stream headroom replay.

## Frozen realization

Use the exact first 65,536 receipt-bound NNCP symbols as 32 streams of 2,048
symbols. Each stream advances through 32 consecutive 64-symbol update
segments. At each segment, project the fixed 256-position memories into
per-layer key/value caches, decode one state at a time, append only the
decoder-visible current key/value, and use the exact relative-position slice
validated at Q0.

After each complete segment, discard the inference caches and perform the
unchanged full differentiable replay, cross entropy, per-parameter clipping,
Adam update, and persistent-memory selection. The first input of every segment
after segment zero is the preceding decoded stream symbol.

Run two independently initialized encoders and one independently initialized
model decoder. Require exact identity of archive, branch frequencies, decoded
symbols, per-segment losses, model, Adam, and persistent memory. Restore the
exact raw prefix with the official NNCP inverse. Allocated and reserved memory
must both remain below decimal 10 GB.

## Same-boundary decision

Map symbol 65,536 to its exact raw boundary and require that boundary to be a
complete WRT emission group. Terminate and decode the recovered canonical
JANUS-plus-quotient P1 at that identical raw boundary.

Promotion requires at least 3,000 exact archive bytes per raw million over
that joint prefix and every identity/resource gate. A valid miss exits zero
and retires the changed-stream realization without architecture, precision,
cache-layout, stream-count, optimizer, block-layout, or compiler sweeps.
Neither outcome inherits the published NNCP score or changes the forecast.
