# Authoring artifact utilities

These opt-in, standard-library tools organize explicitly supplied, cleared
authoring artifacts. They do not replace the normalization ledger, approved
lookup catalog, qualification harness, or composition optimizer. They never
import or execute candidate programs and do not perform network or GPU work.
Only the requested output file is written; keep it separate from input artifacts.

## Run and test

Use Python 3.10 or newer from `projects/algorithm_solver/`:

```sh
python3 literals/seed-inventory-v1/inventory.py /path/to/cleared/batch-a/manifest.json --output /tmp/line-witnesses.json
python3 -m algsolve.authoring_variants /path/to/cleared/batch-a/manifest.json --output /tmp/authoring-variants.json
PYTHONPATH=.:tests python3 -m unittest -v test_authoring_variants
python3 -m unittest discover -s literals/seed-inventory-v1 -p test_inventory.py
```

Both commands accept multiple manifest paths. Tests generate synthetic files in
temporary directories; no corpus sources, assignment packets, qualification
receipts, generated catalogs, or private tests are included with these tools.

The existing `literals/seed-inventory-v1/inventory.py` remains the single physical-line
implementation; it is not copied into `algsolve`. The standalone
`variant-catalog-pilot-v1/catalog.py` becomes `algsolve.authoring_variants`, preserving
`build`, `query` and its pilot schema. Generated artifacts remain external inputs.

The [block inventory](literals/block-inventory-v1/README.md) reuses this catalog for
source identity, adding complete Python statement/block spans and conditional
contracts. Structural proposals are not semantic equivalence or qualification.

## Physical-line witnesses

[`literals/seed-inventory-v1/inventory.py`](literals/seed-inventory-v1/inventory.py) reads each
manifest's `source_inventory` rows: positive integer `id`, `language`
(`python` or `javascript`), relative `path`, and source-byte `sha256`.
Numeric source basenames must match the problem ID and language extension.
Manifest-parent directory names must be unique and become relative provenance
labels. Duplicate language/problem identities or resolved source paths reject.
This pilot intentionally expects one source per problem/language; it does not
consume the multi-variant catalog or choose between alternatives automatically.

The tool emits lines witnessed in at least two distinct problem IDs, separately
by language. Each witness includes exact text, its UTF-8 hash, source and 1-based
line occurrences, occurrence count, and distinct-problem support. LF, CRLF and CR
terminators are normalized and excluded; all horizontal whitespace is preserved.
Blank lines are omitted. Input order and absolute workspace location do not affect
output when manifest bytes and directory labels are unchanged.

These are complete **physical lines**, not necessarily complete statements or
reusable components. Comments, braces, headers and multiline fragments can occur.
An existing parser/frontend must identify usable statements, bindings and effects
before any proposal is admitted. Identical text is not semantic interchangeability;
renamed or structurally similar code is not exact literal reuse.

## One-to-many authoring variants

[`algsolve/authoring_variants.py`](algsolve/authoring_variants.py) additionally
requires a hash-pinned `assignment.public-safe.json` next to each manifest, a
manifest `files` list, and hash-pinned semantic-declaration JSON per source.
Explicit `semantics_path`/`semantics_sha256` references take priority; otherwise
the declaration uses the numeric source basename with `.semantics.json`.

Packet problems require `external_interface`, `statement_constraints_snapshot`
and `return_domain`. Available objective, domain, comparison, mutation/aliasing,
numeric/complexity and fixed-constant declarations also affect contract identity.
A variant ID hashes problem ID, language, source hash, semantic-declaration hash
and public behavioral-contract hash. Multiple source variants for one
problem/language coexist; identical identities deduplicate while preserving
distinct provenance. Conflicting contract versions for one problem reject rather
than silently merge. Separate contract namespaces are not implemented.

The output's `index[problem_id][language]` contains lists of variant IDs.
`query(catalog, problem_id, language)` returns every matching record, without
ranking. `preferred_variant` is null. All qualification statuses remain unknown,
including when input prose claims acceptance. Qualification receipt ingestion
and end-to-end joins into serving or composition catalogs are not implemented.
Original source bodies, packet bodies and semantic-declaration bodies are not
embedded; identities and relative provenance remain hash-linked.

## Trust and integration boundaries

- The caller must supply already-authorized snapshots and preserve exposure and
  reserved-family restrictions. These tools do not discover or authorize inputs.
- Hashes establish byte identity and reference consistency, not semantic truth,
  authentic authority, binding correctness, execution success or admission.
  Semantic-declaration JSON is checked for parseability, not a required schema
  or agreement with the source program.
- Path checks reject parent traversal, escaping paths and source-file symlinks;
  this is not a hostile concurrent-filesystem security boundary.
- Generated witnesses contain source text; generated catalogs contain provenance
  metadata. Keep outputs private unless separately authorized for publication.
- Dictionaries returned by the Python APIs are mutable. Changing a record does
  not preserve the validity of its stored content identity.
- Qualification stays with the existing hash-bound ledger and judge. New rewrites
  need new hashes and the applicable independent checks, including effects,
  aliases, types, numeric domains and complexity obligations.

These utilities preserve the existing component authority and admission gates.
They establish neither semantic alignment, compression improvement, optimality,
human learnability, autonomous assembly nor unseen-problem performance.
