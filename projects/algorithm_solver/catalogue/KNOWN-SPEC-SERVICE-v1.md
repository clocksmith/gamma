# Executable exact known-spec service v1

`known_spec_service.py` provides an in-process adapter and command-line interface
over the **same** `KnownCatalogue`. It requires no informal classifier, embedding
model, corpus loader, candidate execution or network service. Exact IDs such as
`leetcode:10` return one identity with every separately qualified language slot.
Unknown, protected and wholly unqualified IDs abstain. A consumer can select a
language without changing identity; a missing language abstains, never redirects.
All outcomes contain zero clarification questions.

## Run

From the Gamma repository root, with a trusted operator-provisioned configuration
and its independently recorded SHA256:

```sh
python3 -m projects.algorithm_solver.catalogue.known_spec_service \
  --config /approved/config.json --config-sha256 "$APPROVED_CONFIG_SHA256" \
  --problem-id leetcode:10
```

Add `--language python` or `--language javascript` for consumer selection while
retaining the complete language-independent value. Add `--include-source` only
for an authorized, local exact-artifact read; this also requires a language and
source policy. Exit code 0 means a metadata match, not a query answer or execution
success. Exit code 2 is abstention, including invalid configuration.

An application may use:

```python
service = KnownSpecService.from_config(config_path, approved_config_sha256)
value = service.request('leetcode:10')
```

Configuration is operator state, not part of an untrusted request. The only
request inputs are identity, consumer language and artifact opt-in. This is not
a deployed HTTP endpoint and does not authenticate users or grant source access.
Hashes bind bytes; they do not establish the trustworthiness of their supplier.
The external receipt verifier remains the existing trust boundary.

## Pinned configuration contract

The JSON configuration has schema `gamma.known-spec-service.v1`. Required
`universe`, `catalogue` and `verified_receipts` each contain an absolute `path`
and raw-file `sha256`. The loader checks every digest before using JSON and then
constructs the existing validating `KnownCatalogue`. Metadata-only operation
requires no source locators or access policy and never opens candidate files.

Optional `source_access` contains:

- `aliases`, `locators`, `access_policy`: separate `{path, sha256}` records for the
  independently anchored development400-to-global alias manifest, existing
  permitted development source locators, and mandatory source-access policy.
- `development_universe_sha256`: the independently recorded raw-file universe
  anchor required by the aliases. Alias destination must equal the pinned global
  universe **raw-file hash**, not its canonical JSON digest.
- `authorized_problem_ids`: an explicit subset of the exact development alias
  destinations, within the global universe and disjoint from its protected IDs.
- `source_roots`: explicit absolute, operator-controlled immutable directories;
  no empty/root-wide/traversal roots. Provision their parent directories as
  trusted as well. Locator paths must remain under one of these roots.

The access policy must retain `new_source_access_authorized=false` and
`source_publication_authorized=false`, and its existing-source authorization set
must equal the alias destinations. Aliases must be one-to-one exact decimal
`development400:N` to `leetcode:N`, never title/similarity inference. Thus metadata
outside the previously authorized400 cannot request a source read, including IDs
whose broader reservation membership is not fully represented by the known66.
A config update cannot manufacture new authority: new populations require a
separately authorized policy/version, not editing this route's request fields.

The adapter authorizes before opening, builds locators bound to the validated
selected receipt/source and global universe, then calls the existing
`materialize.read_source`. Its no-symlink, regular-file, size and exact byte hash
checks remain in force. Returned UTF-8 source is labeled `artifact.materialized`:
**not executed, adapted, query-public verified, published or a serving release**.
Do not expose this local artifact result through a public endpoint under the
current source-publication restriction. Runtime identity attestation is separate;
this adapter deliberately does not import or invoke runtime/candidate executors.

## Checks performed

Eleven focused synthetic tests cover two-language metadata, unknown/invalid IDs,
policy/language requirements, exact synthetic bytes, denied nondevelopment IDs,
protected slots, roots, stale aliases/hashes, source mutation/symlink rejection,
mandatory policy and runnable CLI behavior. Synthetic source text is never run.

