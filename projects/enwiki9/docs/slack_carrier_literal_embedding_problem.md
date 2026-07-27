# Slack-Carrier Literal Embedding

## Status

`SCLE-1` is an independent finite-object problem. It embeds a fixed literal in
unused alignment slack of an existing framed member, so wrapper source can
read the literal without adding a new frame block.

## Definitions

Let a finite container consist of fixed \(B\)-byte headers followed by member
payloads padded to multiples of \(B\). A member \(M\) has logical length \(s\)
and occupies

\[
B\left\lceil\frac{s}{B}\right\rceil
\]

payload bytes. Its unused slack is

\[
p=B\left\lceil\frac{s}{B}\right\rceil-s.
\]

Let \(L\) be a literal and \(E(M,L)\) a deterministic extension with

\[
|E(M,L)|\le p.
\]

Assume the consumer of \(M\) ignores the extension semantically, while a
wrapper can recover \(L\) from a unique marker in the extended bytes. The
container is subsequently encoded by a deterministic injective codec \(C\).

## Questions

1. Construct the extended member header, checksum, payload, and padding while
   preserving total container length and every byte outside the member header
   and allocated payload block.
2. Prove exact container decoding and literal recovery.
3. State sufficient conditions under which the original consumer has
   identical behavior on \(M\) and \(E(M,L)\).
4. Prove wrapper equivalence when the source literal is replaced by the
   recovered carrier literal.
5. Derive the exact package change after globally re-encoding the modified
   container with \(C\).
6. Explain why unchanged container length does not imply unchanged compressed
   length.
7. Give a finite certificate and the additional native evidence required for
   compression-score transfer.

## Frozen intended instance

The container is the `819200`-byte NNCP source tar. `Makefile` has logical
length `788` and `236` bytes of slack in its allocated tar data block. The
carrier is a Make comment containing the `140`-byte evaluated CFLAGS literal.
The parent compressed payload is the exact minimum of a committed 377-member
XZ family.

