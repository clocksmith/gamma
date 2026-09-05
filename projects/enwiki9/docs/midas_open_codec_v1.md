# Bounded standalone open MIDAS

`tools/midas_open_codec_v1.py` builds and runs the retained open incremental
predictor through a new standalone driver. It does not create a scientific
candidate, queue work, or authorize a corpus run. The predictor, initialization,
raw-byte frontend, finite arithmetic and P/K/F/S update laws are unchanged.

From this project directory, create a caller-owned build cache:

```bash
midas_cache_dir=$(mktemp -d /tmp/gamma-midas-build.XXXXXX)
python3 tools/midas_open_codec_v1.py --cache-dir "$midas_cache_dir" build
python3 tools/midas_open_codec_v1.py --cache-dir "$midas_cache_dir" inventory
```

For a synthetic input of at most 1,024 bytes, using new output directories:

```bash
python3 tools/midas_open_codec_v1.py --cache-dir "$midas_cache_dir" encode \
  --arm F --max-raw-bytes 1024 --wall-seconds 120 \
  --input fixture.raw --output-dir fixture-encoded
python3 tools/midas_open_codec_v1.py --cache-dir "$midas_cache_dir" decode \
  --arm F --max-raw-bytes 1024 --wall-seconds 120 \
  --input fixture-encoded/data --output-dir fixture-decoded
cmp fixture.raw fixture-decoded/data
cmp fixture-encoded/state.bin fixture-decoded/state.bin
```

Each completed output directory contains `data` (archive or inverse),
`state.bin`, and `summary.json`. Directory publication refuses existing files,
directories and symlinks. Invalid input or inversion does not publish a result.
Staging starts only after coding and validation; an interruption during coding
leaves no training staging. A forced termination during publication can leave a
private `.midas-codec-*` directory; it is not a sealed result and must not be
adopted. The tool does not delete other work or automatically clean old caches.

The state envelope is a final-state witness, not a resume format. It contains
the complete predictor, its P/K parent-identity projection, normalized coder
state and a reference-model projection. Full encoder/decoder witnesses should
match within an arm. P/K full witnesses intentionally differ because K executes
discarded learning; compare their parent-identity projections instead. The
projections are not substitutes for the complete predictor witness. Decoder
code/input cursors are role-specific and are not claimed identical.

The wrapper verifies the executable against its build manifest before use and
reports SHA-256 values for every output and state component. Inventory also
refuses changed bound dependencies. Local source and resolved ELF runtime bytes
are listed separately. Compiler/OS assumptions, licenses, submission form,
packaging and duplicated-program accounting remain unresolved: inventory is
not complete package accounting or prize qualification.

The native driver accepts an explicit raw ceiling of 1..250,000 bytes and a
conservative operational archive ceiling of `32 * raw_limit + 64`. It enforces
512 MiB address space, 120 CPU seconds and 32 MiB per file, preserving stricter
caller limits. The Python wrapper requires a wall stop of 1..120 seconds.
Codec timing excludes publication; wrapper timing includes it and excludes
the build. All measurements on a shared host are diagnostic.

## Build deduplication

`lib/native_fixture_build_cache.py` binds compiler/toolchain identity, flags,
sanitized environment, working directory, and transitive source/header contents.
A verified cache hit skips compilation. Changed dependencies create new entries;
corrupted entries are quarantined and rebuilt. A per-key lock prevents concurrent
requests from duplicating compilation. Stricter inherited resource limits are
never raised. Cache bounds and hashes are not qualification evidence.

The implementation requires the existing Linux/POSIX tools, GCC-compatible
compiler, AVX2/FMA host and runtime libraries. Nothing is installed automatically.
The cache is local and caller-owned, not a hermetic toolchain or eviction service.

## Validation boundary

The standalone tests retain the old 65-byte P/K/F/S archive known answers, then
compare reference and incremental F on 1,024 synthetic bytes across 32 model
updates. Archives, model/optimizer projections, inverse and deterministic replay
match; the 1,043-byte archive is larger than its raw input and earns no gain.
Filesystem, cache corruption, inherited-limit and interrupted-operation checks
are separate from the unchanged model tests. Exact evidence is retained in
`operations/evidence/20260905_parallel_native_cache_standalone_midas_unit.json`.

Corpus experiments still require a separately frozen candidate, population,
controls, source, package estimate, CPU/thread policy and resource/stop contract.
Neither this driver nor its build cache depends on HORIZON terminalizing.
