# CATSCAN: Mind Meld

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Coordinate multiple model engines through explicit routing, contribution, and state-transfer contracts.

## Authority

- Owns multi-engine sessions, routing, aggregation, latent handoff, and collaboration telemetry.
- Does not own backend inference or redefine individual model results.

## Scope

- Applies to multi-engine sessions, routing, aggregation, latent handoff, and collaboration telemetry.

## Contracts

- Input: Declared participants, routing policy, session state, and [Mind Meld configuration](README.md).
- Output: Attributed contributions, route decisions, aggregate responses, and replayable session state.

## Invariants

- Every contribution and fallback remains attributable.
- State transfer fails closed on incompatible identity or shape.
- Coordination metrics cannot substitute for task-quality evidence.

## Acceptance

- Routing and handoff behavior survives end-to-end replay and identity checks.
- Evidence: [Mind Meld end-to-end tests](../../tests/test_mind_meld_e2e.py), [engine tests](../../tests/test_mind_meld_engine.py), and [latent handoff tests](../../tests/latent_handoff/test_synthetic_e2e.py).

## Non-goals

- Claiming that more participating models necessarily improve an answer.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
