# CATSCAN: Maintained enwiki9 framework

Parent: [enwiki9](../CATSCAN.md)

## Target

Provide one maintained namespace for execution, evidence, lifecycle, packaging and reporting while preserving historical bytes.

## Authority

- `execution`: bounded processes, leases and cancellation.
- `evidence`: authenticated artifacts, declared closures, validation and witnesses.
- `research`: lifecycle coordination through the lab CLI.
- `packaging`: explicit entrypoints and delivery inventories.
- `reporting`: read-only projections and explicit host observations.
- `adapters`: experiment-specific policies and recipe adaptations.

## Scope

Maintained Python framework services under `gamma_enwiki9/`.

## Contracts

- Input: Explicit identities, roots, populations, budgets, build profiles and dependencies.
- Output: Separate execution outcomes, evidence reports, scientific decisions and package inventories.

## Invariants

- Services never import the lab or research application.
- Evidence never imports reporting, execution or experiment adapters.
- Pure projection never reads procfs, samples CPU state or mutates records.
- Static closure completeness is relative to declarations; dynamic loading and external runtimes require explicit dependencies and restricted replay.
- Immutable publication, derived replacement and canonical append remain distinct operations.
- Process success never grants score credit.

## Acceptance

[Explicit test groups](../tests/run_architecture_groups.py) cover pure behavior, codec equivalence, native fixtures, historical closure and separately provisioned Linux resources. Tests never recurse through results.

## Non-goals

Moving all historical runners, changing algorithms during extraction, replacing the queue/blob store, or granting qualification from synthetic fixtures.

## Freedom

Internal algorithms may change while these boundaries and evidence contracts hold.
