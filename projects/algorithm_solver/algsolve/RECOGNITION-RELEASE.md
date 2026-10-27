# Coherent recognition/BITS candidate bundles

`recognition_bundle.py` packages **already authorized** inputs into an immutable,
content-addressed release directory. It does not acquire descriptions, train/load
models, confer publication rights, qualify recognition, deploy a server, or alter
existing BITS hosting. Source acquisition permission is not publication permission.
Solution guides and cases are not statement-packet assets.

The current [local discovery adapter](BITS.md) is a separate, legacy startup path.
It does **not yet consume this bundle pointer or enforce a client release ID**.
Do not claim that producing a bundle activates that server. A serving-owner
integration and an established permitted deployment target remain prerequisites.

## Operator inputs

`prepare_release(source_root, releases_root, specification,
publication_permissions=registry)` reads only explicitly listed source paths. All
source paths must already be authorized for the intended use, including private
recognition documents. It stages a fresh directory, verifies it, and renames it to
`releases_root/<release_id>`. The ID is SHA256 of canonical JSON for the complete
specification. An existing same-ID release is verified and reused, never replaced.
Partial staging directories do not become releases; the operation can be rerun.

The specification has exactly these fields:

- `schema`: `gamma.recognition-bundle.v1`.
- `ordered_problem_ids`: unique canonical `leetcode:<positive integer>` IDs in
  vector row order. Protected competitors may remain in their frozen positions;
  this never permits opening their descriptions.
- `vector_dimension`: the explicitly pinned embedding dimension.
- `components`: paths for `index_keys`, `index_vectors`, `documents`, `aliases`,
  `preprocessing`, `runtime`, `vector_binding`, `bits_catalogue`, `bits_manifest`,
  and a nonempty `model_manifests` path list.
- `files`: exact relative-path descriptors with `role`, `sha256`, `bytes`,
  `publication` (`private` or `public`), and `permission_id` (null for private).
  Public files must be beneath `public/`. Roles for components use hyphenated
  names, e.g. `index-keys` and `bits-catalogue`; model manifests use
  `model-manifest`. Additional public files may only be `bits-packet` or `public-ui`.
- `publication_permissions`: grant ID to canonical grant SHA256. This binds the
  approved provenance; it does not make a self-authored grant authoritative.

The external operator registry maps grant IDs to objects containing nonempty
`authority` and `reference`, `scope: public-recognition-assets`, and `assets` mapping
exact release-relative paths to approved SHA256 values. Every public asset needs
an exact grant before any public payload is opened. Grants for previous complete
releases must remain available for verification and rollback. A registry may
contain extra grants; only the release's exact referenced grants are used.

## Cross-component checks

- `index_keys` is an ordered unique list of canonical `leetcode:<ID>` keys
  (preferred), or independently mapped `lc:<slug>` aliases. `aliases.by_key`
  resolves each indexed key to the corresponding ordered canonical ID; a
  canonical key must map to itself. No missing slug is guessed or required.
- `documents.documents` has one row per canonical ID in the same order, including
  `problem_id`, exact UTF-8 `text`, `document_sha256`, and UTF-8 `bytes`.
- `preprocessing` explicitly records `encoder`, `model`, `adapter`, `tokenizer`,
  `pooling`, `normalization`, `truncation`, and `document_instruction` identities.
  `runtime` and all model manifests are separately bound nonempty JSON objects.
- `vector_binding` uses schema `gamma.recognition-vector-binding.v1`. Its
  `component_sha256` maps `index_keys`, `index_vectors`, `documents`, `aliases`,
  `preprocessing`, and `runtime` to exact hashes, plus `model_manifests` mapping
  manifest paths to hashes. Its ordered `rows` contain `problem_id`,
  `document_sha256`, raw little-endian float32 `vector_row_sha256`, `origin`
  (`generated` or `reused`), and the genuine execution/reuse `provenance_sha256`.
  This packages externally established lineage, not a substitute for proving it.
  Missing historical provenance must remain a separately identified baseline;
  do not invent hashes or claim dimension equality establishes compatibility.
- Vectors must be C-order, little-endian float32 NPY, with the exact row count and
  dimension, finite values, and unit norms within `1e-4`. NPY headers are bounded
  and parsed without pickle or a model dependency.
- `bits_catalogue.problems` contains explicit `key`, `problem_id`, `title`, and
  `slug` rows. Its key set exactly equals the indexed keys; implementation
  availability does not filter it. `slug` can be null for canonical-ID keys.
  A non-null slug must be a proven alias of that same canonical ID.
- `bits_manifest.problems` is keyed by exactly those index keys, not slugs. Each row names `problem_id`
  and either `scope: metadata-only` with **no payload path**, or
  `scope: public-statement` with an explicitly granted `path` and `sha256`.
  Every public packet is referenced exactly once.
- A public statement packet has exactly `schema: gamma.bits-public-statement.v1`
  and `problem`, whose fields are `problem_id`, `key`, nullable `slug`, `title`,
  and `statement`.
  Additional solution bodies, examples/cases, or starter/source fields are rejected.
  Those require separately authorized artifact classes and must not be smuggled
  through a recognition packet.

Verification rejects unlisted files, symlinks, hard-linked assets, path traversal,
duplicate JSON fields, mismatched orders/identities, and changed hashes. Reads are
bounded to 20,000 files, 256 MiB per file, 512 MiB total, 32 MiB per JSON file, and
16 path components. Actual embedding/rebuild processes still require the owner's
hard process-group lifetime and aggregate-memory supervisor; these file limits
are not a compute envelope.

## One pointer, one rollback

`verify_release(directory, expected_release_id=..., publication_permissions=...)`
verifies a complete candidate without activating it.

Once separately authorized by the established serving owner:

1. `activate_release(state_root, directory, expected_current_release_id=...,
   publication_permissions=...)` validates the successor and current complete
   release, then atomically replaces `active.json`. The pointer contains both
   current and previous content-addressed directories. Initial activation expects
   `None`; subsequent activations require the exact observed current ID.
2. A serving integration calls `resolve_active_release(...)` **once per snapshot**
   and uses that returned directory for both index and BITS assets. It must compare
   the page/client's expected release ID before model execution and reject
   `ReleaseMismatch` (for HTTP, an explicit conflict response is appropriate).
   Resolving static and index paths independently would reintroduce split releases.
3. One rollback operation restores both components:

   ```python
   rollback_release(
       state_root,
       expected_current_release_id=deployed_release_id,
       publication_permissions=approved_registry,
   )
   ```

Rollback revalidates the retained predecessor and atomically swaps the pointer.
It can recover even if the current candidate has become corrupt. Neither release
is deleted. Pointer changes use a locked compare-and-swap, fsync, and atomic rename;
an interrupted publication preserves the prior pointer. This API only changes
local release state: service restart/snapshot lifetime and any remote promotion
belong to the authorized serving integration.

## Evidence scope

Run focused synthetic checks:

```sh
PYTHONPATH=.:projects/algorithm_solver python3 -m unittest \
  projects.algorithm_solver.tests.test_recognition_bundle
```

These tests cover bundle integrity, authorized asset selection, complete-snapshot
selection, stale versions, interruption, and rollback. They do not establish
recall, ranking, ambiguity calibration, latency, vector lineage, public deployment,
or production lookup health.
