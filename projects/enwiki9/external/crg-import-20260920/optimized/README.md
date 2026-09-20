# Corrected CRG research codec, with an optimized native core

**This is not a verified Hutter Prize winner.** It is a working byte compressor,
not the submitted script's simulated decoder or invented score certificate.
No canonical enwik9 250KB/1MB/full-1GB benchmark was completed in this session.
No code was pushed to Gamma and no Gamma experiment was launched.

## Run

Requires Python 3.10+ standard library and, for the fast backend, a C++17 compiler
with unsigned 128-bit integers (tested with GCC on this Linux host).

```sh
python3 crg_fast.py build
python3 -m unittest -v test_crg test_native
python3 crg_fast.py compress sample.bin sample.crg --backend auto
python3 crg_fast.py decompress sample.crg restored.bin
cmp sample.bin restored.bin
```

`auto` measures stored, Deflate9, LZMA6, and native higher-order parent archives;
it transmits only the selected archive. All use the same 96-byte header. It does
not run the unsupported relational treatment by default. All candidate code
and dependencies still belong to the delivered multi-codec implementation.

For the optimized context coder without backend selection:

```sh
python3 crg_fast.py compress sample.bin sample.crg --backend native --arm parent --profile 1
python3 crg_fast.py decompress sample.crg restored.bin
```

For real relational controls, not artificially assigned numbers:

```sh
python3 crg_fast.py compress sample.bin shared.crg --backend native --arm shared --profile 1
python3 benchmark.py sample.bin new_benchmark_directory
```

For the complete standalone Python implementation, without a compiler:

```sh
python3 crg_reference.py compress sample.bin sample.crg --arm parent --profile 1
python3 crg_reference.py decompress sample.crg restored.bin
```

Keep output paths distinct. Existing files are refused unless `--force` is used.
Use `--max-output` to limit decoding, `--timeout` to bound individual native
subprocesses/backends, and an external process-tree memory/resource guard when
performing a controlled Gamma run. These are research commands, not admission to
Gamma's managed queue. Auto's timeout is per candidate, not an aggregate budget.

## Actual local results

These are **not enwik9**. The available natural-text data was the Wikipedia XML
fixture installed with Gensim:

`gensim/test/test_data/enwiki-latest-pages-articles1.xml-p000000010p000030302-shortened.bz2`

The uncompressed intervals are [0,250000), [250000,500000), and
[1000000,2000000). All start with cold model state. The second interval occurred
inside an earlier aggregate prefix diagnostic; it is separate from tuning, not
claimed globally unseen. The third was held apart from the parameter selection.
The 250KB development population selected shrinkage=4 from {2,4,8,16,32}.
No validation or confirmation result was used to retune the final model.
All sizes below include the exact 96-byte archive header, not the software package.

| Implementation | Development 250KB | Separate 250KB | Separate 1MB |
|---|---:|---:|---:|
| Corrected basic order-2 parent | 108,135 | 105,536 | 418,152 |
| Optimized order-6 parent | 70,075 | 66,922 | 268,174 |
| Optimized parent + shared relations | 70,073 | 66,922 | 268,174 |
| Optimized parent + independent relations | 70,073 | 66,922 | 268,174 |
| Deflate level 9 | 88,276 | 81,283 | 341,638 |
| LZMA preset 6 | 75,808 | 71,136 | 283,524 |

**The useful observed improvement is the higher-order baseline.** Shared relations
save only two development bytes, tie independent relations, and add nothing on
either separate population. This does not validate the relational mechanism.
It is not a comparison against native FX2 or a forecast for full enwik9.

The confirmed 1MB context-parent codec reported 0.820 seconds encoding and
0.884 seconds decoding, including its Python framing work after interpreter
startup. Timings are shared-host diagnostics. GNU time's maximum process RSS
was approximately 94,432 KiB; this is not continuous aggregate process-tree or
cgroup qualification. Full package size and prize qualification remain unknown.

## What was corrected

1. Real binary arithmetic encoding and decoding; the decoder does not receive
   the original input, current token, vocabulary, or future structure labels.
2. A fixed byte alphabet: arbitrary binary data, original whitespace and UTF-8
   encodings are preserved without text normalization.
3. Normalized Q16 binary probabilities. There is never a collection of 0.90
   emissions simultaneously assigned to several mutually exclusive outcomes.
4. Persistent integer Bayesian posterior state, rather than discarding the
   updated states and recreating priors at every symbol.
5. A proper outer sequential posterior, not a permanently 50/50 symbol mixture.
6. Bounded parser buffers, histories, donor lengths and context tables.
7. Genuine P/K/I/S/W executions. P/K have identical archives. No arbitrary
   +12, +32 or +85 offsets substitute for actual control encodings.
8. Actual headers, payload lengths, hashes, exact inverses, repeats, and corruption
   tests. Checksums detect corruption, not malicious provenance forgery.
9. No function declares a prefix a Hutter winner. The assessment tool requires
   canonical full enwik9 and still does not claim official acceptance.

## Architecture

- `crg_reference.py`: independent pure-Python predictor, parser, posterior,
  arithmetic coder, bounded file I/O, format and standard-library backends.
- `crg_core.cpp`: optimized native payload engine, integer hot loop, buffered I/O.
  It is an internal engine; use the Python driver for format integrity checks.
- `crg_fast.py`: input snapshot, explicit native build, native process supervision,
  integrity-checked framing, selected backend, atomic publication.
- `benchmark.py`: fresh encoding/decoding/repeat processes with actual archives.
  `--resume` verifies retained data identities and preserves incomplete attempts.
