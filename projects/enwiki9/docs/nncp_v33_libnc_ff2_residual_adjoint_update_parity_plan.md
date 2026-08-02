# NNCP v3.3 LibNC FF2 residual-adjoint update parity

Candidate: `nncp_v33_libnc_ff2_residual_adjoint_update_parity_v1`

Status: frozen source-bound one-update diagnostic; zero score and forecast
credit.

## Question

The parent gradient gate showed that the exact source-captured adjoint, applied
at the post-FF2 residual join, reproduces all 18 bound gradients within
`8.940696716308594e-08` and with zero sign mismatches. This child applies
that single confirmed backward contract inside the existing matched online
update and compares the resulting parameter state with the source export.

## Frozen execution

```text
baseline   existing four-state decoder graph and existing Adam replay
repaired   identical graph, loss, clipping, and Adam replay;
           replace only the four post-FF2 residual-join adjoints
```

The repaired realization runs twice. Hooks affect backward only. The forward
probability stream must therefore remain byte-identical to baseline.

## Gate

Require:

```text
baseline maximum parameter error exactly repeats 0.00031999964267015457
baseline remains outside the frozen 2e-5 tolerance
repaired probabilities are byte-identical to baseline
repaired probabilities remain within 2e-5 of the source trace
every repaired final tensor is within 2e-5 of the source export
two repaired model/probability/loss executions are byte-identical
```

A pass authorizes only derivation and testing of a causal multi-update
contract. The captured four-state adjoint is receipt-specific and cannot be
used as a constructive compressor rule. A valid miss exits zero and retires
the captured residual-adjoint contract as sufficient without optimizer,
learning-rate, clipping, epsilon, or tolerance sweeps.
