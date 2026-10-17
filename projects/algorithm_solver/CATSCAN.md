# CATSCAN: Algorithm Solver

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Measure whether lookup, retrieval, or pattern classification with templates makes a small local model faster or more reliable than the same model alone.

## Authority

- Owns imported problem records, the sandboxed judge, the four routes, frozen samples, and comparison reports.
- Does not claim unseen-problem generalization, benchmark-judge acceptance, or results beyond the contract's model and backend.

## Scope

- Applies to `algsolve/`, `contracts/`, and run outputs under `runs/`.

## Contracts

- Input: [Run contract](contracts/run_contract.json) and the committed [sample manifest](contracts/sample_manifest.json).
- Output: Per-item results and a report rebuilt from them.

## Invariants

- Expected outputs never enter the sandbox; verdicts fail closed.
- Solving problems and their aliases stay out of lookup, retrieval, and classifier training.
- Generative routes share one model, budget, and repair allowance; repairs see public examples only.
- Evidence levels stay separate: example-passed, independent-tests-passed, benchmark-judge-accepted.

## Acceptance

- [Judge tests](../../tests/test_algorithm_solver_judge.py) and [lane tests](../../tests/test_algorithm_solver_lane.py) pass before any run.

## Non-goals

- Training, live-page integration, or use during assessments without explicit permission.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
