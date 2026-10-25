# CATSCAN: Algorithm Solver

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Develop qualified recognition, reusable languages, human composition, autonomous assembly and research evidence under versioned goals.

## Authority

Owns research imports, isolated judging, comparisons, indexes, corpora and reports.
The human user retains recognition ownership; 256one owns production editor
hosting. Existing admission and promotion authority is unchanged.

## Scope

`algsolve/`, `contracts/`, `findings/`, `runs/`, `literals/`, `catalogue/`.

## Contracts

- Input: [versioned goals](contracts/algorithm_solver_goals_v2.json), [run contract](contracts/run_contract.json), [sample](contracts/sample_manifest.json), [composition comparison](contracts/typed_composer_comparison_v1.json).
- Output: source-bound qualification receipts, cost measurements and rebuilt reports.

## Invariants

Inherit the authority, contracts, invariants and acceptance boundaries
in [the preserved charter](HISTORY-CATSCAN-v1.md); its numbered goals are historical
v1 aliases, not current taxonomy. The v2 alias map reorganizes goals without
changing those boundaries, evidence or [M1–M6 gates](literals/MILESTONES.md).

Expected outputs stay outside the sandbox. Protected families/aliases stay closed;
answers and verdicts fail closed. Recognition, representation, human performance
and autonomous correctness qualify separately. Algorithms satisfy pinned
behavior/effect/complexity contracts; exact decoding reconstructs selected
bytes. Charge helpers, operands, controls and decoder costs. Retain rejected
attempts. Organization grants no execution or publication authority.

The owner-approved [prospective catalogue roadmap](catalogue/ROADMAP-v1.md)
prioritizes complete dual-language foundation and recognition 1a/1b/1c, and adds
16/32-entry exploratory literal profiles. This deliberately changes future work
priority, not historical gates, verdicts or protected-data authority. Catalogue
validation checks metadata and external receipt bindings; it does not grant judge
qualification or prove recognition.

## Acceptance

[Judge](../../tests/test_algorithm_solver_judge.py) and
[lane](../../tests/test_algorithm_solver_lane.py) checks pass before runs;
[charter validation](../../tools/catscan.py) checks documentation changes.
Preserve source, decode, human and autonomous evidence classes.

## Non-goals

Unbounded training/downloads, production editor hosting, automatic insertion,
assessment use or hidden answer lookup presented as composition.

## Freedom

Any implementation preserving these boundaries and qualification gates.
