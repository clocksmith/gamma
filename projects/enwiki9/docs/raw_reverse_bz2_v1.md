# Raw block direction

This experiment tests one question: does reversing raw bytes inside a fixed
250,000-byte block reduce the complete BZip2 level-9 representation? The installed
standard-library backend stays unchanged. This is a coding-direction test, not
a new entropy coder or a claim of compression novelty.

P codes forward bytes. K reverses and restores them for bookkeeping, then emits
exactly P. D always codes reversed bytes, even when the archive grows. Every arm
has its own retained archive, independent inverse and repeat from restored raw
bytes. There is no selected fallback hiding an untested treatment inverse.

Each archive starts with `<8sIIQ`: magic `D2REVB01`, block size, block count and
total raw length. Each block has `<IIB32s`: raw length, compressed length,
direction (0 forward or 1 reversed), and the original raw SHA-256. Exactly one
BZip2 stream follows. The header costs 24 bytes and each block header 41 bytes;
these costs apply to every arm. No dictionary or permutation table is stored.

The inverse decodes at most the declared length plus one byte, requires the
exact length, BZip2 end-of-stream and no trailing stream, and reverses direction-1
blocks. Reversing twice is the identity for every byte string. Original checksums
and block order verify the complete reconstruction. Empty input has only its
header; partial final blocks preserve their exact lengths.

```bash
python3 tools/raw_reverse_bz2_v1.py encode input.raw forward.rev --mode P
python3 tools/raw_reverse_bz2_v1.py encode input.raw reversed.rev --mode D
python3 tools/raw_reverse_bz2_v1.py decode reversed.rev restored.raw
cmp input.raw restored.raw
```

The implementation caps input at 1,000,000 bytes, blocks at 250,000 bytes and
archives at 8,000,000 bytes. Existing output paths are refused. Corpus execution
uses the existing guarded queue after source, population, controls, runtime and
resources are frozen and published. Synthetic tests do not authorize corpus
execution by themselves.

Historical raw BZip2 metadata reports 72,658 bytes on opening250KB but retains no
archive hash. The new P must establish its own exact archive. The earlier
89,041-byte Deflate archive uses different framing and a different backend;
only D versus matched P measures this direction change. All matched commands
use the same standalone source file. Its full source/runtime/license/option
inventory remains a submission obligation, even when shared experiment costs
cancel. No small-sample ratio establishes the 99,000,000-byte complete target.
