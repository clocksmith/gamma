# Solution: Slack-Carrier Literal Embedding

## In-place construction

Let the member data block begin at offset \(d\) and its header at offset \(h\).
Write \(E(M,L)\) at \(d\), fill the remainder of the already allocated payload
block with zero padding, replace the logical size field in the header, and
recompute the header checksum with the checksum field treated as spaces.
Every byte before \(h\), between the header and data block as prescribed by the
format, and after the existing allocated data block remains unchanged.

Because \(|E(M,L)|\le s+p\), no later member moves and total container length
is unchanged.

## Decoding and semantic identity

A conforming container reader uses the updated size and checksum, returns
exactly \(E(M,L)\), skips the remaining block padding, and reaches every later
member at its original offset. A unique marker and fixed parsing rule recover
\(L\) exactly.

Require the original consumer to treat the extension as semantically ignored.
For a Makefile carrier, a fresh line beginning with `#` is a comment; require
the marker not to continue a prior recipe or escaped line. Then the effective
build graph and commands are unchanged.

Relate parent and child wrapper states after extraction. The child Makefile has
the ignored extension, all other files agree, and the child reads exactly
\(L\). Replacing the source literal by those recovered bytes preserves the
effective build label. Deterministic build and run transitions therefore
produce equal executable and output bytes.

## Exact economics

Although raw container length is unchanged, a global codec can assign a
different length to any byte change. Let parent and child wrappers be
\(W,W'\), and parent and child compressed containers be \(C(A),C(A')\). Then

\[
\Delta P=
(|W'|-|W|)
+(|C(A')|-|C(A)|).
\]

The construction is beneficial exactly when \(\Delta P<0\). The slack theorem
removes a framing-growth term but does not predict the global codec delta.
That delta must be measured by exact re-encoding. If a finite codec family is
allowed, every committed family member must be evaluated again on \(A'\).

## Certificate

The certificate contains:

1. parent and child raw-container hashes and equal lengths;
2. member header/data offsets, old and new logical lengths, and slack;
3. literal and marker hashes;
4. proof that all bytes outside the allocated carrier regions agree;
5. codec-family commitment, every re-encoding result, selected member, and
   exact decode;
6. wrapper lengths and hashes;
7. restored executable and model hashes.

This proves a constructive package reduction. Native archive identity,
roundtrip, deterministic replay, runtime, memory, and full score remain
separate obligations.

## Frozen NNCP result

The `788`-byte Makefile occupies a `1024`-byte tar data block. Appending the
`145`-byte marker and evaluated flags leaves `91` slack bytes, changes no byte
outside that member's header and allocated data block, and preserves the raw
tar length at `819200` bytes.

All `377` committed XZ family members were re-evaluated. The new exact minimum
is:

```text
dict=800KiB,lc=4,lp=0,pb=0,mode=normal,nice=112,mf=bt2,depth=256
```

Its payload is `233012` bytes, only `12` bytes above the parent. The wrapper
falls from `1099` to `1007` bytes, so the complete package falls from `234099`
to `234019` bytes, an exact `80`-byte saving.

The restored normalized artifacts remain identical:

- `nncp`: `144904` bytes,
  SHA-256 `fed2ef59612c08077572983d70278211b76755d67910b293bb23aa11f1252fe5`;
- `libnc.so`: `565336` bytes,
  SHA-256 `1836cdfde987885e542cb88847cc58c9abefb0ef59a511ea9540dcbe46ac6d3e`.

This is a constructive package proxy. The smaller successor replaces the
parent's pending native T4 gate and retains zero score credit until that gate
passes.
