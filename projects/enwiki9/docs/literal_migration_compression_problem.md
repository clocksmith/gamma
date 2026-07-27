# Literal Migration Compression

## Status

`LMC-1` is an independent finite-object problem. It asks when moving a fixed
runtime literal from wrapper source into an already compressed immutable
closure reduces complete package size without changing execution.

## Definitions

Let \(A=((p_1,x_1),\ldots,(p_m,x_m))\) be an ordered finite path-payload
closure and let \(C\) be a deterministic injective codec on serialized
closures. A deterministic wrapper \(W\) contains a literal byte string \(L\)
and:

1. decodes \(C(A)\);
2. extracts \(A\) below a fresh private root;
3. uses \(L\) as one labeled argument in a deterministic build or run;
4. returns only the resulting output bytes.

Choose a fresh safe path \(p_*\) and define

\[
A'=A\mathbin{\|}(p_*,L).
\]

Construct \(W'\) by removing the source literal \(L\), decoding \(C(A')\), and
reading the bytes at \(p_*\) at the point where \(W\) used \(L\).

## Questions

1. State sufficient path-safety and freshness conditions for \(p_*\).
2. Prove exact recovery of \(A'\) from \(C(A')\).
3. Construct a path-alpha bisimulation between \(W\) and \(W'\) when the read
   literal equals \(L\) and every other effective transition label agrees.
4. Derive the exact complete-package change

   \[
   (|W'|+|C(A')|)-(|W|+|C(A)|).
   \]

5. Prove that migration is beneficial if and only if the wrapper reduction
   exceeds the compressed-closure increase.
6. Give a finite certificate for a frozen instance and distinguish package
   identity from native codec evidence.

## Frozen intended instance

The source wrapper is the `4303`-byte FCF/BPDQ B2 wrapper. \(L\) is its fixed
C++ build-flag string and \(p_*\) is `cmix21/.gamma_lflags`. The existing
raw-LZMA2 closure payload is `269306` bytes. No score credit follows without
restored executable/dictionary identity and a native archive gate.

