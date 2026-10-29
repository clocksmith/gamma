# Shared study catalogue: migration preview

This package implements the owner's separate-destination migration from Gamma,
Simulatte/Lucyd and Hatch/Mesh. It does **not** switch any current consumer, approve
solutions, modify protected populations, download models, or deploy a site.

## One schema authority

- `schema.py`: canonical record/partial-field/embedding definitions.
- `graphs.py`: consolidated shared architecture models, semantic commands, simulation
  v4/v5 documents and the existing composable-study contract.
- `legacy/composable-study.v2.schema.json`: the starting study compatibility
  definition imported from Simulatte. It is consumed by generation, not separately
  rewritten by adapters. Simulatte's live format remains readable during migration.
- `schema.v1.json` and `schema.v1.ts`: generated, reviewable runtime schema and types.

Regenerate with `python3 projects/problem_catalogue/schema.py`. The old Algorithm
Solver proposal file now re-exports the generated types. Renderer, editor-command
execution and simulation behavior remain in Simulatte. The owner explicitly moved
shared graph data contracts here; this migration preview validates existing content
centrally and replays it through pinned snapshots of Lucyd's own semantic code.
Legacy runtime consumers will adopt generated outputs only after reconciliation
review; this tool does not silently switch them.

Records have stable source identities, explicit versions, pinned references and
per-field provenance. A present empty list is different from missing, unknown or
not-applicable. Large/native content remains in content-addressed blobs or explicitly
unopened external references. Backlinks use IDs; the hashed reference graph is acyclic.
Companies are sourced reports rather than employer confirmations. Admission decisions
are separate records; migration creates none.

## Run the eight phases

From Gamma, using Python 3 with the existing `jsonschema` package and Node for Lucyd
semantic replay. Git metadata is required. No model/package installation is performed.
Use a **private destination outside all three repositories**:

```sh
python3 projects/problem_catalogue/migrate.py all \
  --gamma /Users/xyz/deco/gamma \
  --simulatte /Users/xyz/deco/simulatte \
  --hatch /Users/xyz/deco/hatch \
  --destination /Users/xyz/.local/share/gamma-study-migration/catalogue-v1
```

Each phase also runs individually: `inventory`, `extract`, `resolve-identities`,
`convert`, `validate`, `build-catalogue`, `build-embeddings`, `reconcile`. Reuse the
same destination for subsequent revisions. Immutable record versions and source
snapshots remain; unchanged rows retain references even when newly arriving rows
are inserted ahead of them. Existing blobs/versions are never overwritten with
different bytes. A failed phase leaves its prior snapshots and diagnostic outputs;
rerun after fixing the cause. Generated discovery is built only after validation.

Every phase pins its migration tools and upstream phase hashes. Changing either
invalidates dependent phases; rerun from inventory after changing tools. Tool
snapshots and content-addressed phase history retain the earlier run. An exclusive
destination lock prevents concurrent writers. JSON inputs reject duplicate keys
and nonfinite values instead of silently discarding ambiguous content.

Optional inputs are explicit, not discovered by scanning private state:

- `--gamma-catalogue PRIVATE_METADATA_JSON`: known dual-language catalogue v1/v2
  metadata, including historical status/source/receipt bindings. It imports **no**
  qualification or receipt payload and follows no source/test locator.
- `--mesh-session PRIVATE_SESSION_JSON`: a deliberately selected Mesh session.
  Model suggestions remain model-generated and non-authoritative.

All phases operate offline unless an explicitly configured local encoder command
itself has additional behavior. The default source adapters perform no network
request. Default Mesh intake references integration code and owning catalogues;
no screenshots, microphone recordings, credentials or runtime state are scanned.

## What the adapters preserve

| Adapter | Result and boundaries |
| --- | --- |
| Official LeetCode metadata | Declared IDs/titles/slugs become metadata-only contracts; no statement inferred. |
| Gamma source files | Enumerates paths and Git identities without opening candidate code. Unresolved filename identities stay source-local; exact reviewed/declared manifest mappings can join them. |
| Hack2Hire authoring arrivals | Discovers hexadecimal variant filenames as well as numeric filenames. Keeps worklists and batch manifest/design/semantics metadata as native snapshots. Assignment status and filename matches establish neither exact contracts nor qualification. |
| Authored study records | Validates `*/study-records/*.json` contracts, approaches and artifacts against this schema; preserves declared IDs, ordered hints and stages. Rewrites pinned dependency references to migrated versions, retaining the original record bytes. Source FileRefs become explicit unopened external references. |
| Original paired-source manifest | Preserves declared native method/argument APIs, source SHA-256, definition pins and external source references. Development reports remain historical, partially bound evidence. |
| Explicit Gamma catalogue | Preserves every language/status record and original bindings as historical metadata. Never requalifies or admits it. |
| Hack2Hire | Preserves groups, all variants, previews, source labels, company/frequency reports and related-problem candidates. Group previews never become complete variant specifications. |
| Lucyd study and simulation | Preserves 46 source problem identities, both authored representation sets, stage order, explanations, APIs, checks, workloads, graphs and semantic edits. Native replay verifies transitions without running simulations. |
| Mesh | References the existing integrations; explicitly supplied session content retains generated provenance. |

