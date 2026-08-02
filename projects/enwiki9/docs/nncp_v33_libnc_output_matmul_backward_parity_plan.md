# NNCP v3.3 LibNC output matmul backward parity

Candidate: `nncp_v33_libnc_output_matmul_backward_parity_v1`

Status: frozen zero-credit implementation-parity diagnostic.

## Question

Does LibNC's reproducible F32 `nc_matmul` backward reduction use a numerical
contract absent from the PyTorch bound-miniature replay, explaining the first
material gradient divergence immediately behind the exact output layer?

## Frozen fixture

The direct LibNC probe evaluates one `256 x 32` by `32 x 4` multiplication,
matching the bound output projection. Left, right, and nonuniform upstream
tensors are deterministic modular F32 values. Each upstream column has an
explicit zero-sum construction to exercise the cancellation present in a
softmax cross-entropy gradient.

The probe records the complete forward tensor and both complete input-gradient
tensors. It runs twice and requires an identical aggregate SHA-256.

## Frozen comparisons

- PyTorch native F32 matrix multiplication and autograd.
- Scalar F32 accumulation over the shared dimension in ascending order.
- Scalar F32 accumulation over the shared dimension in descending order.

All three compare forward, left-gradient, and right-gradient tensors against
the direct LibNC bytes with one absolute threshold of `2e-6`.

## Decision

A unique non-PyTorch match authorizes one bound-miniature replay changing only
the output-projection matrix-multiply backward. A PyTorch match, no match, a
nonunique match, or nondeterministic LibNC output retires this reduction as the
cause. No dimensions, fixture values, tolerances, BLAS libraries, or reduction
widths are swept.

This diagnostic has zero score and forecast credit. The planning forecast
remains `109,389,323` bytes and the verified full-1G score remains unknown.
