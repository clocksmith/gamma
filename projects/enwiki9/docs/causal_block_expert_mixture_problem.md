# CBM-1: The Causal Block Expert-Mixture Problem

## Problem

Let a binary string be divided into finite blocks. In one block, write the
decoded bits as \(x_1,\ldots,x_n\). Let \(K\ge 1\), let
\(a_1,\ldots,a_K\) be positive integers, and put

\[
A=\sum_{k=1}^K a_k.
\]

Expert \(k\) supplies, before \(x_t\) is known, positive rational
probabilities

\[
p_{k,t}(b\mid x_{<t}),\qquad b\in\{0,1\},
\]

that sum to one. Define

\[
P_k(x_{1:n})=\prod_{t=1}^n p_{k,t}(x_t\mid x_{<t}).
\]

Solve the following independently of any compression corpus.

1. Construct one causal probability \(q_t(b\mid x_{<t})\) from the experts
   and the prior integers.
2. Prove the exact identity

   \[
   \prod_{t=1}^n q_t(x_t\mid x_{<t})
   =
   \frac1A\sum_{k=1}^K a_kP_k(x_{1:n}).
   \]

3. Deduce, for every expert \(k\), the regret inequality

   \[
   -\log_2 Q(x_{1:n})
   \le
   -\log_2P_k(x_{1:n})+\log_2(A/a_k).
   \]

4. Extend the construction to independently restarted blocks and state the
   resulting blockwise best-expert bound.
5. Prove that no expert label needs to be transmitted and that sequential
   decoding is deterministic.
6. Suppose every expert probability is represented by positive integer
   frequencies

   \[
   p_{k,t}(b\mid x_{<t})=r_{k,t}(b)/T,
   \qquad
   r_{k,t}(0)+r_{k,t}(1)=T.
   \]

   Give a canonical exact-integer procedure for computing the mixture
   probability. Prove that dividing all posterior numerators by their gcd
   changes no future mixture probability.
7. Quantize the mixture back to denominator \(T\) by a fixed nearest-integer
   rule with a fixed tie rule. Give an exact identity separating ideal mixture
   loss from quantization loss, and a universal per-bit upper bound.
8. State precisely what this theorem guarantees and what still requires an
   exact arithmetic-coder replay.

All logarithms are base two. A complete solution must be finite,
constructive, and independent of any other Atlas-Clockwork or Gamma problem.

## Hidden transfer reduction

For a frozen enwiki9 parent probability trajectory, a finite correction
codebook can be treated as the \(K\) experts. Restarting the theorem at fixed
decoder-visible block boundaries produces one causal payload without paid
per-block labels. The construction becomes target-bearing only after an exact
trace proves that the supplied expert family contains enough gain and a native
implementation counts its codebook, source, arithmetic bytes, runtime, and
memory.

