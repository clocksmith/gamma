# FE-1: Paid Symbol-Fiber Extraction

## Problem

Let \(x=x_1\ldots x_n\) be a word over a finite alphabet \(A\). For each
\(a\in A\), define its fiber

\[
F_a=\{i\in\{1,\ldots,n\}:x_i=a\},
\qquad n_a=|F_a|.
\]

Suppose a baseline code assigns a nonnegative integer cost \(c_i\) to
position \(i\). A selected symbol \(a\) is removed from the baseline stream.
Its value is transmitted once, and its complete fiber is transmitted by the
lexicographic rank of \(F_a\) among all \(n_a\)-subsets of
\(\{1,\ldots,n\}\).

For each selected symbol, charge a fixed description price \(d_a\) bits and
the exact fixed-length fiber price

\[
r_a=\left\lceil\log_2 {n\choose n_a}\right\rceil.
\]

For a selected set \(S\subseteq A\), define the net ideal gain

\[
G(S)=
\sum_{a\in S}
\left(
\sum_{i\in F_a}c_i-d_a-r_a
\right).
\]

Prove:

1. The fibers \(F_a\) form a unique disjoint partition of
   \(\{1,\ldots,n\}\).
2. A fiber of known cardinality \(n_a\) has a canonical rank in
   \(\{0,\ldots,{n\choose n_a}-1\}\), and
   \(\lceil\log_2{n\choose n_a}\rceil\) fixed-length bits are necessary and
   sufficient in the worst case.
3. The unique inclusion-minimal maximizing set is

   \[
   S^*=
   \left\{
   a:
   \sum_{i\in F_a}c_i>d_a+r_a
   \right\}.
   \]

4. Given the selected values, cardinalities, fiber ranks, and the residual
   unselected subsequence, reconstruct \(x\) exactly by a deterministic
   left-to-right procedure.

The theorem concerns the stated independent fixed-length fiber code. It does
not claim optimality among joint multinomial, arithmetic, or distributional
codes.
