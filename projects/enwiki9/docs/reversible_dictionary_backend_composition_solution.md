# Solution to RDC-1: Reversible Dictionary-Backend Composition

Fix magic \(M\), and let \(\operatorname{be}_w(n)\) be the canonical
\(w\)-byte big-endian encoding of \(n\). For widths large enough for every
allowed string, define

\[
E(x)=M\Vert\operatorname{be}_w(|d|)\Vert
\operatorname{be}_w(|a|)\Vert d\Vert a,
\]

where \((d,s)=P(x)\) and \(a=C(s)\).

The decoder checks \(M\), reads the two lengths, rejects trailing or missing
bytes, splits \(d,a\), computes \(s=V(a)\), and emits \(U(d,s)\). Therefore

\[
U(d,V(C(s)))=U(d,s)=x.
\]

Every operation and framing field is deterministic, so a second encoding of
the same input is byte-identical whenever \(P\) and \(C\) are deterministic.
The exact archive length is

\[
\boxed{|E(x)|=|M|+2w+|d|+|C(s)|},
\]

and the Hutter-style counted total is this length plus every required program,
backend, dictionary-independent table, source, and wrapper byte.

For a bijection \(L:S\leftrightarrow B\), replace the backend pair by
\(C(L(s))\) and \(L^{-1}(V(a))\). The same inverse proof applies.

An alphabet with \(K\) symbols has \(K\) one-symbol possibilities. An
injective fixed-width code therefore needs \(b\) with \(2^b\ge K\), and the
binary rank attains

\[
\boxed{b=\lceil\log_2K\rceil}.
\]

This counting result says nothing about a byte backend's codelength: bit
packing changes boundaries, contexts, and conditional distributions. The
native backend must decide that interaction.

Since \(P\) is injective on valid inputs, \(X\) and its image under \(P\) are
in bijection. A deterministic reversible transform preserves the information
needed to identify \(x\); it can only expose that information in coordinates a
finite model handles better or worse. Dictionary and framing costs remain
real.

A finite certificate binds the exact preprocessor and backend hashes, symbol
byte order, magic, widths, dictionary bytes, source input hash, transformed
hash, backend archive hash, decoded hash, and deterministic second archive.
The transfer is valid only after exact roundtrip, package accounting, native
archive replay, memory, runtime, and distant/full-corpus gates. Proxy shortening
or ideal loss receives zero credit.