Source-native records and original snapshots retain fields that have not yet been
normalized. These are **partial conversions**, not missing educational content
invented by the converter. Distinct study/simulation approaches remain distinct
unless an explicit mapping establishes equivalence. A source-local Gamma entry is
not an additional verified LeetCode problem. Generated counts distinguish namespaces.

Already-authored record imports do not recreate lessons from filenames. Missing,
cyclic, conflicting or hash-mismatched dependencies block their dependent records;
the original snapshots remain and `blockedOutputRows` explains the gap. A later
complete arrival can be imported on the next run. Declared implementation records
connect exact source paths to their problem without assigning identities by title.
Origins/provenance in migrated wrappers point to the authored record snapshot; its
unchanged source-native copy retains the author's original provenance. This proves
faithful import, not the truth or qualification of the author's claims.

## Outputs and review

`inventory.json` pins the input snapshot. `extract.json` and
`resolve-identities.json` retain per-source rows and proposed identity relationships.
`records/KIND/ID/vN.json` holds immutable records; `blobs/` holds pinned content.
`generated/discovery.json`, `company-index.json`, `completeness.json` and
`relationship-candidates.json` are generated views, not hand-maintained registries.
`validate.json` and `lucyd-validation.json` report schema/hash/reference/graph checks.
`reconcile.json` accounts for every inventoried file and extracted row, including
unsupported and blocked material, and identifies changes/new source files that
arrived after the snapshot, including newly added authoring metadata/worklists.
A faithful snapshot can be complete while the live
source repositories have moved ahead. Run again to incorporate those changes.

Encrypted collections are referenced as blocked. Protected candidate/test payloads
remain closed. No permission or source bytes are inferred from filenames or status
labels. Output is private and is not automatically publishable.

## Embeddings are derived and purpose-separated

Without an encoder contract, `build-embeddings` produces an honest blocked build
plan. It does not silently provision weights, borrow vectors with unknown execution
identity, or claim new vectors exist. Problem discovery excludes solutions; solution
study and artifact search get separate index manifests and binary files.

To build/reuse vectors, supply `--encoder-contract PRIVATE_ENCODER_JSON`, matching
`EncoderContract` in the generated types/schema. It pins a locally provisioned model
ID/revision (including a Hugging Face commit when applicable), model/tokenizer/adapter/
runtime manifests, instructions, pooling, normalization, dtype, token/truncation
policy, a character chunk recipe, dimensions, and the exact local encoder program.
The explicit argv receives one bounded JSON request on stdin and returns vectors
with matching IDs, text hashes and actual encoder identity. It must not download a
model as a fallback. This package provides the protocol, not another inference engine.
Use the existing Gamma/Doppler encoder behind a pinned adapter when provisioning it.

`--embedding-baseline PATH/TO/release.json` reuses vectors only when text, purpose,
encoder identity/program, dimensions and recipe match. Owner record revisions may
change without recomputation when the exact embedding input remains unchanged.
Vector byte counts, SHA-256, row identities/order, dimensions and finite float32
values are checked. No empirical retrieval quality follows from a successful build.
Synthetic test vectors test reuse mechanics only; they are not semantic embeddings.

## Focused verification

```sh
python3 -m unittest discover -s projects/problem_catalogue -p 'test_*.py'
```

Tests exercise protected/unopened source handling, partial fields, distinct variants,
no title merging, deterministic reruns, immutable revisions, newly arriving rows,
hash/path tampering, generated-type freshness and purpose-separated embedding reuse.
Direct authored-record tests also cover dependency rebasing, ordered hints,
unopened implementations and incomplete concurrent arrivals.
A full actual-repository preview additionally validates every emitted record and
Lucyd's source-native replay. It is migration evidence, not algorithm qualification.
