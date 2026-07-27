# Independent Problem SCC-1: Source-Closure Compilation

Status: `FROZEN RESEARCH PROBLEM`
Version: `SCC-1`

## Given

Let \(F=(f_1,\ldots,f_r)\) be finite named byte strings in a fixed total path
order. A canonical archive \(U(F)\) writes each regular file with its supplied
path and bytes, mode \(0644\), zero time, zero owner identifiers, and no other
metadata. Let \(C\) be an injective finite coder with inverse \(C^{-1}\).

A frozen build map \(B_\theta\) takes the recovered files, a finite toolchain
descriptor \(\theta\), and no other variable input, and returns an ELF file.
Let \(E\) be a parent ELF file and let \(\Lambda\) be the loader projection
from ELI-1. Let \(W\) be a deterministic wrapper that invokes the recovered
build output and auxiliary payloads.

## Questions

1. Prove that \(C(U(F))\), the fixed archive convention, and \(C^{-1}\)
   recover every path and byte string uniquely.
2. Give a finite verifier for closure, path safety, archive recovery, and two
   clean invocations of \(B_\theta\).
3. Prove that
   \[
   \Lambda(B_\theta(F))=\Lambda(E)
   \]
   implies equal deterministic compressor and decompressor behavior under the
   ELI-1 hypotheses.
4. Prove that if two clean builds have the same loader projection as \(E\),
   then nondeterministic nonprojected build metadata cannot affect the codec
   result.
5. If the parent and source-built wrappers emit identical archives and
   reconstructions, derive the exact score delta from their complete package
   lengths.
6. State exactly why compiler availability, build time, native archive
   identity, peak memory, and full-corpus score remain measured obligations.

## Frozen enwiki9 transfer

The instance contains the B2 cmix21 source closure, build flags, English
dictionary, canonical USTAR representation, and raw LZMA2 coder. The first
native gate is 250K. Promotion requires two clean build projections, exact B2
archive identity, exact roundtrip, deterministic re-encode, and the decimal
memory guard. No source-size screen receives score credit.
