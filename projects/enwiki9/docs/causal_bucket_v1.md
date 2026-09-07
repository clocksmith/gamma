# Causal byte buckets

This standalone experiment changes raw byte order before the unchanged Deflate
backend. It uses no grammar, learned model or parent-probability trace.

Start a frame with predecessor zero. Place each byte into the FIFO bucket named
by its predecessor, then concatenate the 256 buckets in ascending byte order.
Store the final raw byte before that concatenation. For every value `v`, the
number of predecessor occurrences equals the number of emitted occurrences,
plus the initial predecessor indicator, minus the final byte indicator:

```text
bucket_size[v] = payload_histogram[v] + (v == 0) - (v == final_byte)
```

Thus the decoder derives every bucket boundary without a transmitted count
table. It starts at predecessor zero, consumes the next byte from that bucket,
and makes the emitted byte the next predecessor. For a correctly encoded input,
induction reproduces the original path and FIFO consumption order. Require
exact output length, every bucket exhausted, the stored endpoint and outer
SHA-256. Empty input has no frames. All original byte values remain unchanged.

The endpoint is necessary: `01 00 01` and `01 01 00` have identical concatenated
buckets but different final bytes. The endpoint can select another valid raw
sequence; outer checksums detect such corruption. No information is free.

This is a bounded-lookahead ordering transform. The encoder and decoder buffer
one frame. Transform/inverse work is O(N + 256). It does not preserve higher-order
LZ matches; whether local grouping compensates is an empirical question. Context
sorting has established precedents; this experiment claims no general novelty.
Historical negative token-BWT and numeric side-channel receipts concern different
populations and supplied parent probabilities, not this raw-byte comparison.

P uses the unchanged D2GRAM02 plain codec. K computes the transform and inverse,
then emits exactly P. D admits a transformed frame only when its complete bytes
are strictly smaller. All modes retain the existing frame boundaries and level-9
Deflate. A selected archive uses D2BUKT01 and frame mode 5; all-plain fallback
retains exact P bytes. The sole compressed section includes the endpoint. All
lengths, termination and headers count. Decoding performs no grammar discovery
or re-compression. Reports distinguish transmitted payload hashes from encoder
comparison diagnostics; repeated encoding starts from reconstructed raw bytes.

```bash
python3 tools/causal_bucket_v2.py encode input.raw candidate.d2g --mode D
python3 tools/causal_bucket_v2.py decode candidate.d2g restored.raw
cmp input.raw restored.raw
```

Input is bounded to 1,000,000 bytes and frames to 65,536 bytes. Existing output
paths are refused. The retained v1 synthetic implementation missed the encoder
archive cap for extreme tiny frames. The v2 repair checks framing before work
and cumulative stored bytes during encoding; its decoder format is unchanged.
The v1 source and kernel receipt remain historical evidence, not an eligible
corpus implementation. Corpus tests require frozen source/population/control and
resource bindings through the existing queue. A paying development comparison
must survive separately frozen confirmation. Local source inventory is separate
from complete runtime, licensing and package qualification. The 99M complete
objective remains unproved.
