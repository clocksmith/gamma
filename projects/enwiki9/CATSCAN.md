# CATSCAN: Gamma enwiki9

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Preserve the archived research and its evidence after the user's 2026-10-08
retirement decision. The unachieved historical target remains a Gamma-authored
codec reconstructing enwik9 exactly at or below 96,000,000 counted bytes with
bound resource evidence. Preserve all 105M/99M/90M/96M contracts.

## Authority

Owns compression research, candidate lineage, measurement and proof. The lab is the operational entrance; `src/gamma_enwiki9/` owns maintained services. Execution, evidence, lifecycle, packaging and reporting have separate authority. `lib/coders/` owns pure codec semantics. Ledger/workbench remain projections, never queues or launch authority. Live prize rules belong to their publishers.

## Scope

Candidates, source closures, experiments, execution, evidence and delivery.

## Contracts

- Input: [Objective](contracts/research/v4/objective-contract.json), frozen hypotheses and exact dependencies.
- Output: Packages, receipts, reflections and independently replayable evidence.

## Invariants

- [Project status](operations/runtime/project_status.json) withdraws research and
  execution authority while archived. The lab rejects research, queue release and
  execution before side effects; inspection and archive maintenance remain available.
- Reopening requires explicit user authorization; historical handoffs and contracts
  cannot restart the project. Retirement earns no score credit or impossibility claim.
- Missing inversion, determinism, dependencies, resource or accounting evidence fails closed.
- Measured candidates and bound hashes remain immutable; semantic mutations receive new identities.
- Component gains require joint replay; forecasts are not additive score credit.
- Admission locks runtime before queue; qualification reserves the queue before obtaining a lease. Cleanup removes only owned files, lease before lock.
- Historical verification uses original immutable bytes; validity, compatibility and launch authority remain separate.
- New candidates declare kinds/entrypoints; interrupted creation reconciles idempotently before use.
- Projection is deterministic; host observations are explicit and timestamped.

## Acceptance

[Contract validator](tools/research_contracts.py), [architecture groups](tests/run_architecture_groups.py), and [accounting](docs/official_accounting_checklist.md). Only exact full-1G package evidence earns objective credit.

## Non-goals

Shipping LibNC, hidden teacher state, uncounted dependencies, or forecasts as solutions.

## Freedom

Any mechanism preserving these evidence boundaries.
