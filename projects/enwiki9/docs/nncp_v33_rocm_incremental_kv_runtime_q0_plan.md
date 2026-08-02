# NNCP v3.3 ROCm incremental-KV runtime Q0

Candidate and proposal: `nncp_v33_rocm_incremental_kv_runtime_q0_v1`.

## Mechanism

The constructive ROCm decoder currently performs 64 complete 64-position
Transformer forwards per update segment. Before state `t`, positions after `t`
are zero-filled and causally masked, so those repeated prefix computations are
mathematically redundant.

The candidate evaluates one decoded position at a time. Every layer caches the
projected keys and values of the fixed 256-position memory and appends one
current-position key/value pair after that symbol becomes decoder-visible. The
relative-position slice is chosen to match the existing 64-query relative
shift. Predictions remain strictly causal.

After all 64 positions are reconstructed, discard the inference caches and run
the unchanged full differentiable segment forward. Cross entropy, per-parameter
clipping, Adam, persistent-memory selection, configuration, initialization,
and update frequency remain identical to the constructive parent.

## Frozen population and controls

Use the exact first 2,048 NNCP-preprocessed symbols arranged as 32 streams by
64 positions. Run two independent encoders and one independent model-driven
decoder reconstructed from the serialized arithmetic payload.

The reference is the existing causal-replay Q0 receipt:

```text
archive bytes              3,613
branch frequencies         28,673
final model SHA-256        2ae4efe57f08736c3e7d3f67104b74a496f4c54af6ee24b142904ab0be5014f5
loss nats                  9.782143592834473
median measured runtime    18.220641091 seconds
```

## Required evidence

Require exact identity across both candidate encoders and the decoder for:

```text
arithmetic archive
branch-frequency trace
decoded symbols
loss
model parameters after update
Adam state after update
persistent memory
```

The unchanged differentiable replay must reproduce the parent's exact final
model hash and loss. Report whether predictions and archive also equal the
parent. If arithmetic changes because the smaller GEMM shape rounds
differently, it receives no inherited score; it may proceed only as a changed-
stream child.

## Promotion

Require:

```text
ROCm matrix compute                              pass
candidate self-consistency                       exact
decoded symbols                                  exact
parent final model state and loss                exact
decimal-10GB allocated and reserved memory       pass
candidate median runtime reduction               >= 50 percent
archive delta versus parent                      <= 16 bytes
```

Exact parent branch/archive identity authorizes one 65,536-symbol runtime
identity replay. A self-consistent changed stream satisfying the same limits
authorizes one 65,536-symbol changed-stream headroom replay instead. Neither
outcome inherits the published NNCP score or changes the Gamma forecast.

A miss retires this exact eager PyTorch incremental cache without cache-layout,
precision, compiler, graph-capture, model, stream, or segment sweeps. It does
not retire an ABI-compatible native HIP LibNC implementation.
