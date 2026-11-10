# Matched counted fragments and AST source macros

The [contract](CONTRACT.md) was reviewed by the owner before execution. The
[results](RESULTS.md) report both languages at 64, 128 and 256 entries, with
operands, spelling, framing and full population denominators retained.

`codec.py` owns prefix encoding and independent decoding. `shapes.py` and
`js_shapes.cjs` inspect source syntax without executing it. `run.py` reads only
hash-qualified sources through KnownSpecService, fits on historical development
fit IDs, seals the tables, then opens the existing development validation IDs.
`report.py` renders measurements without fitting. `test_codec.py` tests the codec
against an exhaustive segmentation oracle and adversarial packets.
`verify.py` independently decodes retained packets, recomputes aggregates and
checks fitting-source support, exclusions, strict improvement and fallback denominators.

Run the exact-source arms from Gamma (the output directory must not already
exist). Keep this new result separate from the frozen historical results:


```sh
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/test_codec.py
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/run.py \
  --exact-only \
  --service /absolute/path/to/existing/service/config.json \
  --service-sha256 ACTUAL_TRUSTED_CONFIG_HASH \
  --output /absolute/private/run-directory \
  --report /absolute/private/new-comparison.json
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/report.py \
  --results /absolute/private/new-comparison.json \
  --output /absolute/private/new-comparison.md
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/verify.py \
  --private /absolute/private/run-directory \
  --results /absolute/private/new-comparison.json \
  --output /absolute/private/new-verification.json
```

This evaluates representation of known solutions. It does not implement a
problem-description-to-program solver. The compact Python successor diagnostic
has static transformation checks, not fresh native qualification. No public
source dictionary or BITS integration is produced by this experiment.

## Portable workflow and nesting correction (2026-11-10)

The historical compact-Python diagnostic depends on
`../python-compact-v1/transform.py`, which is not in this checkout. Importing the
runner or verifier no longer requires that separate asset. `--exact-only`
explicitly omits the diagnostic, records the choice in the run contract, and
preserves the exact-source arms and all original source-access/partition gates.
Without that flag, missing diagnostic code fails before any service/source read
or output creation. Historical diagnostic replay still requires the exact
original transformer; a substitute does not reproduce its evidence.

The macro encoder now respects the decoder's 128-level nesting ceiling, including
CONCAT levels. It optimizes over valid alternatives and spells bytes when that
is the cheapest admissible representation. Optimization and emission are
iterative, with a one-million-state bound that fails explicitly; no invalid packet
is returned after a resource failure. Prior source costs/results have not been
rerun or revised. Fragment-arm evaluation reuses the indexed dictionary across
its corpus without changing packets or fitting policy.

```sh
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/test_codec.py
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/test_workflow.py
```

Seventeen codec tests and four portable-workflow tests cover nesting boundaries,
independent small-depth cost enumeration, iterative behavior, resource failures,
64-KiB inputs, optional-diagnostic handling and byte-identical historical rendering.
No new source qualification, corpus result, promotion or BITS deployment is
established by these development checks.
