# Deterministic reviewed-contract recognition documents

`recognition_documents.py` builds documents, **not embeddings or recognizer
verdicts**. No candidate, model, training job, downloader or case loader executes.
No description cohort or sealed confirmation file is an input.

## Population and knowledge policy

The production plan retains all **4,081** metadata identities in their original
index order. Protected, unknown, unqualified and unavailable identities remain
competitors. Access/qualification status is never used to remove or rerank rows.
The builder rejects an incomplete or reordered baseline index.

Every row starts with its exact title bytes. An optional externally pinned
`baseline_documents` artifact binds the existing title-only index. Its
`documents` rows must contain exactly `problem_id` and `text`, with the latter
equal to the independently pinned metadata title. Unchanged rows preserve those
bytes exactly—no ID prefix or trailing newline is silently added.

Only an explicitly listed, independently reviewed authority can append these
fields, in fixed order: objective, result, input domain, ordered solve interface.
Structured values use deterministic JSON. No source, examples, cases, reviewer
identity, availability flags or receipt text are copied into ranking text.
Stable IDs remain separate keys. Knowledge class, exact authority hashes and
field provenance remain separate metadata, not encoder features.

**Title-only means unknown contract knowledge**, not false, unsupported,
semantically inapplicable, or absent from the problem universe. Enriching a small
subset introduces explicit knowledge asymmetry; subsequent measured results
must disclose it. This representation cannot prove universal recognition safety.

## Two authority adapters

1. `normative-catalogue`: operator-pinned catalogue, universe and independently
   verified receipts; exact global ID, chosen language and problem-contract hash.
   The existing catalogue validator checks interface, evidence class and all
   receipt bindings. Only `normative-typed-effects` contracts from the supported
   `public_foundation` or `public_batch` provenance shapes may supply text.
   Historical frozen-admitted evidence and compatibility probes cannot silently
   become official-domain authority.
2. `reviewed-public-batch`: operator-pinned independent authority review, freeze
   and review receipt, all mutually hash-bound, with an exact per-ID statement
   identity. This permits reviewed statement knowledge before source
   qualification. It **does not create source qualification** or authorize a
   returned implementation.

Artifact names/paths are operator inputs, never request inputs. Embedded paths
are not followed. Operators must provide approved metadata/public-authority
files only, never candidate or case files. Explicit roots, bounded regular-file
reads, no-follow path components, duplicate-key rejection and exact SHA checks
provide integrity, not a substitute for the operator's authorization.

Immediately before **each authority artifact open**, the builder calls the
independent live boundary gate, rereading and validating all six boundary
metadata pins for that ID and statement access. Reserved/unknown IDs cannot be
enriched through a forged qualification flag. They still retain title-only
competitor rows. A bad supplied authority fails the build; missing authority
simply leaves a title-only document.

## Cache discipline

Each document records UTF-8 byte count, SHA256, baseline text SHA256 and whether
its text changed. Output separately lists changed and unchanged stable IDs.
Only changed documents need new vectors **if** all other encoder/tokenizer,
pooling, instruction, truncation and normalization identities remain identical.
Text equality alone does not validate those identities. This builder never loads
or overwrites vectors. Existing title vectors and historical experiments remain
immutable; an enriched representation requires its own linked policy/evaluation
freeze before any measurements.

## Operator usage

```
python -m projects.algorithm_solver.catalogue.recognition_documents \
  --plan /approved/private/plan.json --plan-sha256 APPROVED_SHA256 \
  --output /new/private/documents.json
```

Plan schema: `gamma.recognition-document-plan.v1`; required fields are
`title_metadata`, `boundary_gate`, `authority_roots`, `authorities`, and
`expected_population`, with optional `baseline_documents`. Each pinned artifact
descriptor contains an absolute `path` and SHA256. Output is created exclusively;
existing files are not overwritten by the CLI.

Synthetic tests cover full competitor retention, deterministic document bytes,
explicit title-only uncertainty, policy drift between reads, denied pre-open
access, exact global identity, hash/authority/interface mismatch, source paths
not followed, root symlinks, and exact baseline delta reuse. A private metadata-
only smoke build retains all4,081 rows and enriches only20 already independently
normative-qualified domains;4,061 title documents remain byte-identical. No
encoder or confirmation cohort was accessed.
