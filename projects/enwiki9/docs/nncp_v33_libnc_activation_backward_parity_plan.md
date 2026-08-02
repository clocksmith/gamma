# NNCP v3.3 LibNC activation-backward parity localization

Proposal: `nncp_v33_libnc_activation_backward_parity_v1`

## Question

The bound NNCP v3.3 miniature matches LibNC's frozen forward distributions but
diverges after the first online update. The previous gradient interposition
localized the disagreement to internal backward paths while leaving the output
gradient nearly exact. Before treating all PyTorch autograd as incompatible,
this gate asks whether the first nonlinear primitive differs: LibNC's
`nc_gelu` forward or backward contract versus PyTorch `gelu`.

The official graph computes GEGLU as `nc_gelu(left) * right`, so a mismatched
GELU derivative would propagate into feed-forward, residual, attention, and
embedding gradients while preserving close frozen inference.

## Frozen primitive gate

Use the public API from the receipt-bound NNCP 2024-06-05 package. Evaluate
`nc_gelu` and its automatic derivative on a fixed F32 grid from -8 through 8,
including dense points around zero. Run the standalone LibNC executable twice
and require byte-identical output.

Compare the values and derivatives to:

1. PyTorch's exact erf GELU.
2. PyTorch's tanh-approximate GELU.

Record the maximum absolute and relative errors for forward values and
derivatives. The tool, compiler command, header, library, and result are all
hash-bound.

## Decision

Promote exactly one corrected bound miniature replay only if one frozen
PyTorch formula matches LibNC's primitive derivative within `2e-6` maximum
absolute error and the repeated LibNC result is byte-identical. Otherwise
retire GELU backward as the cause.

A primitive pass receives zero score credit. The subsequent full-gradient gate
must still reduce every named gradient and the first completed update below
the prior `2e-5` maximum-error threshold. No mature NNCP trace, codec port, or
full-corpus claim is authorized by this gate.
