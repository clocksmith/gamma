# PO-1: Pooled Overflow for Uneven Buckets

## Status

Independent finite mathematics problem. Its transfer target is a
memory-bounded set-associative predictor with shared overflow capacity.

## Problem

There are \(B\) buckets. Bucket \(i\) contains \(n_i\) live entries, where

\[
0\le n_i\le A.
\]

Every bucket has \(a\) private slots, with \(0\le a\le A\). A shared overflow
pool contains \(P\) additional slots that may be assigned to any bucket. Each
entry occupies exactly one slot.

Solve all clauses.

1. Determine the minimum number of overflow slots required to retain every
   entry.
2. Determine the maximum number of entries retainable with a pool of size
   \(P\).
3. Let

   \[
   K=aB+P
   \]

   be the total number of slots. Prove that pooled allocation retains

   \[
   \min\left(\sum_i n_i,K\right)
   \]

   entries, and is therefore globally slot-optimal.
4. Compare this with a uniform unpooled capacity of \(k\) slots per bucket.
   Characterize exactly when the unpooled representation loses entries despite
   having at least as many total slots as live entries.
5. Give a canonical finite allocation and reconstruction algorithm.
6. Extend the theorem to nonnegative entry weights and give an exact finite
   optimizer for the maximum retained weight.
7. State which parts of the theorem fail to imply a compression gain when
   overflow entries require owner identifiers, links, alignment, lookup work,
   or different eviction semantics.

All bucket orders, entry orders, ties, and integer representations are fixed.

