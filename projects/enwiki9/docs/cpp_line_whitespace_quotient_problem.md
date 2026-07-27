# LPWQ-1: The Line-Preserving C++ Whitespace Quotient

## Status

This is an independent finite source-equivalence problem. Its public theorem
does not assume compression gain. The frozen enwiki9 transfer must separately
prove package reduction and exact build identity.

## Given

Let `S` be a finite ordered collection of byte strings representing C or C++
source files. Each file satisfies all of the following:

1. Comments outside literals have already been replaced by whitespace.
2. Raw string literals do not occur.
3. The trigraph `??/` does not occur.
4. Every preprocessing directive logical line is decidable from its first
   physical line and its backslash-newline continuations.
5. Ordinary backslash-newline continuation groups are finite.
6. Ordinary string and character literals are well formed.

Call a physical line protected when it belongs to either a preprocessing
directive continuation group or an ordinary backslash-newline continuation
group.

For each unprotected physical line, define `W` as follows:

1. Preserve every byte inside string and character literals.
2. Preserve every non-horizontal-whitespace byte outside literals.
3. Replace each maximal internal run from `{space, tab, vertical-tab,
   form-feed}` outside literals by one ASCII space.
4. Delete leading and trailing horizontal whitespace outside literals.
5. Preserve the physical newline exactly.

Protected physical lines are copied byte-for-byte.

## Questions

### Q1. Totality and idempotence

Prove that `W` is a deterministic total function on the stated domain and

```text
W(W(S)) = W(S).
```

### Q2. Translation preservation

Prove that each source file and its image under `W` have:

1. the same physical-line count;
2. identical protected logical-line groups;
3. identical literal contents;
4. the same preprocessing-token sequence after C/C++ translation phases
   one through three;
5. identical `__LINE__` values at corresponding tokens;
6. identical results for macro argument stringification.

### Q3. Archive construction

Given a canonical ordered USTAR closure, construct the canonical transformed
USTAR closure by replacing only eligible member payloads with their `W`
images. Prove that member order, names, metadata, and all ineligible payloads
are preserved, and that the construction has a deterministic inverse
certificate consisting of the original closure hash and exact build output
hashes.

The map need not reconstruct original source whitespace. It must reconstruct
the same frozen runtime artifact.

### Q4. Codec transfer

Let two source-building codec packages have identical wrappers, build flags,
compiler environment, runtime executable bytes, and dictionary bytes. Prove
that they define the same compression and decompression functions.

If their counted package sizes are `P` and `P'`, prove that for every input
whose archive is produced successfully,

```text
score' - score = P' - P.
```

State precisely which conclusions fail without deterministic build identity.

## Acceptance

A complete solution proves Q1 through Q4. A frozen transfer instance also
requires:

1. exact transformed payload bytes and SHA-256;
2. two independent clean builds;
3. exact identity with the parent executable and dictionary;
4. complete wrapper and payload accounting;
5. a native exact roundtrip gate before score credit.

