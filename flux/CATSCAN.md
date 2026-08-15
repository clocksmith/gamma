# CATSCAN: Flux package

Parent: [Gamma](../CATSCAN.md)

## Target

Provide Flux's independently installable execution surface while keeping its package and web contracts isolated from Gamma experiments.

## Authority

- Owns Flux package APIs, examples, packaging, and Flux-specific web behavior.
- Does not own Gamma CLI routing or research-lane evidence.

## Scope

- Applies to Flux package APIs, examples, packaging, and Flux-specific web behavior.

## Contracts

- Input: Package configuration in [`pyproject.toml`](pyproject.toml) and documented user inputs.
- Output: Importable Flux behavior and its documented web/example surfaces.

## Invariants

- Flux packaging remains self-describing and independently buildable.
- Gamma internals are not silently made public through Flux.
- Example behavior does not substitute for package acceptance.

## Acceptance

- Package metadata resolves and documented entry points remain consistent.
- Evidence: [package metadata](pyproject.toml), [package documentation](README.md), and [web documentation](web/README.md).

## Non-goals

- Serving as an alias for Gamma's entire runtime.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
