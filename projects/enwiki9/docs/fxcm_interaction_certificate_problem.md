# IC-1: Exact Intervention Interaction Certificates

## Status

Independent finite mathematics problem. Its transfer target is the selection of
simultaneous cmix21 table-layout interventions without invalidly adding
separately measured archive penalties.

## Problem

Let \(N=\{1,\ldots,n\}\). For every subset \(U\subseteq N\), let

\[
f(U)\in\mathbb Z
\]

be the exact measured cost of applying precisely the interventions in \(U\).
Define the Boolean-lattice Möbius coefficient

\[
\mu(S)=\sum_{T\subseteq S}(-1)^{|S|-|T|}f(T).
\]

Solve all clauses.

1. Prove the exact inversion formula

   \[
   f(U)=\sum_{S\subseteq U}\mu(S).
   \]

2. Define degree at most \(d\) by

   \[
   \mu(S)=0\quad\text{whenever }|S|>d.
   \]

   Prove that all coefficients of size at most \(d\) are recovered from the
   values \(f(T)\) with \(|T|\le d\), and count those required values.

3. Prove that, without a structural promise, those low-order observations
   cannot certify degree at most \(d\) on the whole cube.

4. Give a finite exact algorithm minimizing \(f(U)\) subject to an exact memory
   saving constraint

   \[
   \sum_{i\in U}m_i\ge M,
   \]

   assuming the degree-\(d\) promise is valid.

5. Derive the additive and pairwise special cases.

6. Define an exact residual for any audited set \(U\), and state what a
   nonzero residual proves.

7. State a fail-closed enwiki9 transfer protocol distinguishing a mathematical
   interaction model, an empirical screen, and a score-bearing native replay.

All costs, memories, subset orders, and tie rules are exact and frozen.

