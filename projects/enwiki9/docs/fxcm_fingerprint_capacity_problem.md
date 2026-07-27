# FP-1: Fingerprint-Capacity Packing

## Status

Independent finite mathematics problem with an explicit cmix21 transfer. A
solution defines physical candidate layouts; it does not establish predictive
gain.

## Problem

A set-associative predictor bucket contains \(A\) ways. Each way stores seven
one-byte predictor states and one \(b\)-bit fingerprint. The fingerprints are
packed consecutively without padding. The bucket also stores one shared byte,
and the allocator rounds every bucket to a multiple of 32 bytes.

Define

\[
R(A,b)=7A+1+\left\lceil\frac{Ab}{8}\right\rceil
\]

and

\[
C(A,b)=32\left\lceil\frac{R(A,b)}{32}\right\rceil.
\]

Solve all clauses.

1. For a positive multiple \(Q\) of 32, prove an exact necessary and sufficient
   condition for \(C(A,b)\le Q\).
2. Derive the largest feasible associativity \(A_{\max}(Q,b)\).
3. Derive the largest feasible fingerprint width \(b_{\max}(Q,A)\).
4. Classify the maximum-associativity layouts using \(b=16\) for
   \(Q\in\{32,64,96,128\}\).
5. Show that eleven ways fit in 96 bytes exactly when \(b\le13\), and that
   twelve ways cannot fit even with \(b=7\).
6. Assume a query fingerprint and the \(A\) resident fingerprints are
   independent and uniform in \(\{0,\ldots,2^b-1\}\). Derive the exact
   probability of at least one false fingerprint match and a distribution-free
   union-bound expression conditional on those assumptions.
7. Compare the false-match ceilings of \((A,b)=(10,16)\) and \((11,13)\).
8. State the exact transfer boundary between this theorem and a valid
   compression result.

All integer encodings, packing order, and tie rules are canonical and fixed
before any compression measurement.

