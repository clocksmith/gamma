# Solution to the Bootstrap Prefix Dictionary Problem

Status: complete constructive solution
Version: `BPD-1-SOLUTION`

## Canonical learner

A left-to-right scan partitions the finite prefix into maximal ASCII-letter
intervals. Lowercasing is a coordinatewise map with explicit byte semantics.
The scan therefore produces finitely many normalized tokens. Frequency and
first offset are exact integers. The key

\[
(-f(w),a(w),w)
\]

is a total order because distinct tokens differ in the last coordinate if the
first two coordinates tie. Selecting its first \(K\) elements and appending a
newline to each is consequently finite and deterministic.

## Decoder and inverse

The decoder validates the magic and four lengths, rejects trailing or missing
bytes, and splits the payload accordingly. It computes

\[
P=R_\bot(A_P).
\]

It checks the decoded prefix length, constructs \(D=L_K(P)\), and computes

\[
S=R_D(A_S).
\]

It returns \(P\|S\) after checking the declared total length. Component
inverse laws give

\[
R_\bot(E_\bot(P))=P,\qquad
R_{L_K(P)}(E_{L_K(P)}(S))=S,
\]

so the returned string is exactly \(X\). Empty parts use empty component
payloads and do not alter the proof.

## Determinism

The split point, learner, frame fields, and concatenation order are
deterministic. If both component encoders are deterministic, every byte of
the archive is a deterministic function of \(X,m,K\). Re-encoding the decoded
string therefore reproduces the identical archive.

## Accounting

For a header of \(h\) bytes,

\[
|A_{\rm new}|=h+|E_\bot(P)|+|E_{L_K(P)}(S)|.
\]

The learned dictionary contributes no archive or package bytes because both
sides rebuild it from \(P\). Its construction code is counted in the package.
If the old package includes a static dictionary of \(d\) bytes and the new
non-dictionary code grows by \(c\), then

\[
T_{\rm new}-T_{\rm old}
=
(|A_{\rm new}|-|A_{\rm old}|)+c-d.
\]

Thus \(T_{\rm new}<T_{\rm old}\) exactly when

\[
|A_{\rm new}|-|A_{\rm old}|<d-c.
\]

There is no proxy or asymptotic substitution in this criterion.

## Causality

The suffix decoder starts only after \(P\) has been decoded. Every dictionary
entry, order coordinate, and serialized byte is a deterministic function of
that visible prefix. No suffix byte or untransmitted encoder state enters
\(L_K(P)\).

## Finite verifier

The verifier rescans the declared prefix, recomputes all token counts and
first offsets, sorts by the fixed key, checks the exact dictionary bytes,
checks frame arithmetic, applies both component inverses, compares the result
with \(X\), then runs the deterministic encoder again and compares every
archive byte. All sets and strings are finite, so the verifier terminates.

The theorem guarantees reversibility and exact economics for a supplied
backend. It does not guarantee that the learned dictionary compresses the
suffix well enough to satisfy the displayed inequality; that is a native
measurement obligation.

