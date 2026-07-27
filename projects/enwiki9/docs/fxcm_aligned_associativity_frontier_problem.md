# AF-1: The Aligned Associativity Frontier

## Status

Independent finite mathematics problem. Its solution licenses a finite candidate
family; it does not supply compression credit without native replay.

## Problem

Let a hash-table bucket contain \(A\) ways, where

\[
A\in\{1,\ldots,14\}.
\]

Each way requires one two-byte fingerprint and seven one-byte predictor states.
Each bucket also requires one shared byte. Buckets are allocated with 32-byte
alignment, so the physical bytes per bucket are

\[
c(A)=32\left\lceil\frac{9A+1}{32}\right\rceil.
\]

For a fixed hash range, define normalized memory and capacity by

\[
M(A)=c(A),\qquad K(A)=A.
\]

Say that \(A'\) dominates \(A\) when

\[
M(A')\le M(A),\qquad K(A')\ge K(A),
\]

with at least one strict inequality.

Solve all clauses.

1. Compute \(c(A)\) for every \(A\in\{1,\ldots,14\}\).
2. Determine the complete set of undominated associativities.
3. Prove that every omitted associativity is dominated.
4. For each undominated value, give its exact memory and capacity ratios
   relative to \(A=14\).
5. Let \(B_i\) be the fixed number of buckets in table \(i\), and let
   \(A_i\) be chosen independently from the undominated set. Given an integer
   memory budget \(R\), nonnegative integer penalties \(d_i(A)\), and the
   baseline \(A_i=14\), construct a finite exact algorithm minimizing

   \[
   \sum_i d_i(A_i)
   \]

   subject to

   \[
   \sum_i B_i c(A_i)\le R.
   \]

6. Prove that the algorithm returns the lexicographically first minimizer under
   a fixed table order and fixed associativity order.
7. Explain exactly what additional empirical evidence is required before the
   selected allocation can affect a compression score.

## Canonical conventions

- Associativities are ordered \(14,12,10,7,3\).
- In a tie, prefer the lexicographically first vector in that order.
- All costs and budgets are exact integers.
- \(+\infty\) denotes a forbidden option.

