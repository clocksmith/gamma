# CATSCAN: Maintained enwiki9 framework

Parent: [enwiki9](../CATSCAN.md)

## Target

Maintain execution, evidence, lifecycle, packaging and reporting services while preserving historical bytes.

## Authority

- `execution`: bounded processes, leases and cancellation.
- `evidence`: authenticated artifacts, declared closures, validation and witnesses.
- `research`: lifecycle coordination through the lab CLI.
- `packaging`: explicit entrypoints and delivery inventories.
- `reporting`: read-only projections and explicit host observations.
- `adapters`: experiment-specific policies and recipe adaptations.

## Scope

Python services and experiment-specific native diagnostic sources under
`gamma_enwiki9/`. Native diagnostic sources belong to adapters; the existing
execution services retain process and resource authority.

## Contracts

- Input: Identities, roots, populations, budgets, build profiles and dependencies.
- Output: Execution outcomes, evidence reports, scientific decisions and package inventories.

## Invariants

- Services never import the lab or research application.
- Evidence never imports reporting, execution or experiment adapters.
- Pure projection never reads procfs, samples CPU state or mutates records.
- Static closure is relative to declarations; dynamic loading requires explicit dependencies and restricted replay.
- Terminal interpretation resolves original input identities; launches require current bindings. Original-validator replay remains separate.
- Virtual address limits exceed resident budgets only with an identity-bound inherited memory cgroup.
- Immutable publication, derived replacement and canonical append remain distinct operations.
- Process success never grants score credit.
- Adapter-owned native diagnostics receive explicit inputs and emit measurements;
  they do not launch experiments, mutate lifecycle records or grant promotion.

## Acceptance

[Explicit test groups](../tests/run_architecture_groups.py) cover pure behavior, codec equivalence, native fixtures, historical closure and separately provisioned Linux resources. Tests never recurse through results.

## Non-goals

Moving all historical runners, changing algorithms during extraction, replacing the queue/blob store, or granting qualification from synthetic fixtures.

## Freedom

Algorithms may change within these evidence boundaries.
