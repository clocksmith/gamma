# Typed-composer synthetic development diagnostic v1

This is an authored fault-injection diagnostic for Track A, not a reconstruction
of the missing frozen neural comparison. It tests whether the existing strict
decoder and bounded correction distinguish malformed structure, invalid
bindings, invalid operators, and valid-but-wrong programs.

## Result

[The retained report](evidence/report.md) and [complete receipt](evidence/diagnostic.json)
contain 14 cases constructed from two tiny authored programs. They are not 14
independent problems or a representative sample of predictor failures.

- Graph validity: raw 4/14, constrained 13/14.
- Passes all four explicit authored expectations: raw 2/14, constrained 11/14.
- Nine useful repairs on those expectations, zero harmful repairs.
- Structural faults: three of four repaired. The interior EMPTY slot remains
  invalid under the unchanged default correction policy.
- Binding faults: unknown, out-of-scope, and wrong-type references are repaired.
  A valid reference to the wrong integer input remains unchanged and wrong.
- Operator faults: arity/result-type mismatches are repaired. A type-correct
  multiplication substituted for addition remains unchanged and wrong, even
  though it happens to pass the first authored check.
- One combined structural/binding fault is repaired with two charged edits.
- Both valid control graphs remain unchanged.

The interior EMPTY example exposes a candidate-selection limitation: the default
policy considers active slots plus one frontier slot, not every interior hole.
The existing opt-in policy is tested separately by
`test_typed_comparison.py`; this diagnostic does not switch it on, change the
default, select a new model candidate, or reopen any reservation.

## Evidence contract

Every raw code array, injected coordinate, raw/decoded graph, validation failure,
correction attempt, edit, and authored check is retained. Dense synthetic scores
are reproduced losslessly from the documented sparse recipe and checked by hash.
Their argmax is the corrupted token; the original correct token is deliberately
given the runner-up score. This favorable construction establishes a correction
mechanism on fixtures, not the quality of actual learned rankings.

All raw and constrained graphs are fixed before expected values are checked.
The expectations are explicitly authored, not independent sealed evaluation data.
An invalid graph is not executed and its expectation verdict remains null.
Valid-but-wrong graphs remain unchanged, as required by schema-only correction.

The existing bounded typed-data interpreter evaluates only these authored
graphs, with a 1,000-operation budget. No Python/JavaScript source is executed,
no native judge is invoked, and no sandbox is weakened, bypassed or replaced.
No model, embeddings, catalogue, hidden tests, protected cases, training, network
service or new package is used. Existing codecs and correction code are unchanged.

The receipt hashes the diagnostic, codec, correction, recipes and interpreter.
It records the 64-slot descriptor and a separate synthetic policy with the
existing default bounds: two alternative values per field, 64 edit options,
two edits, 128 candidates and 0.2 seconds. Clock-limited outcomes can vary with
machine load; retain them rather than rerunning until a preferred result appears.
Timing is decoder/correction timing only, not complete request latency.

## Reproduce

From the repository root, use a new output directory:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=projects/algorithm_solver \
  python3 -B -m algsolve.synth.typed_synthetic_diagnostic --output /tmp/NEW-UNUSED-DIAGNOSTIC
```

The command refuses to overwrite earlier evidence. It requires the Python
standard library and the repository's typed modules, not Torch or Transformers.

## Verification and remaining blockers

- Nine new diagnostic unit tests passed, including raw capture/score hashes,
  decision-before-check ordering, per-axis outcomes and no-overwrite behavior.
- Four existing prediction-codec tests and eleven existing synthetic comparison
  tests passed. The comparison's real native-sandbox test was deliberately not
  part of this synthetic-only check.
- Changed modules parsed and imported successfully.
- The broader native-judge/lane suites were not run; pytest is absent and the
  existing native sandbox has a previously recorded NETLINK_ROUTE failure.
  No native qualification or general lane acceptance is claimed.

The original neural comparison still needs its exact frozen checkpoint,
development corpus, qualification/training summaries, verified embedding assets,
Torch/Transformers runtime and working unchanged sandbox on an authorized host.
None is reconstructed by this diagnostic. Synthetic fixture success does not
qualify a development candidate, authorize protected scoring, establish unseen
generalization, or start an autonomous development loop.

Component intent is preserved. This additive diagnostic changes no production
runtime, protected population, qualification gate, vocabulary or native-sandbox
boundary. Its local base was Gamma `632d8d368d3dd7d420ea9c06aca6ecba5fed61ed`.
