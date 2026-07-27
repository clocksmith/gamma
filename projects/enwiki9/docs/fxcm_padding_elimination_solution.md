# PE-1 Solution: Padding-Free State Serialization

## 1. Canonical bijection

For field \(i\), let

\[
e_i:X_i\to\{0,1\}^{b_i}
\]

be its supplied canonical fixed-width bijection onto its legal codewords. Define

\[
\Phi(x_1,\ldots,x_m)
=
e_1(x_1)\Vert e_2(x_2)\Vert\cdots\Vert e_m(x_m),
\]

where \(\Vert\) denotes concatenation.

Because every field encoding is injective and its boundaries are fixed,
\(\Phi\) is injective. Splitting an \(r\)-bit string at the frozen boundaries
and applying each inverse \(e_i^{-1}\) reconstructs the unique logical record.
Thus \(\Phi\) is a bijection between \(X\) and the set of legal packed strings.

## 2. Logical accessors

Let

\[
o_i=\sum_{j<i}b_j
\]

be field \(i\)'s bit offset.

`read_i` extracts bits

\[
o_i,\ldots,o_i+b_i-1
\]

and applies \(e_i^{-1}\).

`write_i(v)` replaces exactly those bits by \(e_i(v)\), leaving every other bit
unchanged.

Therefore

\[
\operatorname{read}_i(\Phi(x))=x_i
\]

and

\[
\operatorname{write}_i(\Phi(x),v)
=
\Phi(x_1,\ldots,x_{i-1},v,x_{i+1},\ldots,x_m).
\]

The operations are mutually consistent and preserve all non-target fields.

## 3. State conjugacy

Let \(L_t\) be the complete logical array state after \(t\) updates in the
aligned implementation, and let \(P_t\) be the packed byte state. Initialize

\[
P_0=\Phi^{B}(L_0),
\]

where \(\Phi^{B}\) applies the encoding record by record.

Assume inductively that

\[
P_t=\Phi^{B}(L_t).
\]

Every logical read in the packed implementation returns the same field value by
the accessor theorem. Consequently both implementations choose the same
deterministic update and prediction. Every logical write produces exactly the
packed encoding of the aligned implementation's updated field. Hence

\[
P_{t+1}=\Phi^{B}(L_{t+1}).
\]

By induction, the relation holds for all \(t\), and every prediction is
identical.

## 4. Archive identity

If the encoder and decoder use the same deterministic arithmetic-coder
semantics, identical input histories and identical predictions imply identical
coder state after every symbol. Identical finalization then gives the same
archive bytes.

\[
\boxed{
\text{logical conjugacy}+\text{identical coder}
\Longrightarrow
\text{archive identity}.
}
\]

This is stronger than an equal-length claim.

## 5. Exact payload saving

The aligned array uses

\[
Bs
\]

bytes. The packed array uses

\[
B(r/8)
\]

bytes. Therefore the exact payload saving is

\[
\boxed{
B\left(s-\frac r8\right).
}
\]

This excludes allocator headers, array descriptors, and executable changes,
which must be counted separately.

## 6. ContextMap2 specialization

Fourteen 16-bit fingerprints require

\[
14\cdot2=28
\]

bytes. Ninety-eight predictor-state bytes and one shared byte give

\[
28+98+1=127
\]

logical bytes.

Against a 128-byte aligned cell, padding-free serialization saves exactly one
byte per bucket:

\[
\boxed{B\text{ bytes over }B\text{ buckets}.}
\]

It preserves all fourteen ways and all sixteen fingerprint bits.

## 7. Language-level safety

Declaring a C++ structure `packed` may create unaligned `uint16_t` objects.
Forming or dereferencing misaligned typed references may be undefined,
implementation-defined, or slower depending on the language and target.
Therefore a layout attribute alone does not establish the accessor identities
used in the proof.

A conforming implementation can use:

- explicit byte arrays;
- fixed shifts and masks; or
- `memcpy` between aligned scalar temporaries and packed bytes.

The generated values must use a frozen byte order. Compiler behavior and target
flags become part of the package evidence.

## 8. Transfer boundary

PE-1 licenses an archive-identical implementation only after Gamma verifies:

- every logical field is represented and no hidden padding is observed;
- all reads and writes use the proved accessors;
- exact per-event probabilities match the parent;
- coder-state hashes match;
- the final archive hash matches;
- roundtrip and deterministic second archive pass;
- measured RSS decreases after allocator effects;
- runtime remains eligible;
- source/package growth is counted.

If any prediction differs, PE-1's hypothesis was not instantiated and the
candidate becomes a score-changing model variant rather than an
archive-preserving compaction.

