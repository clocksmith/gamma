# BF-1: Amortized Prior-Block Fibers

## Problem

Partition a word into \(B\) aligned blocks of fixed length \(L\), plus a
literal tail. Blocks with equal contents form disjoint equivalence classes.
For a class \(C=\{i_0<i_1<\cdots<i_{m-1}\}\), retain \(i_0\) literally and
permit any subset \(T\subseteq C\setminus\{i_0\}\) to be copied from \(i_0\).

The class descriptor costs \(d\) bits. A selected set of size \(k\) is ranked
as a \(k\)-subset of the \(B-1\) nonsource block slots and costs

\[
R(k)=\left\lceil\log_2{B-1\choose k}\right\rceil
\]

bits. Target block \(i\) has baseline cost \(c_i\). Prove:

1. Equal-content classes uniquely partition the aligned blocks.
2. For fixed \(k\), the maximum-saving target set consists of the \(k\)
   largest \(c_i\) in the class, with smaller block index breaking ties.
3. Scanning \(k=1,\ldots,m-1\) and comparing

   \[
   \sum_{i\in T_k}c_i-d-R(k)
   \]

   with zero gives the exact inclusion-minimal optimum for that class.
4. Class optima combine independently because their target blocks are
   disjoint.
5. The selected class descriptors, target ranks, residual literal blocks,
   and literal tail reconstruct the original word exactly in one pass.

Give finite construction and complexity bounds.
