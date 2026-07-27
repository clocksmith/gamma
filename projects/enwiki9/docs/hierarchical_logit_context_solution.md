# HL-1 Solution: Exact MDL Selection on a Context Hierarchy

At a leaf, splitting is unavailable, so the optimum is

\[
D(v)=a_v+\min_k L_v(k).
\]

At an internal node, every legal subtree model makes exactly one of two
mutually exclusive first decisions. If it stops, its best expert is the
minimum-loss expert and its cost is the first branch. If it splits, child
observation sets are disjoint and all child models are required, so their
independent optimum costs add with \(b_v\). Induction from the leaves proves
the recurrence.

Choose the least expert index on an expert tie. Choose stopping on equality
between stop and split. These rules produce a deterministic
inclusion-minimal model. Store one decision bit at every visited internal node
and the selected expert index at every stopped node; a preorder traversal
reconstructs the model uniquely.

Computing every expert loss is external input work. Given the loss table, one
postorder pass evaluates each expert once per node and each tree edge once.
The running time is \(O(|T|K)\), and values plus backpointers use \(O(|T|)\)
space.

For causal transfer, traverse the selected tree using only coordinates known
from already decoded data. The reached stopped node supplies a fixed expert,
whose probability is also computed before truth. Both encoder and decoder
therefore choose identical probabilities by induction over positions.

The theorem proves exact MDL optimality only for the supplied training losses,
prices, hierarchy, and expert family. A sealed chronological replay is still
required to establish predictive transfer and net archive benefit.
