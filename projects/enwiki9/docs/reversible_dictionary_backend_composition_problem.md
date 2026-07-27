# Reversible Dictionary-Backend Composition

## Independent finite problem RDC-1

Let \(X,S,D,A\) be finite byte-string sets. A deterministic preprocessor
produces

\[
P:X\to D\times S
\]

and a deterministic inverse \(U:D\times S\to X\) satisfies
\(U(P(x))=x\). A backend compressor \(C:S\to A\) has deterministic inverse
\(V:A\to S\) satisfying \(V(C(s))=s\).

1. Construct a canonical self-delimiting archive containing \(d\in D\) and
   \(C(s)\), with fixed magic and fixed-width big-endian lengths.
2. Prove exact reconstruction and deterministic second-archive identity.
3. Give the exact total archive and counted-score equations.
4. Extend the construction through any canonical bijective symbol layout
   \(L:S\leftrightarrow B\).
5. For an alphabet of size \(K\), prove the minimum fixed-width symbol
   representation is \(\lceil\log_2K\rceil\) bits, but explain why minimum
   physical width does not imply minimum backend codelength.
6. Prove that a reversible deterministic representation creates no new source
   information; any gain comes from model fit, framing, or implementation.
7. State a finite certificate and an enwiki9 transfer reduction.

The problem is independent of any particular corpus or compressor.

## Organizer-owned transfer reduction

Instantiate \(P,U\) with official NNCP `pc/pd`, \(S\) with its canonical
big-endian 16-bit symbol stream, and \(C,V\) with frozen B2 cmix21. The learned
dictionary is transmitted inside the archive. Source packages for both
programs are counted. The candidate is target-bearing only if native archive
savings repay the entire additional package and target debt.
