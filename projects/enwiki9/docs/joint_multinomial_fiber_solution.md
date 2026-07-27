# JMF-1 Solution: Joint Multinomial Symbol Fibers

Every position contains exactly one alphabet symbol. The fibers are therefore
pairwise disjoint and cover all positions. Replacing all unselected fibers by
\(\rho\) preserves a unique partition into the selected fibers and the
residual positions.

Choose the \(n_\rho\) residual positions, then the \(n_a\) positions for each
selected symbol. The number of choices is

\[
\binom{n}{n_\rho}
\binom{n-n_\rho}{n_{a_1}}\cdots
=\frac{n!}{n_\rho!\prod_{a\in S}n_a!}.
\]

Lexicographic rank and unrank give a canonical bijection with
\(\{0,\ldots,M(S)-1\}\). An injective fixed-length code of \(L\) bits has at
most \(2^L\) values, so \(L\ge\lceil\log_2M(S)\rceil\). A zero-padded rank
attains the bound.

In the without-replacement model, a category \(j\) is used \(n_j\) times.
Its successive probability numerators are
\(n_j,n_j-1,\ldots,1\). All denominators are
\(n,n-1,\ldots,1\). Hence the category-word probability is

\[
\frac{\prod_j n_j!}{n!}=\frac1{M(S)}.
\]

At a binary-tree node, the probability of a leaf equals the product of child
count ratios on its root-to-leaf path because all intermediate subtree counts
cancel. Multiplying over positions therefore gives the same categorical
without-replacement probability and again \(1/M(S)\).

For a subset with extracted total \(k\),

\[
\begin{aligned}
G(S)
&=\sum_{a\in S}(C_a-d_a)-h\\
&\quad-\log_2(n!)
+\log_2((n-k)!)
+\sum_{a\in S}\log_2(n_a!)\\
&=\sum_{a\in S}V_a-h-\log_2\frac{n!}{(n-k)!}.
\end{aligned}
\]

For fixed \(k\), the final two terms are constant. A zero-one knapsack with
item weight \(n_a\) and value \(V_a\) therefore computes the best subset at
that weight. Scanning all reachable \(k\), together with the empty value zero,
proves the displayed optimum.

Process symbols in alphabet order. Update a knapsack cell only on strict
improvement, so equality inherits exclusion. Select the least extracted count
on a global equality. Store one inclusion bit for every item and reachable
weight plus the final weight. Backtracking gives the unique canonical subset.
The dynamic program uses \(O(|A|n)\) arithmetic operations, \(O(n)\) values,
and \(O(|A|n)\) certificate bits. Direct verification recomputes every
transition and tie.

For reconstruction, decode the complete category word first. Scan it from
left to right. A selected category emits its known symbol. A residual category
consumes the next symbol from the residual code. Feed either reconstructed
symbol to the parent predictor before proceeding. Induction on position shows
that encoder and decoder have the same prefix, predictor state, and next
probabilities, and reconstruct exactly \(x\).

The multinomial calculation is a real-valued ideal length. A finite range
coder rounds probabilities, renormalizes, frames its streams, and finalizes
them. Its exact byte length need not equal
\(\lceil\log_2M(S)\rceil\). The frozen application must therefore replay its
actual integer coder and receives no credit from the ideal objective alone.
