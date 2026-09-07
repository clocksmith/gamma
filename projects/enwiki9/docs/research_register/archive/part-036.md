# Research Register Archive - part 036

[Current register](../../research_register.md) | [Register index](../README.md) | [Archive index](README.md)

## 2026-09-05 - Parallel build deduplication and standalone open MIDAS

`lib/native_fixture_build_cache.py` now reuses unchanged C++ builds under a
compiler/toolchain, flag, environment and transitive source/header identity.
Per-key locking prevents duplicate compilation; corrupt entries are quarantined
and rebuilt. Stricter inherited resource ceilings are preserved. Sixteen cache
tests pass, including the inherited-file-limit failure found during integration.
This is a local build cache, not a hermetic package or resource certificate.

`tools/midas_open_codec_v1.py` exposes bounded build, inventory, encode and decode
commands through a new C++ driver using the unchanged incremental predictor.
Output directories publish without overwrite only after coding and validation.
FIFO, symlink, corrupted-input, stale-build, no-overwrite and interrupted-operation
checks pass. Inventory reports local source and resolved runtime bytes separately
and leaves complete-package qualification explicitly unknown.

Seventeen combined MIDAS tests pass, for 33 tests with the parallel cache suite.
The standalone driver retains all original 65-byte P/K/F/S archive known answers.
On 1,024 synthetic bytes, incremental and reference F produce the same 1,043-byte
archive and model/optimizer projection after 32 updates. Independent decoding
after source removal and deterministic re-encoding reproduce exact bytes and
same-arm final-state witnesses. The archive is larger than raw; no compression
gain, corpus result, package qualification or objective credit is claimed.

Evidence: `operations/evidence/20260905_parallel_native_cache_standalone_midas_unit.json`.
Usage: `docs/midas_open_codec_v1.md`. One complete older record moved to archive
part 028 with link targets preserved, keeping this register within its line cap.
Neither implementation lane waited for HORIZON; its process, observer and partial
scientific output remained untouched. The other agent's FX2 work was preserved.
A corpus successor still needs frozen architecture, population, control, package
and composite resource budgets before launch.

## 2026-09-05 - Incremental open MIDAS preserves the retained reference

`lib/midas_open_profile_incremental_fixture.hpp` adds a separate cached-forward
implementation of the fixed one-layer integration fixture. The original parent
and sealed neural kernels remain unchanged. Its translation unit includes the
original forward source instead of linking it twice, preserving the arithmetic
helpers. Future zero-symbol K/V placeholders and the full masked softmax row are
retained; the reference exponential floor does not make masked weights zero.
Every parameter update invalidates the cache and replays the causal prefix.

Nine regression tests pass. On 65- and 129-byte synthetic populations, all
P/K/F/S F32 rows, Q16 probabilities and finite archives match the reference.
Model, optimizer, detached memory and discarded K-shadow states also match.
Encoder/decoder checkpoints include the complete incremental cache, including
pending predictions at every bit offset around midpoint and segment boundaries.
Cross-decoding, deterministic repeats, partial-segment inverses and corrupted
cache rejection pass. No corpus data or teacher state enters these tests.

The paired 129-byte F diagnostic records reference encode/decode CPU of
0.243620/0.229980 seconds versus incremental 0.034700/0.034990 seconds, with
13,996 KiB cumulative process peak RSS. Initialization, full updates and cache
resets are included. This is shared-host diagnostic evidence, not qualification.
The synthetic F/S archives are 170 bytes versus P/K's 169; no gain is claimed.

Evidence: `operations/evidence/20260905_midas_incremental_profile_identity_unit.json`.
The receipt distinguishes implementation validation from budget exhaustion and
retains exact finite bytes, source bindings and sanitizer outcomes. This adds no
compression, package, resource-qualification or full-corpus score credit. Before
a corpus successor, coordinate the compact-parent owner and freeze the chosen
architecture, population, package, memory and kernel/runtime budgets. HORIZON
and the other agent's FX2 work remain unchanged by this implementation.
