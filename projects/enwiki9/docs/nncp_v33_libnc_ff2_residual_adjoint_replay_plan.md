# NNCP v3.3 LibNC FF2 residual-adjoint replay

Candidate: `nncp_v33_libnc_ff2_residual_adjoint_replay_v1`

Status: frozen source-bound diagnostic; zero score and forecast credit.

## Question

The observation-neutral parent captured an exact `32 x 4` LibNC adjoint after
the FF2 bias. That adjoint reconstructs the bound `ff2_0` gradient exactly and
the bound `ff_bias2_0` gradient within one float32 accumulation unit, while the
matched PyTorch adjoint differs by `11.4507%` relative L2 and two signs.

This child asks one question: does replaying that exact adjoint at the
post-FF2 residual join reproduce the complete source-bound backward map?

## Frozen variants

All variants build the identical four-state forward graph and decode the same
teacher trace twice.

```text
baseline          unchanged matched PyTorch backward
ff2_branch_only   replace the FF2 branch adjoint only
residual_join     replace the residual-join adjoint before both branches
```

The source-captured float32 matrix is decoded from the parent decision's
canonical base64 field and accepted only when its SHA-256 is
`63c4f89074fab3041a1d1b3a6f78bf32960946255d940e77274feeadb560a064`.
No value is fitted or inferred from the target gradients.

## Exact gate

Require:

```text
all three variants repeat byte-identically
all forward probability streams are identical and within 2e-6 of teacher
baseline reproduces the prior PyTorch gradient hash and remains a miss
FF2-branch-only matches ff2_0 and ff_bias2_0 but remains insufficient upstream
residual-join matches all 18 bound named gradients within 2e-6
residual-join has zero gradient sign mismatches
```

A pass authorizes one exact first-update replay. It does not authorize a
prefix compression run or change the `109,389,323`-byte forecast. A valid miss
is `REJECT` with process status zero and retires this boundary without a
tolerance, optimizer, width, loss, or parameter sweep.