- `assess_submission.py`: full-corpus identity check and declared component
  arithmetic; deliberately not a resource, licensing, or award certificate.
- `test_crg.py`, `test_native.py`: 33 tests, including cross-language byte identity.

The baseline uses backoff estimates from contexts of 0, 1, and 2..6 previous
bytes. The higher-order tables have exact 64-bit context tags and deterministic
collision eviction. Counts decay through specified integer halving at total 512.
The strong profile has five 2^18-slot context banks. This is conventional
context modeling, not a claimed novel invention.

Relations remain an optional depth-one exact-word model. The parser maintains
separate title/body memories and knows a link target only after decoding `[[`.
Candidate strings use completed history. Shared weights persist only when the
candidate set remains identical; independent weights reset each mention. The
wrong-donor control changes the actual spelling using ROT13, not just donor IDs.
This control is causal and matched in capacity; it is not guaranteed to erase
all information or to be worse on every corpus.

The outer expert posterior persists across the file. That is a new, explicitly
specified reference profile, not a claim that changing Gamma's frozen epochs
repairs its previously rejected expert. No old Gamma result is inherited.

## Mathematics and its limits

For ideal sequence distributions P and Q, the posterior-weighted sequential
mixture represents M(x)=0.5 P(x)+0.5 Q(x). Therefore

`-log2 M(x) <= min(-log2 P(x), -log2 Q(x)) + 1`.

This is NOT true over an entire sequence for a fixed 50/50 mixture at every
symbol. On 100 successive ones with p=0.99 and q=0.01, that fixed mixture costs
100 bits, while P costs approximately 1.44995697 bits. The true sequence mixture
costs approximately 2.44995697 bits.

This implementation rounds Q40 posterior weights and Q16 output probabilities.
Its guarantee is deterministic execution of those specified integer operations,
not exact rational Bayesian inference or a universal one-bit archive overhead.
The real archive is measured. Do not equate 156.016 log-cost bits with a
19-byte (=152-bit) finite-file difference or claim one observed example proves
a finite-precision regret bound.

At each bit the encoder and decoder calculate the same count from the same
reconstructed prefix. Arithmetic intervals and deterministic model updates
then select the same next bit. Induction supplies the correctness argument;
actual tests check the implementation. Neither induction nor valid normalized
probabilities imply any particular corpus compression rate.

For the fixed multi-codec executable, auto chooses the shortest among the
actually generated files, including the mode header. This is a finite selection
property, not a proof of the best compressor among untested algorithms. It does
not ignore the cost of bundling all supported implementations.

## Format and safety

Magic `CRG2`, version 2; all multibyte header fields are big-endian.
`>4sBBHQQQ32s32s` stores magic, version, mode, zero flags, original byte length,
exact payload bit count, payload byte count, original SHA-256, payload SHA-256.

Modes 0..3 are basic parent/independent/shared/wrong. Bookkeeping uses parent
mode to preserve exact P/K archive identity. Modes 4/5/6 are Deflate/LZMA/stored.
Modes 7..10 are higher-order parent/independent/shared/wrong. The mode is paid
in the header. No out-of-band flags or source data are needed for decoding.

A 32-bit arithmetic coder normalizes E1/E2/E3 intervals. It stores its termination
and 32 zero padding bits; EOF never silently manufactures missing bits. The
header and data digests are checked before output publication. A checksum is
not a cryptographic authenticity guarantee, and this is not an adversarial
security audit. Arithmetic streams are not claimed to have unique canonical
encodings under an attacker who rewrites checksums; generated repeats are exact.

Decode output is bounded by its declared length and the user-supplied cap.
The native wrapper uses private temporary directories; failed outputs are not
published. It does not implement a complete OS sandbox. A no-original-input
subprocess test is not a filesystem-sealing proof.

## Test and evidence scope

- 33 Python/native tests pass.
- Native and Python archives are byte-identical on all five arms and both
  profiles for tested fixtures. Both implementations decode each other's files.
- 20 native encode/decode processes pass UndefinedBehaviorSanitizer fixtures.
- 24 local Wikipedia comparisons complete 72 fresh encode/decode/repeat phases.
- Every retained output was compared byte-for-byte with its input; every repeat
  was compared byte-for-byte with its archive.
- The first aggregate benchmark invocation was interrupted by the tool wall
  limit. Completed records were verified on resume; incomplete attempts were
  preserved rather than called valid measurements.
- C++ whitespace formatting occurred after benchmarking. The formatted source
  produced a byte-identical native executable, documented in the evidence.
- Default auto selection was subsequently changed to exclude the unpaid
  relational arm. Benchmark commands specify arms explicitly and their original
  measured driver is retained. Regression tests were rerun after that change.

No full enwik9 corpus was mounted. GitHub text access succeeded, but raw-byte
materialization/download did not. The local Wikipedia fixture is a different
population; its hashes and coordinate ranges are retained. Data is not included
in this source bundle. To reproduce those populations, use an existing copy of
the named Gensim test fixture; no dependency installation is required by the codec.

## Integrating into Gamma

Use the files as a separately identified research implementation. Do not replace
frozen FX2/CRG evidence, inherit other candidates' size results, or bypass Gamma's
resource admission and ownership. The optimized context predictor is not FX2.
A next Gamma measurement must compare identical canonical input bytes and price
its own implementation, models, options, runtime and final package.

The official criteria are maintained at:
https://www.hutter1.net/prize/hrules.htm

This bundle does not establish 96M, 95M, the current one-percent threshold, or
an official award. It establishes a real, tested correction to the uploaded
pseudo-code and a measured improvement over its low-order reference baseline.
