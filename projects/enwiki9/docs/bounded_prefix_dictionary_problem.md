# BPDQ-1: Bounded Adjacent-Prefix Dictionary Coding

## Status

This is an independent finite coding problem. It concerns exact representation
of an ordered list and does not assume that the representation compresses
better after an outer coder.

## Given

Let

```text
D = (w_1, ..., w_n)
```

be a finite ordered list of byte strings containing no line-feed byte. Let
`lcp(w_{i-1}, w_i)` be the adjacent longest-common-prefix length, with
`w_0` empty. Assume

```text
0 <= lcp(w_{i-1}, w_i) <= 223.
```

Let `t` be one bit recording whether the original line serialization ends in
a line feed.

Define the record for `w_i` as:

```text
byte(32 + lcp(w_{i-1}, w_i))
suffix after that prefix
line feed
```

The complete representation is the four-byte magic `BPD1`, the byte `t`, and
the records in order.

## Questions

1. Construct deterministic encoders and decoders and prove they are mutual
   inverses.
2. Prove that record boundaries are unambiguous.
3. Derive the exact encoded length.
4. Prove that the maximum-LCP condition is a finite certificate verifiable
   while encoding.
5. Prove that replacing one member of a canonical USTAR closure by this
   representation and restoring it before use preserves every other member.
6. If the restored closure, wrapper, build flags, executable, and dictionary
   equal a parent codec package exactly, prove exact equality of compression
   and decompression functions and derive the score difference from package
   lengths alone.

## Frozen-transfer acceptance

The enwiki9 instance must additionally provide:

1. exact dictionary and encoded hashes;
2. exact decode identity;
3. complete transformed-payload and wrapper accounting;
4. exact restored-closure identity;
5. exact runtime artifact identity;
6. a native deterministic roundtrip receipt before score credit.

