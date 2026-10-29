# CATSCAN: Shared problem catalogue

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Preserve source meaning in a versioned, reversible study catalogue with explicit partial content and evidence.

## Authority

- Owns migration, consolidated problem/graph data contracts, generated schemas/types and derived indexes, by owner direction.
- Simulatte retains rendering, command execution and simulation semantics; Gamma retains algorithm qualification; Hatch consumes records.
- Does not own source-access permission, source publication or automatic consumer migration.

## Scope

`projects/problem_catalogue/`; migration output stays outside source repositories.

## Contracts

- Input: [source adapters](migrate.py), [record definitions](schema.py), [graph definitions](graphs.py).
- Output: [JSON Schema](schema.v1.json), [TypeScript](schema.v1.ts), immutable records, source accounting and embedding plans.

## Invariants

Preserve source identities, versions and bytes or explicit unopened references. Never merge by title, filename or vector similarity. Missing, unknown and present-empty differ. Retain historical evidence without qualification upgrades. Protected payloads and encrypted collections stay closed. Hashed references remain acyclic. Problem recognition excludes solution text. Schema consolidation alone switches no legacy consumer. No automatic downloads, execution of candidate programs, deployment or publication.

## Acceptance

[Focused checks](test_migration.py) verify immutable revisions, partial fields, hash/reference integrity, new arrivals and embedding reuse. Actual migrations reconcile every input and replay Lucyd graphs through pinned native semantics. Report blocked inputs and stale snapshots.

## Non-goals

Another judge, renderer, simulator or inferred qualification registry.

## Freedom

Any implementation preserving these boundaries and recorded source meaning.
