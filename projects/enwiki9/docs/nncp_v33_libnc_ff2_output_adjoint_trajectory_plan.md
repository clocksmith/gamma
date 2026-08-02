# NNCP v3.3 LibNC FF2 output-adjoint trajectory

Candidate and proposal:
`nncp_v33_libnc_ff2_output_adjoint_trajectory_v1`.

## Purpose

The source-bound `ff2_0` and `ff_bias2_0` gradients differ materially from a
matched PyTorch graph and from a synthetic LibNC FF2-to-loss graph. Graph cuts
inside the saved concat-optimized source crash before producing evidence. This
gate observes the boundary without cutting it.

Each of the four decoder states adds a separate all-zero F32 parameter tensor
after the FF2 bias and before the residual join. Its gradient is the exact
adjoint entering the FF2 output. The source also serializes the exact activated
FF2 input before the matrix multiplication. The zero addition must preserve
the receipt-bound archive, probability trace, and every existing named
parameter-gradient byte.

## Algebraic control

For adjoint matrix `A` with one decoder state per column and activated FF2
input `H`:

```text
ff_bias2 gradient = column_sum(A)
ff2 gradient      = A * transpose(H)
```

The matched PyTorch graph must satisfy this composition first. The native
capture then distinguishes:

```text
UPSTREAM_ADJOINT_LOCALIZED
  native A differs from PyTorch and reconstructs both bound gradients

CONCAT_MATMUL_BACKWARD_LOCALIZED
  native A matches PyTorch, reconstructs PyTorch, but not the bound gradients

UNRESOLVED
  neither causal explanation passes the frozen 2e-6 gate
```

## Identity and decision

Two executions must repeat the probe and named-gradient directories, reproduce
the exact bound archive and trace, and leave all 18 source-named gradients
byte-identical. Any violation is infrastructure failure. A unique localization
authorizes only one exact miniature parity child. This diagnostic carries zero
score and forecast credit; the planning forecast remains `109,389,323` bytes
and the verified full-1G result remains unknown.
