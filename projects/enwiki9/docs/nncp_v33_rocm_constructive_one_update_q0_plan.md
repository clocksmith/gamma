# NNCP v3.3 faithful ROCm constructive one-update Q0

Proposal and candidate: `nncp_v33_rocm_constructive_one_update_q0_v1`.

## Purpose

The official NNCP v3.3 enwik9 result is below the 108,000,000-byte target, but
its CUDA LibNC runtime cannot execute on this AMD host. Frozen forward parity
is established, while exact LibNC online-update parity remains false. This gate
therefore makes no LibNC-equivalence claim. It asks whether a self-consistent
source-level PyTorch/ROCm realization can perform an actual encode and an
independent model-driven decode.

This differs from the retired ROCm ALiBi teacher. It freezes the official
profile structure:

- 20 layers, width 1024, eight 128-wide heads, and GEGLU width 3072.
- Learned per-layer relative tables of width 320 and one shared relative bias.
- Memory 256, segment 64, batch 32, and the official contiguous-stream block
  layout.
- F32 input embedding, BF16 remaining parameters, RMS normalization with
  learned gain and bias and epsilon `1e-5`.
- The directly measured LibNC unfused F32 tanh-GELU contract.
- Adam `(beta1=0, beta2=0.9999, epsilon=1e-8)` with per-parameter norm clipping
  at `0.05`.

No dropout or retraining occurs in this one normal update block.

## Frozen population and execution

Use exactly the first 2,048 symbols of the receipt-bound official
16,392-symbol preprocessed stream. Arrange them as 32 contiguous streams of 64
symbols, matching `process_block()`.

The encoder evaluates the complete causally masked shifted-input segment,
range-codes symbols in state-major then stream-major order, applies one update,
and hashes every final parameter byte.

The decoder starts from a separately seeded model. For each state it evaluates
only the decoded prefix, derives its branch frequencies, and decodes all 32
stream symbols. After state 63 it applies the identical update. It may recompute
the masked segment during Q0; runtime optimization is a successor concern.

## Gate

Require:

- Real ROCm matrix compute in the declared runtime mode.
- Exact future-perturbation prefix identity.
- Two seeded encoder archives byte-identical.
- Encoder and decoder branch-frequency streams byte-identical.
- Exact decoded preprocessed symbols.
- Exact complete final model-state hashes across both encoders and decoder.
- Exact official preprocessor inverse to the bound raw prefix.
- Legal nonzero 15-bit range frequencies.
- Peak allocated GPU memory below decimal 10 GB.

A pass authorizes one frozen 65,536-symbol headroom gate. It receives zero
score credit and does not inherit the published NNCP score. A miss retires this
realization without architecture, precision, stream-count, or optimizer rescue
sweeps.
