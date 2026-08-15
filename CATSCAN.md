# CATSCAN: Gamma

Parent: none

## Target

Provide one trustworthy workbench for inspecting, comparing, measuring, and improving model or algorithm behavior under explicit evidence contracts.

## Authority

- Owns repository-wide product boundaries, shared evidence discipline, and component precedence.
- Does not own lane-specific algorithms, datasets, or promotion thresholds.

## Scope

- Applies to repository-wide product boundaries, shared evidence discipline, and component precedence.

## Contracts

- Input: Mission and durable strategy from [GOALS.md](GOALS.md) and public navigation from [README.md](README.md).
- Output: The [`gamma.py`](gamma.py) CLI, reusable packages, research lanes, and auditable evidence.

## Invariants

- Results remain bound to exact inputs, runtime, metric, and replay evidence.
- Missing or conflicting promotion evidence fails closed.
- Research evidence is not silently promoted into a general product claim.

## Acceptance

- CLI and documentation remain aligned and core routing remains explicit.
- Evidence: [CLI parity test](tests/test_docs_cli_parity.py), [router test](tests/test_command_router.py), and [CI](.github/workflows/ci.yml).

## Non-goals

- Declaring every experiment a supported product surface.
- Hiding component-specific policy in repository-wide prose.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
