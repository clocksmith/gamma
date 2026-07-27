# IF-1: Mandatory-Positive Frequency Projection

## Status

Independent finite mathematics problem. Its transfer target is deterministic
integer arithmetic coding from neural symbol probabilities.

## Problem

Let

\[
p=(p_1,\ldots,p_V)
\]

be a probability vector, and let \(Q>V\) be an integer arithmetic-frequency
total. Every symbol must receive a positive integer frequency.

Define

\[
r_i=\left(1-\frac VQ\right)p_i+\frac1Q.
\]

Solve all clauses.

1. Prove that \(r\) is a probability vector and \(Qr_i\ge1\).
2. Construct canonical integers \(f_i\ge1\) summing to \(Q\) by the
   largest-remainder method.
3. Prove

   \[
   \left|\frac{f_i}{Q}-r_i\right|<\frac1Q.
   \]

4. Prove the pointwise lower bound

   \[
   \frac{f_i}{Q}\ge\left(1-\frac VQ\right)p_i.
   \]

5. Bound the excess ideal codelength for every true symbol.
6. Combine the result with an approximate-logit oscillation bound.
7. Derive a sufficient cumulative byte-margin inequality for \(N\) symbols.
8. State canonical tie rules and the exact transfer boundary to a native
   arithmetic archive.

All arithmetic used to compute the frequencies must be deterministic and
decoder-recomputable.

