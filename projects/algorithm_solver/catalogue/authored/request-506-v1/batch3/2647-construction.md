# Original threshold-two triangle construction

Development derivation by the author/integration agents, not copied editorial code.
For n rows there are V=n² cells and E=3n(n−1)/2 shared edges. In any
activation order each nonseed needs two distinct earlier-neighbor edges.
Hence 2(V−k)≤E and k≥ceil(n(n+3)/4).

Use base constructions for n=1,2,3 of sizes 1,3,5. For n≥4 recursively
fill rows 1 through n−4 and add a four-row fringe. Seed all odd cells of
row n, cell (n−1,2n−4), and positions 1,5,9,... of rows n−2 and n−3.
When n is odd, move the final seed of row n−2 one cell left.
This adds exactly 2n−1 seeds, so total matches the lower bound.

Why it fills: the bottom row's odd seeds fill its even gaps. Call the
other fringe rows A=n−3, B=n−2, C=n−1. With the inner region already red,
the alternating A/B seeds at positions 1 modulo 4 activate even cells
using an upper neighbor and an adjacent seed; intervening odd gaps then
activate. The only possible unfinished boundary is the right edge.
For even n, A ends seeded and fills; B's final upward cell gets its
second red neighbor from the special C seed. For odd n, the shifted B
seed supplies the downward neighbor of A's final upward cell, resolving
that boundary; B's last upward cell then sees both the shifted B seed
and the special C seed. Thus A and B fill in either parity. The special
C seed propagates horizontally through C, whose upper and lower fringe
neighbors are now red. This proves the fringe induction.

`test_triangle.py` separately verifies unique in-range seeds, the exact
lower-bound count and queue-based threshold-two activation for n=1..40,
all four residues near 100 and 256, and n=999,1000, in both languages.
These finite simulations supplement the construction argument; they are
not hidden-judge results or scientific qualification.
