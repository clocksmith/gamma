# CATSCAN: Gamma Python runtime

Parent: [Gamma](../CATSCAN.md)

## Target

Execute Gamma's supported interactive, comparison, benchmark, and coordination commands through explicit Python interfaces.

## Authority

- Owns runtime orchestration and shared Python behavior under `src/`.
- Does not own research-lane policy or standalone package contracts.

## Scope

- Applies to runtime orchestration and shared Python behavior under `src/`.

## Contracts

- Input: CLI requests routed by [`gamma.py`](../gamma.py) and repository configuration.
- Output: Typed runtime behavior, errors, events, and command results.

## Invariants

- Unsupported behavior remains explicit; no hidden engine or command fallback.
- Component outputs preserve the caller's named model, workload, and settings.
- Engine, game, benchmark, comparison, and Mind Meld responsibilities remain separable.

## Acceptance

- Commands route to the declared surface and runtime configuration remains valid.
- Evidence: [router test](../tests/test_command_router.py) and [core configuration test](../tests/test_core_config.py).

## Non-goals

- Owning domain experiment conclusions or generated research evidence.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
