# DV-1: Delayed-View Residual Prediction

## Problem

Let an encoded symbol stream be partitioned into deterministic emission groups
\(G_1,\ldots,G_m\). Group \(G_j\) reconstructs a raw expansion \(R_j\), but
\(R_j\) becomes visible only after every symbol of \(G_j\) has been decoded.

Before each encoded bit \(t\), a baseline supplies probability \(p_t\). Define
a finite deterministic context from:

1. raw expansions of completed groups only;
2. encoded bits already decoded in the current group;
3. fixed finite counters and tables.

An auxiliary predictor supplies \(r_t\), and the final probability is a fixed
integer blend

\[
q_t=\operatorname{clamp}
\left(
\left\lfloor\frac{(D-w)p_t+wr_t}{D}\right\rfloor
\right).
\]

Prove:

1. Encoder and decoder have identical delayed raw history before every bit.
2. A deterministic bounded-table insertion, lookup, update, and eviction rule
   preserves identical auxiliary state.
3. If the table updates only after the current truth bit, \(q_t\) is causal.
4. Arithmetic decoding with \(q_t\), followed by the deterministic inverse
   group transform, reconstructs the original raw stream exactly.
5. The construction transmits no table state, but its source, memory, runtime,
   and any archive regression remain fully chargeable.

State the induction invariant precisely.
