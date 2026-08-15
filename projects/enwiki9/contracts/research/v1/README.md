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
- `delta-midas-probe-result.schema.json` binds prospective partition, leakage,
  causal-feature, quantized-model, shifted-control, and held-out evidence for
  the compact residual probe;
- `mechanism-graph.schema.json` prevents additive component forecasts by
  binding shared probability boundaries, cost overlap, causal compatibility,
  closed dependencies, and an exact joint-replay requirement;
- `dependency-closure.schema.json` binds every counted package member,
  dependency, command, license, and option byte;
- `run-receipt.schema.json` composes exact corpus, archive, package,
  correctness, resource, distribution, and independent-verification evidence.
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

The authority pages can change without notice. A content-hash change requires
a new contract version and revalidation before any promotion; historical
receipts retain the objective digest under which they were produced.
