# CATSCAN: Gamma skills

Parent: [Gamma](../CATSCAN.md)

## Target

Encode discoverable agent workflows that faithfully operate Gamma's existing authorities and evidence contracts.

## Authority

- Owns reusable agent workflow instructions under `skills/`.
- Does not redefine product, project, benchmark, or promotion authority.

## Scope

- Applies to reusable agent workflow instructions under `skills/`.

## Contracts

- Input: Canonical component charters, project instructions, and [skill index](README.md).
- Output: Bounded workflows that direct agents to the correct commands, contracts, and evidence.

## Invariants

- A skill never overrides an applicable CATSCAN or AGENTS instruction.
- Workflow guidance distinguishes diagnostics from promoted evidence.
- Missing prerequisites cause an explicit stop or fallback.
- Every skill declares objective validation and explicit stop conditions.
- Open-ended development, research prioritization, model choice without supplied
  criteria, and writing style remain outside skill authority.

## Acceptance

- Every maintained skill points to existing authority and uses supported entry points.
- Evidence: [skill index](README.md) and [repository layout tests](../tests/test_repository_layout.py).

## Non-goals

- Duplicating component goals or embedding mutable status inside skill prose.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
