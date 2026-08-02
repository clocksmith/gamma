# NNCP v3.3 tanh-GELU plus LibNC-order RMSNorm update parity

Candidate and proposal:
`nncp_v33_libnc_tanh_gelu_rmsnorm_update_parity_v1`.

Two direct LibNC component gates now prove differences from ordinary PyTorch:

```text
GELU       unfused tanh formula with positive-tail saturation
RMSNorm    inverse * (g - y * mean(g*y)) backward order
```

Apply exactly those two corrections to the same serialized one-layer,
32-wide, four-symbol bound miniature used by the previous full-update gate.
Retain its initial tensors, LibNC teacher distributions, final LibNC tensors,
learning rate `0.00016`, per-parameter gradient clip `0.05`, optimizer, and
`2e-5` tolerance.

Run twice from the serialized initial state. Promotion requires repeated
probabilities, losses, and final tensor hashes to be byte-identical, and both
the maximum distribution error and every final parameter error to be no more
than `2e-5`.

A miss retires the combined correction as sufficient and authorizes no mature
trace. A pass authorizes only the next exact primitive localization or frozen
full-profile parity gate. Score and forecast credit remain zero.
