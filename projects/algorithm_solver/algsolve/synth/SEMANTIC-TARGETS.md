# Family-first semantic target preparation

`semantic_target_pipeline.py` adds a development-label workflow alongside the
historical exporters. It does not replace their datasets, change a reservation,
train a student, open protected evaluation, or claim unseen-family performance.
Algorithm Solver component intent and acceptance thresholds are unchanged.

## Freeze before generation

The planner accepts a JSON array containing only these metadata fields:

- `uid`, `key`, `family`: stable identities and a reviewed semantic family.
- `aliases`: other known problem UIDs or catalogue keys, including cross-source
  aliases and alternative implementations of the same problem.
- `structural_groups`: known shared patterns declared before target generation.
- `problem_sha256`: `semantic_target_pipeline.digest(json.loads(problem.to_json()))`.
- `independent_tests_sha256`: the same canonical digest of the authorized
  independent development test array, before teacher generation.

Metadata must be prepared through an authorized source adapter. Producing these
digests is not permission to open any protected payload. Reuse existing metadata
and authority hashes for reserved records. Statements, source, tests and target
programs are rejected by the planner's metadata schema.

The boundary JSON must contain `uids`, `keys`, `families`, `structural_groups`
(arrays) and `sources_sha256` (a nonempty mapping of existing boundary authority
names to SHA-256 digests). The caller must supply the complete metadata-only union
of existing protected solving, recognition, confirmation, alias and structural
reservations. Hashes bind that declared union; they do not establish its
completeness or confer access authority. Existing reservation files are never
rewritten. This module does not read the full corpus to reconstruct a boundary.

From the repository root:

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.synth.semantic_target_pipeline \
  --metadata /authorized/identity-metadata.json \
  --boundary /authorized/existing-reservation-union.json \
  --allowlist /authorized/development-allowlist.json \
  --holdout-family selected-family \
  --recombination-uid lcd:selected-combination-uid \
  --output /new-run/family-plan.json
```

All aliases, same-family problems and declared shared structures stay in one
connected component. Existing protection (`excluded_existing`) takes precedence
over all other splits. When `--allowlist` (`uids`, `keys`, `sources_sha256`) is
supplied, any unallowlisted entry or unallowlisted alias marks its entire
connected alias, family and structural-group component `excluded_unallowlisted`
so unknown entries, non-allowlisted catalogue rows and cross-family aliases stay
excluded. When `--recombination-uid` is supplied, selected fitting UIDs within
seen families become `heldout_combination` while requiring every such family to
retain at least one `development_fit` example. Other components become
`development_fit`. There must be at least one fitting component and one new
held-out component (`heldout_family`). The plan is deterministic, hash-bound
and write-once. Slug sibling closure is additional protection, not a substitute
for semantic family review. Do not discover held-out structure by generating or
inspecting targets after the split.

## Build through authorized offline adapters

Call `build_targets(plan_path, output, codec_path=..., teacher_identity=...,
load_problem=..., propose=..., load_independent_tests=...)` from a local driver:

- `load_problem(row)` returns a normalized `Problem` matching the frozen UID and
  complete payload digest. Only `development_fit` rows are passed to it.
- `propose(uid, public_input, plan_sha256)` returns between one and
  `max_proposals` proposals, four by default. Each proposal has exactly `variant`,
  `program`, `requirements`, and `bound_probe`. `program` uses the existing typed
  AST schema; `requirements.unsupported_requirements` must be an empty array;
  `bound_probe` is one declared test with `args` and `expected`.
- The teacher receives only statement, starter, parameter types and public
  examples, along with the identity and frozen plan hash. It does not receive
  reference solutions, independent tests, or qualification feedback. Supply
  already authorized local teacher output or separately authorized offline
  compute. This builder neither downloads weights nor invokes a remote provider.
- `load_independent_tests(row)` runs only after raw proposals are recorded. Its
  nonempty test list must match the pre-generation digest. Tests and detailed
  failure receipts stay outside the model input. No teacher retry sees them.

The existing frozen typed codec validates bindings and expands the AST. Python
compilation checks syntax without executing the target. Public, independent and
declared-bound tests then run through the existing repository sandbox judge;
incomplete or failed receipts emit no target. Native qualification (`judge=None`)
requires Linux with the unchanged `bwrap` and `prlimit` sandbox and fails closed
before creating an output directory on macOS or hosts missing those tools; no
direct-execution fallback is provided when the teacher or sandbox is missing. The
declared bound probe is not independent evidence of asymptotic complexity.

Successful pairs retain all family/group identities, feature and pattern hashes,
source attribution, codec, teacher, implementation and plan bindings. Every raw
proposal and rejection is retained separately. Output directories are new-only.
Plan, codec or implementation drift aborts before the final pairs file is
published. Generated variants never cause post-generation repartitioning.

The optional `judge` injection exists for unit tests: its pairs are explicitly
`training_eligible: false` and use `qualified_test_double`, never real sandbox
qualification. A new consumer must check `training_eligible`, the summary and
its artifact hashes. Do not pass test-double output to legacy training consumers
that ignore that field. This builder does not update an existing training corpus.

## Evidence limits

Focused tests exercise synthetic metadata, lazy access boundaries, compiler
rejection, independent-test failure, unavailable services, immutable artifacts and
input isolation. They do not qualify a new model, real target corpus or protected
benchmark. Real preparation requires the authorized metadata/boundary union,
teacher adapter and functioning sandbox. Future training and reserved scoring
retain their separate authorization and frozen acceptance gates.
