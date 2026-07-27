# Solution to SCC-1: Source-Closure Compilation

Status: complete constructive solution
Version: `SCC-1-SOLUTION`

The canonical archive is a finite sequence of fixed-format headers and file
bytes in a supplied total order. Fixed paths, lengths, modes, owners, and
times remove metadata ambiguity. Parsing those headers recovers each boundary
and path. Injectivity of \(C\) and the identity
\(C^{-1}(C(U(F)))=U(F)\) therefore recover every original byte string.

A verifier rejects absolute paths, parent components, duplicates, nonregular
members, unexpected names, lengths, modes, owners, or times. It decodes the
payload, compares the complete recovered manifest, creates two empty build
directories, invokes the frozen build map in each, and computes ELI-1 loader
projections of both outputs. Every operation ranges over finite files and
terminating build receipts.

If a clean output has the same loader projection as \(E\), ELI-1 gives the
same initial mapped process image and entry point. Under equal arguments,
environment, libraries, inputs, deterministic execution, and nonintrospection,
machine-state induction gives identical outputs and exit status. Two clean
builds may differ in section tables or other nonprojected metadata; equality
of both loader projections with \(E\) proves that such differences are outside
the execution state admitted by the hypotheses.

Let parent and successor complete package lengths be \(P\) and \(P'\), and
their common archive length be \(A\). Their counted totals are \(A+P\) and
\(A+P'\), so the exact score delta is

\[
(A+P')-(A+P)=P'-P.
\]

The theorem does not make a compiler available, bound its runtime, prove that
the frozen source is a complete closure on another host, or establish native
archive identity on its own. Build execution, exact encode/decode, deterministic
re-encode, peak memory, runtime, and the final full-corpus count remain
mandatory measured receipts.
