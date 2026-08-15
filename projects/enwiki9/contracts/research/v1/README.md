# Enwik9 research contracts v1

`objective-contract.json` is the canonical objective for Gamma's enwik9 lane.
It binds the corpus identity, fully counted `105,000,000`-byte target, exact
reconstruction requirements, resource limits, distribution obligations,
evidence floor, and gate ladders. Prose may explain the objective but must not
override this contract.

The accompanying schemas define the first fail-closed evidence boundary:

- `candidate-revision.schema.json` binds semantic source identity, parent and
  previous revisions, the declared edit, and immutable content-addressed blobs;
- `resource-guard-receipt.schema.json` binds process-tree RSS, threads,
  affinity, elapsed wall time, and declared candidate scratch usage;
- `experiment-contract.schema.json` freezes arms, changed variables, population,
  causal inputs, measurements, and machine-evaluable consequences before a
  result can change scientific state;
- `experiment-result.schema.json` binds the exact analyzer and input hashes to
  alignment, measurements, predicate evaluations, and a zero-credit decision;
- `adaptive-experiment-contract.schema.json` may opt new work into
  `complete-result-artifacts-v1`; under that policy the result path must be
  declared and every other declared output must be bound exactly once by the
  terminal result, with no undeclared or path-aliased artifacts;
  `pythonSourceClosureEntries` additionally names entry inputs whose complete
  project-local runtime source closure must appear in the prospective input
  manifest, including the research-contract JSON files when the validator is
  reachable;
- `named-gradient-detail.schema.json` validates the repeated named-gradient row
  population, experiment and revision bindings, execution logs, summary
  coverage, and optional direct-versus-explicit-F32 reference fields; result
  validation also recomputes any complete q2 low-precision comparison from its
  prospectively bound detail input;
- `delta-midas-probe-result.schema.json` binds prospective partition, leakage,
  causal-feature, quantized-model, shifted-control, and held-out evidence for
  the compact residual probe;
- `mechanism-graph.schema.json` prevents additive component forecasts by
  binding shared probability boundaries, cost overlap, causal compatibility,
  closed dependencies, and an exact joint-replay requirement;
- `dependency-closure.schema.json` binds every counted package member,
  dependency, command, license, and option byte;
- `driver-run-ledger-row.schema.json` binds every canonical driver-ledger row
  to one retained project-relative result JSON by byte count and SHA-256;
- `clean-room-replay.schema.json` binds three fresh package copies, sealed
  build/compress/replay/decode commands, device and network probes, resource
  guards, scratch cleanup, and the manifest-derived license audit;
- `clean-room-attempt.schema.json` preserves partial phase order, logs, guards,
  artifacts, cleanup state, and the terminal error when replay cannot compose;
- `run-receipt.schema.json` composes exact corpus, archive, package,
  second-archive determinism, correctness, resource, clean-room distribution,
  and independent-verification evidence.
- `release-receipt-index.schema.json` provides a deterministic structural router
  to every canonical release bundle without granting file-verification credit;
- `reflection-receipt.schema.json` separates process completion from scientific
  validity, attribution, typed measurements, retained knowledge, and the next
  state transition;
- `search-policy.json` defines the evidence-aware lexicographic proposal order
  without changing any measured value or promotion predicate.

Schema validity is necessary but not sufficient. `research_contracts.py` also
recomputes candidate-tree identity, requires counted files to exactly cover the
declared candidate root, verifies referenced receipt hashes, derives package
and official-score totals, checks guard claims against measured maxima, and
rejects an `objective-achieved` verdict when any antecedent is absent or false.

Paths in a dependency closure are relative to its `candidateRoot`; that root is
relative to the manifest. Paths in a run receipt are relative to that receipt.
Absolute paths and implicit symlink packaging are rejected. `totalPackageBytes`
counts the manifest's files; `requiredOptionBytes` remains separate and is added
exactly once by the run-receipt score formula. Candidate-tree identity is the
SHA-256 of canonical JSON containing each counted file's sorted `path`, `bytes`,
and `sha256` fields.

The contract digest is the SHA-256 of canonical JSON: UTF-8, object keys sorted,
no insignificant whitespace, and no non-finite numbers. Receipts and generated
views bind that digest rather than copying objective fields without provenance.

Validate the contract and print its digest:

```bash
python3 projects/enwiki9/tools/research_contracts.py
```

Also verify the local corpus size and hashes:

```bash
python3 projects/enwiki9/tools/research_contracts.py --verify-corpus
```

Validate one or more receipts and hash every referenced payload file:

```bash
python3 projects/enwiki9/tools/research_contracts.py path/to/receipt.json
```

Use `--structure-only` only for diagnostic inspection. A promotion handoff must
retain the normal file-verifying result. Promotion-grade compression and
decompression guards each require their matching `--phase`, a measured
`--geekbench5-single-core-score`, aggregate process-tree RSS, a one-CPU affinity
union, and declared candidate scratch paths.

Create a new counted bundle under
`results/<candidate>/release/<receipt>/` with
`tools/enwiki9_dependency_closure.py`. A complete bundle must declare every dependency; a counted dependency's provider
must be a counted file, required options must occur in the declared commands,
and one bundled dependency must bind a counted license file. Commands use the
placeholders documented in `tools/README.md`.

Run `tools/enwiki9_clean_room_replay.py` only against a new bundle. It performs
two fresh-build full-corpus compressions and a third fresh-build decode. The
decode namespace never receives the corpus. Each runtime is restricted to one
logical CPU and measured for process-tree RSS, wall time, and candidate scratch
usage. A second host's complete primary receipt is required before the verdict
can become `objective-achieved`.

`tools/enwiki9_release_receipts.py` regenerates
`docs/release_receipt_index.json`. The index validates receipt structure and
hash-links each manifest, run, or failed attempt, but its
`structure-only-router` mode is not a replacement for full artifact validation.

The authority pages can change without notice. A content-hash change requires
a new contract version and revalidation before any promotion; historical
receipts retain the objective digest under which they were produced.

The optional `outputManifestPolicy` field is the backward-compatible migration
boundary for adaptive contract v1. Historical contracts without it retain their
original validation semantics. New multi-artifact experiments should declare
`complete-result-artifacts-v1`; omitting the policy grants no claim that the
contract's output list and the result's artifact list are complete.

The optional `pythonSourceClosureEntries` field is likewise backward compatible.
When present, every named entry must be a declared tool input and every Python
module it resolves under `tools/` must appear once in the same hash-bound input
manifest. If that closure reaches `research_contracts.py`, all JSON files under
this contract directory are runtime support inputs and must also appear once.
Experiment-specific non-Python patches, models, and data remain explicit inputs.
