# NNCP Midpoint First-Half Tree-Node Calibration QM0

Candidate: `nncp_midpoint_tree_node_calibration_qm0_v1`.

This zero-credit same-object attribution asks whether the full midpoint
teacher's gain can be represented as a compact correction over NNCP's existing
balanced symbol tree. It consumes the receipt-bound faithful probability trace
and exact `262,144`-symbol population; it does not rebuild NNCP or make LibNC
eligible.

For every 64-state native segment, states 0--31 are coded faithfully. Their
realized branches are pooled across the 32 native streams by exact tree node.
For node `u`, let `z_u` and `n_u` be the zero count and total count. During
states 32--63 the sleeping node expert predicts

```text
Q_u(0) = (z_u + 1/2) / (n_u + 1).
```

It is marginalized with the faithful complete-symbol distribution at frozen
prior mass `16:1`; posterior weights update after each decoded branch and reset
at the next symbol. First-half statistics reset at every segment. No node ID,
count, selector, source address, distance, or model parameter is transmitted.

Matched arms use the same arithmetic coder and population:

- `base`: unchanged faithful trace;
- `node`: current first-half counts at the exact tree node;
- `depth`: current first-half counts pooled only by tree depth;
- `prior`: exact-node counts from the preceding segment's first half.

Promotion requires at least `7,500` actual bytes over `base`, positive
original-coordinate thirds, at least `1,000` bytes over both controls,
byte-identical repeat encoding, exact symbol decode, exact branch population,
and at most `65,536` compressed source bytes. Any miss retires this exact
pooling, KT law, `16:1` mixture, and reset schedule without concentration,
node-grouping, or persistence sweeps.

