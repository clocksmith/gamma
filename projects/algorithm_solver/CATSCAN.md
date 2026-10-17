# CATSCAN: Algorithm Solver

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Build and measure example-gated retrieval of stored algorithm solutions. Separately investigate deterministic component composition and compare both against model generation under frozen evidence contracts.

## Authority

- Owns imported problem records, the sandboxed judge, the four comparison routes, the editor-facing answer interface, index-only mining, frozen samples, and comparison reports.
- Does not claim unseen-problem generalization, benchmark-judge acceptance, or results beyond the contract's model and backend.

## Scope

- Applies to `algsolve/`, `contracts/`, committed `findings/`, and run outputs under `runs/`.

## Contracts

- Input: [Run contract](contracts/run_contract.json) and the committed [sample manifest](contracts/sample_manifest.json).
- Output: Per-item results and a report rebuilt from them.

## Invariants

- Expected outputs never enter the sandbox; verdicts fail closed.
- Held-out solving problems and aliases stay out of research lookup, retrieval, mining and training. The existing separate all-corpus service index is only for known-problem retrieval; it cannot supply research comparisons or vocabulary mining.
- Editor answers require query-public-example verification; stored-reference validation is not query correctness. Missing sandbox or examples fails closed.
- Expanded vocabulary candidates reserve fresh confirmation families before mining. Structural recurrence alone is not a tested component.
- Generative routes share one model, budget, and repair allowance; repairs see public examples only.
- Evidence levels stay separate: example-passed, independent-tests-passed, benchmark-judge-accepted.

## Acceptance

- [Judge tests](../../tests/test_algorithm_solver_judge.py) and [lane tests](../../tests/test_algorithm_solver_lane.py) pass before any run.

## Non-goals

- Training, production editor hosting, automatic insertion, or use during assessments. The user authorized preparing a future editor mode; this lane owns its research interface, not a production web application.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
