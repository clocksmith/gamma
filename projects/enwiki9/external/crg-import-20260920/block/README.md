# Corrected CRG code and verified block compressor

**Working implementation, not a Hutter Prize winner.** This package audits the
two uploaded programs and supplies executable replacements. It does not revive
Gamma's retired relational-binding experiment or inherit any FX2 score.

## Run

Python-only (Python 3.10+ and its standard compression modules):

```sh
python3 compress.py encode input.bin output.gcb
python3 compress.py decode output.gcb restored.bin
cmp input.bin restored.bin
```

Add the native experimental context/role-history codec:

```sh
make
python3 compress.py bench /path/to/gamma/projects/enwiki9/data/enwik9_250000.bin --cpp ./crg
python3 compress.py encode input.bin output.gcb --cpp ./crg
python3 compress.py decode output.gcb restored.bin --cpp ./crg
cmp input.bin restored.bin
```

The native program alone handles at most 1 MiB per file:

```sh
./crg c sample.bin sample.cgr base
./crg d sample.cgr restored.bin
./crg c sample.bin role.cgr history
```

Use the Python container for larger files. It streams independent blocks of at
most 1 MiB. Input/output must differ; existing output files are never overwritten.
Python publication is atomic and failed verification leaves no final output.
The default decoding output ceiling is one billion bytes; adjust `--max-output`
explicitly for another use. A native-coded block requires the native executable
on decoding. Archives do not store that executable.

## Contents and responsibilities

- `src/crg.cpp`: integer arithmetic coder, bounded causal models and native format.
- `compress.py`: block container, real codec selection, integrity and CLI.
- `tests/`: independent roundtrips, corruption checks, compiler comparison and
  arithmetic endpoint/underflow stress. No reference input is passed to decode.
- `evidence/`: actual test and benchmark results from this session.
- `original/`: **incorrect uploaded sources for audit only**, not the replacement.
- `PROOFS.md`: precisely scoped mathematical arguments and limitations.

## Corrected native algorithm

The parent uses interpolated bit contexts of byte orders zero through six,
bounded counters, an eight-mebibyte direct-mapped context table, and declared
unsigned hashing. This is ordinary context modeling, not a novel learned model.

Optional `history` mode maintains separate bounded histories of completed title
and body words. It builds normalized next-byte counts from exact matching past
word prefixes. Titles can predict subsequent text; decoded body words can
predict subsequent link targets. No future target byte is passed to the model.
A deterministic integer posterior combines this expert with the context parent.
There is no claim that the rounded posterior has an exact one-bit regret bound.
There are no persistent latent argument bindings or recursive grammar induction.

The parser is bounded classification for prediction, not an XML validator or
normalizer. All original bytes, malformed markup and non-ASCII data included,
remain literal coder outcomes. Original spellings are never silently repaired.

The native file stores its length, mode, raw CRC and payload CRC. It validates
sizes and probabilities and rejects truncation rather than silently inventing
zero bytes. The global Python format additionally checks SHA-256 of the entire
reconstruction and rejects trailing data and bounded-output violations.

## Exact block selection

Auto mode measures literal, Deflate, Bzip2 and LZMA payloads. With `--cpp`, it also
measures both native modes. The smallest actual result is stored with its method
identifier and complete block header. Every chosen candidate is decoded and
checked before publication. Costs are real bytes; no imaginary control offsets
or estimated log losses are substituted for archives.

The selection is optimal ONLY among these measured alternatives with this block
policy and fixed container. It is not globally optimal, and running all the
encoders is slower than running one. Smaller dictionaries and reset blocks can
lose cross-block compression; no advantage over native FX2 is claimed.

## Actual measurements

All entries below include the identical 52-byte GCB1 file header and 17-byte
single-block record. C++ blocks also include their complete native framing.

| Input | Deflate | LZMA | C++ context | C++ role history | Auto |
|---|---:|---:|---:|---:|---:|
| Original 218-byte example | 202 | 269 | 222 | 222 | 202 |
| Verified 1,000-byte enwik9 prefix | 393 | 469 | 451 | 451 | 393 |
| Synthetic XML, 250,000 bytes | 45,069 | 23,377 | 46,821 | 46,821 | 23,377 |
| Synthetic XML, 1,000,000 bytes | 179,248 | 90,921 | 184,135 | 184,135 | 90,921 |

**The 250KB and 1MB rows are artificially generated XML, NOT enwik9. Do not
extrapolate them or use their percentages as a prize result.** Role history
produced no archive improvement on these cases. The generic codecs, not a new
relational mechanism, win the selection. The canonical 1,000-byte file was
verified against Git blob 7592125ce585293363cb36dee3fd774007d97dc4. Larger actual
corpus files could not be transferred into this runtime; no current 250KB/1MB
native FX2 comparison or full-corpus run was performed here.

`python3 tests/make_benchmark_inputs.py` reconstructs the synthetic benchmark
files from seed 923. `bench` measures and verifies each real candidate, then
prints full-size, timing, hash, inverse and repeat results. Existing dependency
versions are recorded in `evidence/build.json`. Compression-library versions can
change emitted files; byte-identical results across every library release are
not claimed.

23 Python tests passed, including randomized native roundtrips; the separate
arithmetic checker inverted 100,000 events with sanitizers. GCC/Clang builds
agreed on the tested fixture. Native 1MB synthetic history encoding and decoding
used roughly 12 MiB peak process RSS here; shared-container timing is diagnostic,
not normalized Hutter resource qualification.

## Prize, novelty and accounting

No full-corpus score is established. The package does not contain a complete
self-extracting enwik9 archive, complete runtime/license closure, official
runtime calibration or committee verification. Every CLI report leaves
`hutter_win_established` false. Novelty and global optimality are not claimed:
arithmetic coding, context models, word-history predictors, Bayesian mixtures
and minimum-size codec selection all have prior art.

Python, zlib, Bzip2, liblzma, the C++ standard runtime and a native executable
where selected are delivery dependencies. The source-only ZIP is a source-size
measurement, NOT accepted complete Hutter packaging. The official detailed rules
are https://www.hutter1.net/prize/hrules.htm .

The recent Gamma closure (2771e03ae) remains valid: shared bindings lost 4, 5 and
19 archive bytes on its three populations before the 49,038-byte implementation
increment. This new standalone correction supplies no evidence overturning that.
