# CATSCAN: Gamma enwiki9

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Produce a Gamma-authored, self-contained codec that exactly reconstructs canonical enwik9 with a fully counted score at or below 105,000,000 bytes and satisfies the bound prize-resource rules.

## Authority

- Owns the enwiki9 objective, adaptive research state, candidate lineage, measurement contracts, and proof frontier.
- Does not own live Hutter Prize rules or grant score credit to teachers, forecasts, traces, or external compressors.

## Scope

- Applies to the enwiki9 objective, adaptive state, candidate lineage, measurement contracts, and proof frontier.

## Contracts

- Input: Canonical [objective contract](contracts/research/v1/objective-contract.json) and immutable, hash-bound experiment evidence.
- Output: Candidate packages, exact receipts, reflections, ledgers, and ultimately one independently replayable full-corpus proof.

## Invariants

- Missing roundtrip, determinism, dependency, resource, or accounting evidence fails closed.
- Measured candidates are immutable; every semantic edit creates a new identity.
- Component gains require a new joint replay and are never added as forecasts.

## Acceptance

- The objective validates, all gate antecedents resolve, and only exact full-1G package evidence receives objective credit.
- Evidence: [contract validator](tools/research_contracts.py), [accounting checklist](docs/official_accounting_checklist.md), and [upper-bound certificate](UPPER_BOUND_CERTIFICATE.md).

## Non-goals

- Shipping LibNC, hidden teacher state, uncounted dependencies, or a forecast as the solution.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
