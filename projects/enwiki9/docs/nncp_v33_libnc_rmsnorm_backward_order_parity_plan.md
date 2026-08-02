# NNCP v3.3 LibNC RMSNorm backward operation-order parity

Candidate and proposal:
`nncp_v33_libnc_rmsnorm_backward_order_parity_v1`.

The direct RMSNorm gate matched every forward value exactly but left a
`6.103515625e-05` maximum input-gradient error under ordinary PyTorch
autograd. A read-only localization showed that the mathematically equivalent
backward order

```text
inverse = rsqrt(mean(x*x) + eps)
y       = x * inverse
dx      = inverse * (g - y * mean(g*y))
```

matches the 40 direct LibNC gradients to one F32 ULP.

Freeze three backward implementations over the same direct, repeated LibNC
probe: ordinary PyTorch autograd, the output-based LibNC order above, and a
divided closed form. Require a unique output-order match within `1e-7` for both
values and gradients. A pass authorizes exactly one bound miniature full
update combining the already measured tanh GELU with this custom RMSNorm
backward. A miss retires the operation-order hypothesis without epsilon,
shape, grid, or threshold sweeps.

This diagnostic has zero score and forecast credit.
