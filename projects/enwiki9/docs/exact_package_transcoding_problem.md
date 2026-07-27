# Exact Package Transcoding Problem

Status: independent constructive problem
Version: `EPT-1`

## Given

Let a deterministic compressor program be a finite tuple

\[
\Pi=(W,C,D_1,\ldots,D_r),
\]

where \(W\) is wrapper source, \(C\) is an executable payload, and the \(D_i\)
are auxiliary byte strings. Before compression or decompression, \(W\)
recovers each payload by a total deterministic decoder \(U_i\).

For each \(i\), let \(Z_i\) and \(Z'_i\) be two finite package encodings such
that

\[
U_i(Z_i)=U'_i(Z'_i).
\]

Assume the old and new wrappers differ only by selecting \(U_i,Z_i\) versus
\(U'_i,Z'_i\), and pass the recovered bytes to the same program interfaces in
the same order.

## Questions

1. Prove extensional identity of compression and decompression for every
   input, including identical archive bytes.
2. Prove deterministic second-archive identity transfers from the old package
   to the new package.
3. Give a finite verifier requiring hashes of every recovered payload and a
   canonical wrapper-difference certificate.
4. If old and new package lengths are \(P\) and \(P'\), prove the exact counted
   score change is \(P'-P\).
5. State precisely what is not proved about startup time, peak memory, library
   availability, and official eligibility.

