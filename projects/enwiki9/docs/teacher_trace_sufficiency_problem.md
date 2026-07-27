# TS-1: Sufficient Teacher Traces

## Status

Independent finite information problem. Its transfer target is the next NNCP
distillation trace contract.

## Problem

Let \(V\ge3\). A teacher emits a probability vector

\[
p\in\Delta_V
\]

and the realized symbol is \(y\). A scalar trace records only

\[
(y,p_y).
\]

Solve all clauses.

1. Prove that the scalar trace does not identify the teacher distribution.
2. Construct two teachers with the same scalar trace whose tail supports are
   disjoint.
3. Prove a minimax lower bound on the KL regret of any student distribution
   chosen using only that scalar trace.
4. If teacher probabilities are positive integer frequencies summing to \(Q\),
   count the number of possible vectors and derive an information lower bound
   for exact identification.
5. Define a top-\(k\)-plus-tail trace and identify a restricted student family
   for which it is a sufficient statistic for teacher cross-entropy.
6. State what additional information is needed for unrestricted distillation.
7. Apply the result to the existing 10,000-symbol NNCP trace.

All symbol orders and ties are canonical.

