# CATSCAN: Mandate 2038

Parent: [Gamma games](../CATSCAN.md)

## Target

Deliver a coherent, replayable institutional strategy game whose authored rules, browser runtime, physical specification, and evidence agree.

## Authority

- Owns Mandate 2038 mechanics, authored copy, runtime projections, simulation, physical specification, balance evidence, and release records.
- Does not own manufacturing, publication, legal approval, public hosting (m3t4), or claims about real institutions.

## Scope

- Applies to Mandate 2038 mechanics, copy, projections, simulation, physical specification, and release evidence.

## Contracts

- Input: Complete records in `components/`, `world.md`, `rules.md`, `ui.json`, the build declarations in `content/graph.json`, and the [balance contract](lab/contracts/balance-contract.json).
- Output: Generated runtime, rules, site, physical-kit artifacts, and versioned evidence.

## Invariants

- One ruleset; no retired module or rules profile is selectable. The 2026-10-12 movement and setup-objective selection needs fresh balance and human-play evidence.
- `rules.md`, `components/`, and `world.md` keep single authored homes; generated graph targets are never hand-edited.
- Fictional identities remain fictional, simulated sessions remain labeled, and old releases remain immutable.
- Canonical rule changes update every affected authority and evidence surface together.
- [Retained details](GOVERNANCE_DETAILS.md) keep every detailed and dated boundary from the prior charter.

## Acceptance

- Content, runtime, deterministic simulation, balance, and generated projections pass the package checks.
- Evidence: [package scripts](package.json), [content boundary checks](tasks/content/check-boundaries.mjs), and [project instructions](AGENTS.md).

## Non-goals

- Authorizing retail publication or treating exploratory player counts as promoted balance evidence.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
