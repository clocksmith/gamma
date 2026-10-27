# Source-to-guide admission and joint vocabulary work

Owner direction, 2026-10-26. This is the prospective operating contract for the
new candidate-creation work. Historical populations, verdicts and dictionaries
remain immutable controls. No new corpus or evaluation split is frozen yet.

## Inventory before freezing

`guide_admission.py` projects the existing pinned catalogue, externally verified
receipt bundle, source-access policy and scoped source census. It retains every
problem and both language slots. Canonical variants and imported source references
stay distinct: the census is neither an admission ledger nor an exhaustive inventory
of all implementations. The authoring registry remains
`algsolve/authoring_variants.py`; it supplies variant identities and provenance,
not qualification. Additional variants must be joined to their own exact evidence.

The current command is an inventory, **not a completed admission queue or corpus
freeze**. Each row records source/interface/test/runtime/effect hashes, receipt
binding status, permission, aliases, known historical development exposure and
explicit unresolved transitions. Unknown exposure never means fresh. Missing
adapter/license joins mean *not joined*, not evidence that no such record exists.
No null field can satisfy admission, and no candidate import becomes a guide.

The optional source check delegates to the existing `KnownSpecService` gate:
only authorized qualified slots are materialized, with exact source identity and
per-open protection checks. It does not execute candidates, read cases, assess
browser compatibility or rerun the independent receipt verifier.

Run from the Gamma root under a process-group supervisor with memory and wall
limits:

```sh
.venv/bin/python -m projects.algorithm_solver.catalogue.guide_admission \
  --config /absolute/private/inventory-config.json \
  --config-sha256 OPERATOR_PINNED_SHA256 \
  --verify-sources --output /absolute/private/new-snapshot
```

The JSON config has exactly `service` and `source_census`, each an absolute
`path` and SHA-256 descriptor. Service uses the existing v2 configuration.
No input source/reference paths from the census are followed. Omit
`--verify-sources` for metadata-only inspection. The private output directory
must not exist; it receives `queue.json`, aggregate `summary.json` and detached
`SHA256SUMS`. Do not commit private per-ID membership or source locators.
The snapshot binds input and implementation hashes; it does not certify freshness.

## Corpus and evidence requirements

Before assigning a split, join exact source, interface, adapter, tests, provenance,
license and permission records; verify deterministic behavior and applicable host
API constraints. Preserve the specification, mutation/identity, numeric and
complexity obligations. Bounded checks are bounded evidence, never proofs.

Group each canonical problem, both languages, aliases and near-duplicate variants.
Unknown grouping is a blocker, not permission to assign independently. Record
prior fitting/curation exposure. Existing protected populations remain protected.
Resolve catalogue family/difficulty/batch metadata before a deterministic grouped
assignment. Keep manifests immutable, with detached checksums and exposure history
across versions. No new seed, label or variant ID restores consumed evaluation data.

## Candidate creation and comparison

Preserve original sources. Identify explicit qualified alternatives through the
authoring registry. Prefer conventional names, consistent formatting and shared
programming idioms; unsafe renaming, coercion/control-flow changes and uncharged
helpers are forbidden. Alternate qualified source choice, literal selection and
exact segmentation instead of only refitting a fixed source corpus.

Keep two pools separate: human-oriented coherent exact strings and compression-only
arbitrary fragments. Label assistant-authored seeds as such. Syntax analysis may
propose recurring structure, but eligible literals emit exactly their stored text.
Parameters, helper insertion, macros and editor actions require separate declared
representations and full cost accounting. Complete answers cannot hide in entries.

Compare seed-only, machine-only and combined pools under identical budgets at
16, 32, 64, 128 and 256 entries. Retain minimum-cost segmentation paths and declared
tie-breaking. Unmatched text is uncovered. Report coverage, regressions, median/p95
selections, absolute singleton bits and their percentage, encoded bits, storage,
operands/helpers/constants and readability separately by width and language.
Padding to dilute singleton share is forbidden. Preserve the original compact-library
population and gates: median at most 32, p95 at most 96, at most 10% singleton bits.
Smaller exploratory vocabularies may have explicit partial coverage; limited search
failure proves no general impossibility.

## Confirmation and publishing

Freeze candidates before independently authorized confirmation. Once confirmation
informs tuning, retain it as consumed development evidence. Exact reconstruction,
behavioral acceptance, compression and human use are separate outcomes.

Counterbalance interfaces on matched unfamiliar tasks; measure completion time,
errors, lookups, corrections and delayed retention. Distinguish guided playback
from independent composition. Human studies require real participants; simulated
users or assistant judgments cannot establish fluency. Publish uncertainty and
negative results. Promote only demonstrated benefits through Gamma's selected
package and 256one's browser validation/publishing pipeline, preserving old IDs.

## Current result and next concrete joins

The [inventory summary](guide-admission-v1/summary.json) checks metadata bindings
and canonical source bytes. It does not assign splits or qualify new guides.
The next work is source-specific license/adapter evidence, additional variants,
historical exposure and near-duplicate grouping. Then freeze the admitted corpus,
create idiom candidates, compare them, and validate a selected browser package.

The current 150 JavaScript BITS guides are different source variants from this
canonical catalogue: 121 have a qualified canonical counterpart with different
bytes; 29 have no qualified canonical slot in this snapshot. None is an exact
canonical source match. This does not revoke their separate historical guide
evidence; it means that evidence cannot be transplanted onto canonical sources.
