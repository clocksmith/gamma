# Solution: Literal Migration Compression

## Safe extension

Require that \(p_*\) is a nonempty relative path, has no `..` component, is not
absolute, and differs from every existing member path. Require extraction to
reject duplicate paths and to remain below a fresh private root. Then appending
\((p_*,L)\) preserves unique safe extraction.

Because \(C\) is injective on serialized closures, decoding \(C(A')\) recovers
the exact ordered path-payload list \(A'\). In particular, the extracted bytes
at \(p_*\) equal \(L\).

## Bisimulation

Relate wrapper states after extraction by the usual fresh-root alpha map.
Every original member has identical bytes at corresponding relative paths.
The child has one extra private file \(p_*\), which is unobservable except at
the migrated-literal read.

At that read, \(W'\) obtains exactly \(L\). Substitute those bytes for the
source literal in the next labeled transition. Its effective build or runtime
argument is then identical to \(W\)'s. By hypothesis every other transition
label agrees. Determinism and path-alpha invariance give identical executable,
model, dictionary, archive, and output bytes. Induction over the finite
transition trace proves observational equivalence on the fixed closure.

## Exact economics

The parent package size is

\[
P=|W|+|C(A)|
\]

and the child size is

\[
P'=|W'|+|C(A')|.
\]

Thus

\[
P'-P=
(|W'|-|W|)
+(|C(A')|-|C(A)|).
\]

Writing

\[
S_W=|W|-|W'|,\qquad
G_C=|C(A')|-|C(A)|,
\]

migration is strictly beneficial exactly when

\[
S_W>G_C.
\]

No entropy estimate or isolated-literal length can replace this measured
global inequality.

## Certificate

The finite certificate contains:

1. parent and child wrapper bytes and hashes;
2. parent and child compressed-closure bytes and hashes;
3. decoded ordered-member hashes;
4. the fresh path and literal hash;
5. exact parent and child package sizes;
6. effective build/run labels;
7. restored executable and auxiliary-data hashes.

Those facts prove a constructive package reduction. Native archive equality,
roundtrip, deterministic replay, runtime, and memory remain separate evidence
before any Hutter score transfer.

## Frozen B2 result

The fixed build literal is `493` bytes. Appending
`cmix21/.gamma_lflags` increases the raw FCF frame from `941417` to `941936`
bytes, but the raw-LZMA2 payload grows only from `269306` to `269455` bytes.
The ordinary migrated wrapper is `3774` bytes, down from `4303`.

\[
(3774+269455)-(4303+269306)=-380.
\]

Thus LMC-1 alone saves exactly `380` counted package bytes.

Applying the already proved DWNF-1 wrapper normal form reduces the wrapper
further to `1885` bytes. The composed package is therefore

\[
1885+269455=271340
\]

bytes, saving `2269` bytes against the FCF parent. A clean build used
`337488` KiB peak RSS and reproduced:

- executable: `837176` bytes,
  SHA-256 `5913ac6c77b875f5871391db08fb01be3ecb9fff8db9dbc203a5c94bfe624adb`;
- dictionary: `411996` bytes,
  SHA-256 `4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a`.

This is a constructive package proxy. The final successor remains at zero
score credit until its queued native codec gate completes.
