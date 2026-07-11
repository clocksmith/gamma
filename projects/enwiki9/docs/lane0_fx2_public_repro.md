# Lane 0: fx2-cmix Public Reproduction

Lane 0 is a control lane, not an optimization lane. Its job is to reproduce the
published fx2-cmix package path on the local enwik9 file so later full-corpus
claims have a known-good reference.

Public target recorded by the upstream repository:

- Program: `fx2-cmix`
- Total score: `110793128`
- `archive9` size: `110351665`
- Counted executable size: `441463`
- Reported RAM max: `9523660 KiB`

## Current Preflight State

Latest lock-safe preflight command:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --preflight
```

Current facts:

- `projects/enwiki9/data/enwik9` exists at `1,000,000,000` bytes.
- Corpus SHA-256 is
  `159b85351e5f76e60cbe32e04c677847a9ecba3adc79addab6f4c6c7aa3744bc`.
- `projects/enwiki9/external/fx2-cmix` exists.
- Root binary `external/fx2-cmix/cmix` exists at `379,312` bytes.
- Dictionary `external/fx2-cmix/dictionary/english.dic` exists.
- Article-order asset
  `external/fx2-cmix/src/readalike_prepr/data/new_article_order` exists.
- Build script `external/fx2-cmix/build_and_construct_comp.sh` exists.
- Exact upstream package `external/fx2-cmix/run/cmix` is absent.
- Candidate root-binary control package
  `programs/fx2cmix_public_repro_v1/cmix` exists at `680,876` bytes with
  SHA-256 `6fdccda4b637dc07160378df82d96957db8e32e932152856d99feb664b987590`.
- Required exact-build tools reported absent: `clang++-17`,
  `llvm-profdata-17`, `upx-ucl`.

Interpretation:

```text
Lane 0 can validate local control packaging from the root binary. The control
is `239,413` bytes larger than the public `441,463`-byte executable, so it
cannot claim exact public executable-size reproduction until the upstream
package or equivalent build-tool path is present and counted.
```

This lane must stay separate from:

- Lane 1: experimental `cmix21` memory shaping.
- Lane 2: residual, embedding-teacher, manifold, or soft-state probes.

## No Exact Top-Three Prefix Matrix

This checkout does not contain a clean exact `1M`/`10M` calibration matrix for
the three published submission programs. In particular:

- the local `fx2-cmix` lane has source and a `680,876`-byte control package,
  but not the exact public `441,463`-byte executable package;
- an exact upstream `fx-cmix` submission package is not present as its own
  local lane;
- an exact upstream `fast cmix` submission package is not present as its own
  local lane.

Local `fx2cmix_recovered_*`, cmix21, geometry-order, and core-tune prefix rows
are derivative experiments. They must not be labeled as exact prefix results
for the published top-three submissions. The absence is not repaired by
running the public fx2 full-corpus-specialized path on an arbitrary prefix.

## Why Prefix Gates Are Invalid Here

The upstream `cmix -e` path is specialized for full enwik9. It uses fixed
split/reorder constants and a fixed article-order asset, then emits a
self-extracting `archive9` binary. A 1K, 250K, 1M, or 10M prefix does not
exercise the same package path and can fail for reasons unrelated to the public
submission.

Lane 0 therefore has two valid stages:

1. Preflight: verify data size/hash, source checkout, package asset, and target
   accounting.
2. Full reproduction: run `cmix -e`, execute `archive9`, verify restored bytes,
   record archive size, program size, score, hashes, and RSS guard output.

## Commands

Preflight:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --preflight
```

Attempt the exact upstream build path:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --build-upstream
```

This command is expected to report `missing_exact_build_tools` unless
`clang++-17`, `llvm-profdata-17`, and `upx-ucl` are available. A clean public
reproduction should use the package emitted at
`projects/enwiki9/external/fx2-cmix/run/cmix`.

Prepare the candidate package after the upstream `run/cmix` package exists:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --prepare
```

If the exact upstream package is absent, a local control package can be assembled
from `projects/enwiki9/external/fx2-cmix/cmix`:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --prepare-from-root-binary
```

That control validates the `-e/archive9` machinery, but it is not an exact
public executable-size reproduction unless the reported package size matches the
upstream target.

This command invokes cmix to compress package assets, so the helper now holds
`/tmp/enwiki9-heavy.lock` and refuses to run while an active scorer owns the
lock.

Run the guarded full reproduction:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --run-guarded
```

The guarded runner enforces the official decimal `10GB` ceiling as
`9,765,625` KiB over aggregate process-tree RSS. Its terminal metadata record
attaches the guard JSON to the full result rather than relying on a separate
unlinked memory receipt.

The success condition is not a forecast. The result must prove:

- restored bytes equal `projects/enwiki9/data/enwik9`;
- `compressed_size` equals the emitted `archive9` bytes;
- `program_size` equals the counted fx2-cmix executable/package bytes for this
  lane;
- `hutter_score = compressed_size + program_size`;
- aggregate process-tree RSS stayed at or below `9,765,625` KiB.
