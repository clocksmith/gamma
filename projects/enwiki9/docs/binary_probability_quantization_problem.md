# BQ-1: Clamped Binary Probability Quantization

## Status

Independent finite analysis problem. Its transfer target is NNCP's binary range
coder, whose pinned source uses

\[
Q=2^{15}=32768.
\]

## Problem

Let \(Q\ge3\), \(p\in[0,1]\), and define

\[
k(p)=
\min\left(Q-1,\max\left(1,\left\lfloor Qp+\frac12\right\rfloor\right)\right),
\qquad
q(p)=\frac{k(p)}Q.
\]

For outcome \(y\in\{0,1\}\), define binary log loss

\[
\ell(p,y)=
-y\log_2p-(1-y)\log_2(1-p).
\]

Solve all clauses.

1. Prove that \(1\le k(p)\le Q-1\).
2. Prove a global pointwise bound on the true-event probability ratio and
   excess log loss.
3. Give a sharper bound when the teacher's true-event probability is at least
   \(\alpha>1/(2Q)\).
4. Derive an expected Bernoulli KL bound under an interior-probability
   condition.
5. Combine probability quantization with an approximate binary logit.
6. Derive a cumulative byte-margin condition for \(N\) coded bits.
7. Specialize every exact constant to \(Q=32768\).
8. State the native-archive transfer boundary.

The rounding and tie rule are fixed and shared by encoder and decoder.

