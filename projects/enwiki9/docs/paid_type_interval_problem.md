# TI-1: Paid Ordered Type-Interval Coding

## Problem

Let \(M\ge1\). Cell \(j\in\{0,\ldots,M-1\}\) contains a finite ordered
binary sequence. For an interval \(I=[a,b]\), concatenate the sequences in
their original global occurrence order and define:

\[
N_I=\text{number of outcomes},\qquad
E_I=\text{number of ones}.
\]

Let \(C_I\) be the baseline cost, in integer quanta, of those outcomes. A
type-interval code transmits:

1. a fixed \(d\)-bit interval descriptor;
2. \(E_I\);
3. the lexicographic rank of the length-\(N_I\), weight-\(E_I\) binary
   sequence.

Assume the descriptor price includes the endpoint and count fields. Define

\[
R_I=\left\lceil\log_2{N_I\choose E_I}\right\rceil
\]

and, for a fixed quantum scale \(Q\),

\[
W_I=C_I-Q(d+R_I).
\]

Only pairwise disjoint cell intervals may be selected. Prove:

1. The fixed-weight outcome sequence has a canonical rank using exactly
   \(R_I\) fixed-length bits in the worst case.
2. The recurrence

   \[
   D(t)=\max\left(
   D(t-1),
   \max_{0\le a<t}\{D(a)+W_{[a,t-1]}\}
   \right),
   \qquad D(0)=0,
   \]

   returns the maximum total weight of disjoint intervals contained in
   \(\{0,\ldots,t-1\}\).
3. Preferring the skip branch on ties and then the least left endpoint gives
   a deterministic inclusion-minimal optimum.
4. If cell membership is computable before each outcome and all selected
   descriptors and ranks are transmitted first, a decoder can reconstruct
   the original sequence left to right, even when selected interval streams
   are interleaved in time.

State exact \(O(M^2)\) time and \(O(M)\) dynamic-programming storage bounds,
excluding storage of the supplied cell statistics.
