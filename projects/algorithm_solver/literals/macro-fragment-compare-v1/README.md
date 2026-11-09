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

Run from Gamma (the output directory must not already exist):

```sh
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/test_codec.py
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/run.py \
  --service /absolute/path/to/existing/service/config.json \
  --service-sha256 ACTUAL_TRUSTED_CONFIG_HASH \
  --output /absolute/private/run-directory \
  --report projects/algorithm_solver/literals/macro-fragment-compare-v1/results.json
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/report.py
python3 projects/algorithm_solver/literals/macro-fragment-compare-v1/verify.py \
  --private /absolute/private/run-directory
```

This evaluates representation of known solutions. It does not implement a
problem-description-to-program solver. The compact Python successor diagnostic
has static transformation checks, not fresh native qualification. No public
source dictionary or BITS integration is produced by this experiment.
