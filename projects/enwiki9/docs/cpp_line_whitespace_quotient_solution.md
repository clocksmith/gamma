# LPWQ-1: Complete Solution

## Q1. Totality and idempotence

The hypotheses partition every physical line into protected and unprotected
lines. Protected lines have the unique image equal to themselves.

On an unprotected line, the finite scanner has three states: ordinary text,
string literal, and character literal. Escapes consume the immediately
following byte inside either literal. Well-formedness guarantees that the
scanner returns to ordinary text before the physical newline. Every byte is
therefore consumed exactly once, so the map is deterministic and total.

After one application, every horizontal-whitespace run outside literals on an
unprotected line is either absent at a boundary or is one ASCII space between
non-whitespace bytes. A second application makes no change. Protected lines
were already fixed. Hence

```text
W(W(S)) = W(S).
```

## Q2. Translation preservation

The construction copies every physical newline. It therefore preserves line
count. It copies every directive or ordinary continuation group byte-for-byte,
so translation-phase-two line splicing is identical on every protected group.
The exclusion of `??/` prevents an unrecognized trigraph from creating another
splice.

Consider an unprotected line after splicing. Literal bytes are copied exactly.
Outside literals, every non-whitespace byte is copied in order. Any whitespace
that separated two surrounding byte sequences remains one separating space.
Leading and trailing whitespace cannot create a preprocessing token. Thus the
ordered preprocessing-token sequence is unchanged.

Every corresponding token remains on the same physical line because no
newline is inserted or removed. Consequently `__LINE__` expands to the same
integer. Directive replacement lists are unchanged. For a macro argument,
C/C++ stringification discards leading and trailing whitespace and replaces
each internal whitespace sequence between preprocessing tokens by one space.
That is exactly the normal form produced by `W`, so stringification is
unchanged.

## Q3. Archive construction

Process USTAR members in their supplied order. Reject non-regular members.
Copy each header, name, mode, ownership field, timestamp, and ineligible
payload. For an eligible member, replace only its payload by `W(payload)`,
update its size and USTAR checksum, and retain canonical block padding.

All operations are finite and deterministic. Repeating the transform leaves
every eligible payload unchanged by Q1, so the archive payload map is
idempotent.

The source map is intentionally a quotient and is not byte-reversible.
Transfer does not require recovering discarded whitespace. The certificate
binds the parent closure, transformed closure, compiler invocation, executable,
and dictionary. Exact output hashes prove that both closures select the same
frozen runtime representative.

## Q4. Codec transfer

Let `R` and `R'` be the runtime pairs produced by the two packages. Exact
executable and dictionary identity gives `R = R'` byte-for-byte. The wrappers
and invocation environment are also identical. For any input, both packages
therefore invoke the same deterministic executable with the same mode,
dictionary, input bytes, and environment. Their output bytes are equal.
Compression and decompression functions coincide.

Write archive length as `A(x)`. Since `A'(x) = A(x)`, complete counted scores
are

```text
score(x)  = A(x) + P
score'(x) = A(x) + P'.
```

Subtracting gives

```text
score'(x) - score(x) = P' - P.
```

Without deterministic build identity, equal preprocessing tokens are
insufficient for this transfer claim. Compiler nondeterminism, paths,
timestamps, environment-dependent headers, or undefined behavior may alter
the executable. In that case the transformed package requires an independent
native codec proof and receives no inherited archive or score claim.

## Frozen enwiki9 instance

The canonical transformer processed 73 closure members and transformed 70
source members. It reduced eligible source bytes from 640,568 to 538,268 and
the USTAR closure from 1,146,880 to 1,044,480 bytes. Raw-LZMA2 payload size
fell from 284,583 to 277,064 bytes, saving 7,519 bytes.

Two independent clean builds produced:

```text
executable bytes: 837176
executable SHA-256:
5913ac6c77b875f5871391db08fb01be3ecb9fff8db9dbc203a5c94bfe624adb

dictionary bytes: 411996
dictionary SHA-256:
4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a
```

Both outputs equal the parent CQQ-1 outputs exactly. The unchanged wrapper is
2,808 bytes, so the counted package is 279,872 bytes. This saves 7,519 bytes
against CQQ-1 and 284,274 bytes against B2 package accounting.

The result is a constructive package proxy with zero score credit until its
native gate produces an exact archive, roundtrip, deterministic second
archive, runtime, and memory receipt.

