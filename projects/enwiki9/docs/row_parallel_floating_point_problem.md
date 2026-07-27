# Row-Parallel Floating-Point Equivalence Problem

Status: independent constructive problem
Version: `RPF-1`

## Given

Fix one floating-point format, rounding mode, exception mode, and deterministic
scalar operation \(\operatorname{fl}\). For matrices \(A,B\), define every
output coordinate by the ordered recurrence

\[
s_0=0,\qquad
s_{k+1}=\operatorname{fl}\!\left(
s_k+\operatorname{fl}(A_{ik}B_{kj})
\right),
\qquad
Y_{ij}=s_n.
\]

A serial evaluator computes output coordinates in lexicographic \((i,j)\)
order. A parallel evaluator partitions the output-coordinate set among
workers. Each worker computes its assigned coordinates using the identical
ordered recurrence and writes only those coordinates. A barrier occurs before
any consumer reads \(Y\).

## Questions

1. Prove bitwise equality of every output coordinate under the serial and
   parallel evaluators.
2. Extend the proof to a finite acyclic graph whose nodes are row-separable
   matrix products or coordinatewise deterministic operations, with a barrier
   between dependent nodes.
3. Extend it to gradients and parameter updates when every reduction retains
   its exact within-coordinate order and updates occur after a barrier.
4. Give a finite ownership-and-order certificate and verifier.
5. Show by counterexample why partitioning a single dot-product reduction or
   changing its parenthesization is not covered.
6. State the exact evidence required before applying the theorem to a closed
   numerical library.

