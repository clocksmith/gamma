# BPDQ-1: Complete Solution

## Encoder and decoder

For each word, the encoder compares it with the preceding word and computes
the unique longest common prefix length `k`. It emits `32 + k`, the remaining
suffix, and line feed.

The decoder starts with the empty preceding word. For each record it subtracts
32 from the first byte to recover `k`, copies the first `k` bytes of the
preceding word, appends the remaining record bytes, and makes that word the
new predecessor. Finally it joins decoded words with line feeds and appends
one final line feed exactly when the header bit is one.

Induction on the record index proves inversion. If the preceding decoded word
equals the preceding input word, the stored prefix and suffix concatenate to
the current input word. The base predecessor is empty, so every word and the
final-newline state are recovered exactly.

## Unambiguous boundaries

The prefix byte lies in the interval 32 through 255 and therefore cannot equal
line feed. A suffix contains no line feed by hypothesis. Consequently each
line feed terminates exactly one record, and the first byte of every nonempty
record is uniquely the prefix byte.

## Exact length

Write

```text
k_i = lcp(w_{i-1}, w_i).
```

The header has five bytes. Record `i` has one prefix byte, `|w_i| - k_i`
suffix bytes, and one delimiter. Therefore

```text
L(D) = 5 + sum_i (2 + |w_i| - k_i).
```

The encoder computes every `k_i` before emission and rejects any value above
223. The maximum-LCP hypothesis is therefore certified by the finite list of
computed lengths.

## Archive and codec transfer

Canonical USTAR construction processes members in order. It copies every
member except the designated dictionary byte-for-byte, replaces that payload
with the bounded-prefix representation, updates only its size and checksum,
and preserves canonical padding. The runtime wrapper decodes that member
before build or execution. By the inverse theorem, the restored dictionary is
identical; all other members were never changed.

If restored closure bytes, wrapper behavior, build flags, executable, and
dictionary are identical to the parent, both packages invoke the same
deterministic runtime on every input. Their archives and decoded outputs are
equal. With equal archive length `A` and package lengths `P` and `P'`,

```text
(A + P') - (A + P) = P' - P.
```

No score inheritance is valid if restoration or runtime identity fails.

## Frozen enwiki9 instance

The 411,996-byte dictionary contains 44,515 records, ends in line feed, and
has maximum adjacent LCP 17. Its SHA-256 is:

```text
4c8568cca9343b9a6212477880f56f8efd162f8784224a25edd043097d36215a
```

The bounded representation is 362,457 bytes with SHA-256:

```text
b442e63a75837033e7ef3ef29081926a8e80f4c8ae3a818edede6d8846071e04
```

Exact decoding reproduces the dictionary. In the LPWQ-1 closure, raw-LZMA2
payload size falls from 277,064 to 270,395 bytes, a 6,669-byte gross saving.
Wrapper growth and restored-closure identity must be counted before this
becomes a constructive package result. Score credit remains zero until the
native gate passes.
