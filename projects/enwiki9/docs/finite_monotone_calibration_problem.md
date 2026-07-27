# Independent Problem MC-1: Finite Monotone Bernoulli Calibration

Status: `FROZEN RESEARCH PROBLEM`
Version: `MC-1`

This problem is mathematically independent of the Atlas-Clockwork problems.
Its application is frozen separately and does not affect the theorem.

## Definitions

Let \(m\ge1\). For ordered cells \(i=1,\ldots,m\), let
\(a_i,b_i\in\mathbb Z_{\ge0}\), not both zero, count observed zeros and ones.
For \(p\in[0,1]\), define

\[
\ell_i(p)=-a_i\log_2(1-p)-b_i\log_2p,
\]

using the standard extended-real conventions at zero and one.

A monotone calibration is

\[
0\le p_1\le\cdots\le p_m\le1.
\]

Its loss is

\[
L(p_1,\ldots,p_m)=\sum_{i=1}^m\ell_i(p_i).
\]

For a nonempty interval \(I\), write

\[
A_I=\sum_{i\in I}a_i,\qquad
B_I=\sum_{i\in I}b_i,\qquad
\mu_I=\frac{B_I}{A_I+B_I}.
\]

## Questions

Prove all of the following.

1. An optimizer exists.
2. There is a unique vector of fitted probabilities, although its partition
   into adjacent equal-valued blocks need not be unique before equal blocks are
   merged.
3. The canonical coarsest optimizer is obtained by pool-adjacent-violators:
   begin with singleton blocks and repeatedly merge adjacent blocks whenever
   the left empirical mean is at least the right empirical mean.
4. Every final block \(I\) receives probability \(\mu_I\), and final block
   means are strictly increasing.
5. The result is independent of the order in which violating adjacent pairs
   are merged.
6. Give a finite certificate consisting of the final contiguous blocks, their
   counts, and fitted probabilities, and give necessary and sufficient local
   checks for optimality.
7. Let
   \[
   Q_M=\{1/M,2/M,\ldots,(M-1)/M\}.
   \]
   Replacing each final block mean by its smallest loss-minimizing member of
   \(Q_M\) preserves monotonicity. Prove this claim and characterize the
   minimizing grid point by comparing the two grid points adjacent to
   \(M\mu_I\), with endpoint clipping.
8. If consecutive fitted blocks acquire the same grid probability, prove that
   merging them preserves both monotonicity and quantized loss.

No numerical fitting or implementation is a solution.

## Frozen application gate

The application uses exactly 256 ordered bins of the parent q16 probability.
It trains the canonical coarsest fit on the first half of an exact native trace,
quantizes to \(Q_{65536}\), freezes the table, and range-codes the second half.
The table is charged three bytes per final block. The mechanism is promoted
only if net savings are at least 2,000 bytes per million raw bytes. Otherwise
global monotone recalibration is retired without alternate bin counts,
regularizers, or table budgets.
