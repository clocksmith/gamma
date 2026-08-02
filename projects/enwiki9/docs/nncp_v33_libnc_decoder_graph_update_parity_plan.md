# NNCP v3.3 LibNC decoder-graph update parity

Candidate: `nncp_v33_libnc_decoder_graph_update_parity_v1`

Status: frozen zero-credit implementation-parity diagnostic.

## Question

Does LibNC's state-major decoder graph explain the bound one-update gradient
divergence that remains after direct GELU, RMSNorm, output-matmul, and loss
backward primitives have been bounded?

## Frozen change

The parent builds one vectorized four-symbol causal segment graph. This child
builds four causal decoder-state graphs in chronological order. Each state
adds its completed normalized input, key, and value nodes to the prefix
available to later states. The four logits are joined only for the single
segment loss and update.

Everything else remains fixed:

- Bound initial LibNC tensor export, truth symbols, probability trace, and
  final tensor export.
- One F32 layer, width 32, two heads, memory four, segment four.
- Measured LibNC tanh-GELU forward graph.
- Measured LibNC RMSNorm backward operation order.
- Mean cross-entropy, per-parameter norm clipping, Adam parameters, and
  `0.00016` learning rate.
- Absolute probability and final-tensor tolerance `2e-5`.

## Decision

Promotion requires bound probabilities and every final tensor within `2e-5`,
plus byte-identical repeated probabilities, losses, and final tensors. A miss
retires the state-major saved-node graph as sufficient. No mask, memory,
primitive, optimizer, loss, width, or tolerance rescue sweep follows.

This diagnostic has zero score and forecast credit. The planning forecast
remains `109,389,323` bytes and the verified full-1G score remains unknown.
