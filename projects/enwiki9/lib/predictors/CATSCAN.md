# CATSCAN: Pure enwiki9 predictors

Parent: [enwiki9](../../CATSCAN.md)

## Target

Expose bounded, causal prediction state for codecs and training adapters.

## Authority

Owns predictive state and explicit observation interfaces. Execution, source
resolution, lifecycle decisions and artifact publication belong to callers.

## Scope

Maintained predictor and decoder-built memory components.

## Invariants

- Inputs are explicit configuration, authenticated assets and decoded history.
- State capable of affecting predictions has declared initialization and bounds.
- A partial source emission cannot publish a complete metadata item.
- Controls share opportunities and capacity; zero contribution preserves the parent.
- Synthetic fixtures prove implementation behavior, not corpus gains.

## Acceptance

[Title-memory fixtures](../../tests/test_fx2_title_memory_v1.py) check causality,
bounded retention, controls and deterministic state without a corpus run.
Relational binding fixtures additionally compare fixed-point posterior updates
with an exact reference, persistent versus independent arguments, distinct donor
controls, and completed-emission coordinates. One coding sequence is retained;
predictors neither select experiments nor publish results.

## Non-goals

Queue ownership, host discovery, experiment launch, packaging or scientific verdicts.
