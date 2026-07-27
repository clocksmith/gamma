# FCF-1: Finite Path-Payload Closure Framing

## Given

Let

```text
C = ((p_1, x_1), ..., (p_n, x_n))
```

be a finite ordered collection where:

1. `0 <= n <= 65535`;
2. every `p_i` is a distinct nonempty UTF-8 relative POSIX path;
3. no path component equals `..`;
4. the UTF-8 length of each path is at most 65535;
5. each byte payload `x_i` has length at most `2^32 - 1`.

Define the frame:

```text
"FCF1"
u16be(n)
for i = 1..n:
    u16be(|utf8(p_i)|)
    u32be(|x_i|)
    utf8(p_i)
    x_i
```

## Questions

1. Construct a deterministic decoder and prove exact inversion.
2. Prove that record boundaries and end-of-frame are uniquely decidable.
3. Derive the exact frame length.
4. Give a path-safe extraction algorithm and prove it cannot write outside
   its designated root.
5. Prove that the frame preserves member order and payload identity while
   intentionally quotienting irrelevant USTAR metadata and padding.
6. If a source-building codec restores the same ordered path-payload closure
   before build, prove exact runtime and score transfer conditional on
   executable and dictionary identity.

## Frozen-transfer acceptance

The enwiki9 instance must count the complete frame payload and decoder wrapper,
prove all-member restoration, reproduce the frozen runtime, and pass native
archive, roundtrip, determinism, runtime, and memory gates before score credit.

