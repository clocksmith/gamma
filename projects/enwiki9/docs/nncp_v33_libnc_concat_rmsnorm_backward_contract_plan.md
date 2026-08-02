# NNCP v3.3 LibNC concat-RMSNorm backward contract

Candidate: `nncp_v33_libnc_concat_rmsnorm_backward_contract_v1`

Status: frozen analytic source-parity gate; zero score and forecast credit.

## Derived rule

The source-captured post-FF2 adjoint differs from the matched RMSNorm adjoint
by one nearly constant feature offset per decoder state. Without fitting, the
offset is exactly the missing centered-gradient term from the final RMSNorm
nodes combined below `nc_concat_optimization`.

Let:

```text
inverse = rsqrt(mean(x*x) + 1e-5)
y       = x * inverse
g       = adjoint arriving at y
```

The ordinary direct LibNC RMSNorm gate established:

```text
dx = inverse * (g - y * mean(g*y))
```

The concat-root analytic contract is:

```text
dx = inverse * (g - mean(g) - y * mean(g*y))
```

Only the final RMSNorm node in each of the four output roots uses this rule.
Earlier RMSNorms retain the already proved direct LibNC operation order.

## Gate

The captured adjoint is read only as validation truth. It is never substituted
into backward. The analytic formula must independently reproduce:

```text
captured residual-join adjoint       within 2e-6, zero sign mismatches
all 18 source named gradients        within 2e-6, zero sign mismatches
teacher forward probabilities        within 2e-6
all source final tensors             within 2e-5 after one update
forward probabilities vs baseline   byte-identical
gradient and update replays          byte-identical
```

A pass converts the receipt-specific observation into a causal rule valid for
arbitrary current inputs and decoded truth. It authorizes one native
source-bound multi-update receipt, not a compression score or forecast change.
No formula coefficient or normalization variant is swept after a miss.
