# FE-1 Solution: Paid Symbol-Fiber Extraction

For every position \(i\), exactly one equality \(x_i=a\) holds. Hence the
sets \(F_a\) are pairwise disjoint and their union is
\(\{1,\ldots,n\}\). They are uniquely determined by \(x\).

Order the \(n_a\)-subsets of \(\{1,\ldots,n\}\) lexicographically by their
increasing element lists. This gives a bijection between possible fibers and

\[
\left\{0,\ldots,{n\choose n_a}-1\right\}.
\]

The standard combinatorial-number-system scan ranks and unranks the subsets
finitely and canonically. An injective fixed-length code of length \(L\) has
at most \(2^L\) words, so it requires

\[
L\ge\left\lceil\log_2{n\choose n_a}\right\rceil.
\]

Encoding the rank as a zero-padded binary integer attains this bound.

Define the independent contribution

\[
w_a=\sum_{i\in F_a}c_i-d_a-
\left\lceil\log_2{n\choose n_a}\right\rceil.
\]

Then

\[
G(S)=\sum_{a\in S}w_a.
\]

Every positive \(w_a\) must be included by any maximizer, every negative
\(w_a\) must be excluded, and zero-weight symbols may be chosen arbitrarily.
Consequently the inclusion-minimal maximizer is exactly

\[
S^*=\{a:w_a>0\}.
\]

For reconstruction, unrank every selected fiber first. Since true symbol
fibers are disjoint, reject any overlap. Scan positions from left to right.
If the current position belongs to a selected fiber, emit that fiber's
symbol. Otherwise consume and emit the next symbol of the residual
subsequence. At the end, require every residual symbol to have been consumed.
The partition property proves that the emitted word is exactly \(x\).

Thus the optimizer and inverse are finite, deterministic, and exact. The
result does not extend automatically to a joint code whose fiber prices
interact.
