# CATSCAN: Gamma core package

Parent: [Gamma](../CATSCAN.md)

## Target

Provide a small installable Python core for reusable Gamma primitives without importing repository research state.

## Authority

- Owns the `gamma-core` package API, packaging metadata, and core implementation.
- Does not own the repository CLI, research projects, or engine integrations.

## Scope

- Applies to the `gamma-core` package API, packaging metadata, and core implementation.

## Contracts

- Input: Stable package configuration in [`pyproject.toml`](pyproject.toml).
- Output: An importable, versioned Python package documented in [README.md](README.md).

## Invariants

- Public imports do not depend on untracked repository state.
- Package dependencies and compatibility remain explicit.
- Core APIs remain narrower than repository-wide orchestration.

## Acceptance

- The package builds from its declared metadata and core configuration remains compatible.
- Evidence: [package metadata](pyproject.toml) and [core configuration tests](../tests/test_core_config.py).

## Non-goals

- Becoming a second implementation of every `src/` surface.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
