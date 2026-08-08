# Far-History Content-Defined Copy QM0

## Question

Does canonical full-1G enwiki9 contain enough exact redundancy beyond
Endpoint428's direct 100,000,000-byte history to close the current
4,389,323-byte score debt with an explicit prior-copy alphabet?

The old `dedup_v1` candidate used fixed aligned 256-byte chunks followed by
LZMA and was measured only at 1K and 250K. Those scopes cannot contain a source
more than 100M behind its target. This gate asks a different full-corpus
question and uses content-defined anchors so equal strings align regardless of
their absolute offsets.

## Frozen scanner

- exact input size: 1,000,000,000 bytes;
- rolling window: 32 bytes;
- anchor: low six bits of the first independent 64-bit rolling hash are zero;
- identity key: two independently seeded 64-bit rolling hashes;
- collision check: exact 32-byte comparison before extension;
- source: earliest prior anchor with the same identity;
- minimum target-source distance: 100,000,000 bytes;
- minimum maximal match: 64 bytes;
- extension: exact backward and forward comparison, clipped to the prior
  selected target boundary and to a completely decoded source;
- selection: deterministic chronological nonoverlap;
- command: one tag byte plus canonical ULEB128 distance and length.

The scanner is executed twice from fresh state. Both complete JSON summaries
must be byte-equivalent after parsing. Selected spans are always verified from
the mapped corpus; hashes never establish equality by themselves.

## Economic ceiling

No full Endpoint428 P1 trace exists. This gate therefore reports a conservative
target-bearing proxy, not score credit: copied raw bytes are multiplied by the
current archive-only forecast rate

```text
(109,389,323 - 261,125) / 1,000,000,000
```

and explicit command bytes plus compressed scanner source are subtracted.
Promotion requires at least 100,000,000 copied raw bytes, positive coverage in
all thirds, and 8,800,000 average-rate-equivalent net bytes. That is twice the
current score debt so a later Endpoint-relative trace can absorb substantial
selection and integration loss. A miss retires this exact far-copy
realization; a pass authorizes a paid reversible stream and target-relative
pricing, not a forecast update.

