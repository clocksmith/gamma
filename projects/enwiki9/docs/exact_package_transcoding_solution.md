# Solution to the Exact Package Transcoding Problem

Status: complete constructive solution
Version: `EPT-1-SOLUTION`

For every package payload, the hypothesis gives bytewise equality after
recovery:

\[
U_i(Z_i)=U'_i(Z'_i).
\]

The wrappers pass these equal byte strings to equal interfaces in equal order.
Determinism and substitution of equals therefore make every subsequent state,
system call argument, probability, coder transition, and output byte equal.
Thus compression archives are identical and decompression outputs are
identical for every input.

If the old compressor is deterministic, two old executions have equal
recovered payloads and equal archives. The new package recovers those same
payloads, so two new executions also produce that archive. Deterministic
second-archive identity transfers.

A finite verifier decodes every old and new payload, checks lengths and
SHA-256 digests, and checks that the wrapper edit belongs to the frozen
grammar:

1. substitute the decoder module;
2. substitute the encoded payload suffix;
3. preserve recovered filenames, modes, arguments, and all remaining source.

All files are finite, so direct comparison terminates.

Let archive length be \(A(X)\), equal under both packages. Counted totals are

\[
T=A(X)+P,\qquad T'=A(X)+P'.
\]

Hence

\[
T'-T=P'-P.
\]

This is exact and requires no corpus projection.

The theorem does not prove that the new decoder library is available in the
submission environment, that its startup is fast enough, or that its
temporary and resident memory fit the rules. Those remain measured package
and resource obligations. It also does not license any wrapper edit outside
the frozen decoder-substitution grammar.

