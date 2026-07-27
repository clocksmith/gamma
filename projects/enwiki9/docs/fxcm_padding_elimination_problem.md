# PE-1: Padding-Free State Serialization

## Status

Independent finite mathematics problem. Its transfer target is exact
archive-preserving compaction of fixed-width predictor records.

## Problem

Let

\[
X=X_1\times\cdots\times X_m
\]

be a finite logical record. Field \(i\) has a canonical fixed-width binary
encoding of \(b_i\) bits. Assume

\[
r=\sum_{i=1}^{m}b_i
\]

is divisible by eight. An aligned array representation uses \(s\) bytes per
record, where

\[
s>r/8.
\]

An algorithm evolves an array of \(B\) records by deterministic logical read
and write operations and emits predictions as a deterministic function of the
logical state.

Solve all clauses.

1. Construct a canonical bijection between \(X\) and an \(r\)-bit packed
   record.
2. Construct mutually inverse logical read and write operations on packed
   records.
3. Prove by induction that replacing the aligned representation with the packed
   representation preserves every logical state and prediction.
4. Deduce exact archive identity when encoder and decoder use the same
   deterministic coder.
5. Compute the exact payload saving for \(B\) records.
6. Specialize to a record with fourteen 16-bit fingerprints, ninety-eight
   one-byte predictor states, and one shared byte.
7. Explain why a language-level packed structure with unaligned integer
   references is not by itself a correctness proof.
8. State the complete enwiki9 transfer requirements.

All field orders, bit orders, endianness, and update rules are frozen.