A real metadata-only dry check on the frozen complete universe routed all **4,081
IDs**: **400 matched, 3,681 abstained**, exposing **400 JavaScript +372 Python**
slots; all66 explicitly marked protected IDs abstained. `read_source` was replaced
with a failing sentinel for the complete check, proving that this path performed
zero candidate reads; no cases, models or candidates were loaded/executed. The
actual CLI was also run for `leetcode:10`, returning the two language slots.

Catalogue canonical digest:
`448af90d5178c02a5090986b7b10906384e7764db8c7d124af17ee5860661041`.
Private checked-config raw SHA256:
`b4f239461cd3c79dbf20b938104f574eac2c1d5e8977993e1ade846aba718061`.
The source-policy/artifact paths remain private operator configuration, not
committed candidate source. This is exact-route mechanism evidence; it is not
informal recognition, complete catalogue coverage or goal1c full-path latency.
Original frozen500 compact-library M1 remains unmet and separate.

```sh
python3 -m unittest projects.algorithm_solver.catalogue.test_known_spec_service
python3 -m py_compile projects/algorithm_solver/catalogue/known_spec_service.py
```

## Historical informal recognizer: identified assets, not loaded

Inspected public runtime/config **as data** at immutable GitHub commit
`32b0e46bc2909cde11659bc2927737791a4a28a1` in `clocksmith/gamma`:

| File under `projects/algorithm_solver/` | Git blob identity |
| --- | --- |
| `algsolve/embed.py` | `c78d3de57d6f92bc529dd380603348e5eab0a280` |
| `contracts/run_contract.json` | `fe779b91cd31fdcbbdb68c06e7aee4dcfc54dd47` |
| `contracts/lookup_thresholds.json` | `d3a38b9f9a601da42ad2fb168eb8bb5978c00743` |
| `contracts/statement_lookup_thresholds.json` | `452c343dbadcb8d2a527678094034783f0b66552` |

Embedding asset is **Qwen/Qwen3-Embedding-0.6B**, configured through
`ALGSOLVE_EMBEDDING_DIR`. The code pins:

- `model.safetensors` SHA256
  `0437e45c94563b09e13cb7a64478fc406947a93cb34a7e05870fc8dcd48e23fd`;
- `tokenizer.json` SHA256
  `def76fb086971c7867b829c23a26261e38d9d74e02139253b38aeb9df8b4b50a`.

`LazyCPUEmbedder` uses four torch threads, CPU float32, left padding, a1024-token
limit and normalized final-token pooling. These settings, the exact query
instruction in `embed.py`, tokenizer/model configuration files and their runtime
versions must remain pinned for a safe future reproduction. A model repository
name alone is insufficient; this inspection did **not** verify installed assets,
all auxiliary configuration hashes or a complete Hugging Face revision.
No model was downloaded or instantiated.

The historical approved route requires a serving-runtime-bound approved manifest,
`data/derived/corpus_embeddings.npy`, matching
`data/derived/corpus_embedding_keys.json`, and index identity/statement/interface
metadata. Legacy `data/derived/corpus_entries.jsonl` embeds references and must
**not** be loaded wholesale. The alternative research index is
`data/derived/index_embeddings.npy` with `index_embedding_keys.json`; it is a
different population, not a drop-in replacement.

Keep both frozen threshold files unchanged: lookup score1.096599/margin0.0;
statement score0.634824546178182/margin0.004102371987842357; the approved sibling
guard additionally retains0.02. These values are historical configuration, not
new estimates or an authorized fit. The run contract binds120-second route /
30-second judge /10-second reserve budgets. No fallback generator is needed for
qualified lookup, and no generation/training is enabled here.

**Remaining safe-context gap for1b:** obtain independently anchored metadata-only
index rows with exact key/ID mapping and permitted statement/interface inputs;
apply the existing family/member/near-duplicate exclusion closure before any
source access; verify index vector/key order and hashes against that snapshot;
provide the pinned encoder configuration and runtime; preserve existing confidence,
identity, absence/ambiguity and query-public verification gates. Historical
boundary inputs are named in `library_audit.py` as
`contracts/typed_confirmation_v1.json`, metadata from `data/derived/problems.jsonl`
and `data/derived/near_duplicates.json`; do not use full problem/source/case
loaders to extract them. Their current safe projection and exact artifact hashes
were **not** inspected or established here. No protected scoring or recognition
release follows from the new exact-ID CLI.
