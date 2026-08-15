# CATSCAN: Gamma tools

Parent: [Gamma](../CATSCAN.md)

## Target

Provide reproducible developer, analysis, migration, validation, and benchmark-support utilities without becoming hidden product behavior.

## Authority

- Owns repository utilities and generated-artifact maintenance under `tools/`.
- Does not own runtime semantics or silently grant research promotion.

## Scope

- Applies to repository utilities and generated-artifact maintenance under `tools/`.

## Contracts

- Input: Explicit files, configuration, and commands from [tooling documentation](README.md).
- Output: Deterministic transformations, validations, reports, and actionable errors.

## Invariants

- Destructive or state-changing operations require explicit targets.
- Generated outputs identify their source authority.
- Tool success cannot substitute for missing runtime or scientific evidence.

## Acceptance

- Repository validators fail on drift and environment diagnostics report actual capability.
- Evidence: [GPU setup probe](test_gpu_setup.py), [repository layout tests](../tests/test_repository_layout.py), and [CI](../.github/workflows/ci.yml).

## Non-goals

- Creating undocumented alternate workflows around canonical project tools.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
