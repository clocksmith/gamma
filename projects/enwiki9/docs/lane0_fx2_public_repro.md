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

This lane must stay separate from:

- Lane 1: experimental `cmix21` memory shaping.
- Lane 2: residual, embedding-teacher, manifold, or soft-state probes.

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

Run the guarded full reproduction:

```bash
python3 projects/enwiki9/tools/fx2_public_repro_queue.py --run-guarded
```

The success condition is not a forecast. The result must prove:

- restored bytes equal `projects/enwiki9/data/enwik9`;
- `compressed_size` equals the emitted `archive9` bytes;
- `program_size` equals the counted fx2-cmix executable/package bytes for this
  lane;
- `hutter_score = compressed_size + program_size`;
- RSS guard did not trip.
