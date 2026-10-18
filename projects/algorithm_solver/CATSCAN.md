# CATSCAN: Algorithm Solver

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Recognize stored solutions; separately learn non-autoregressive composition of
typed functions, data-structure operations, explicit state and control flow.
Reusable recipes expand into those building blocks; a compact neural predictor
selects and connects them, with deterministic assembly and validation. Compare
against search and autoregressive generation. The recorded three-call baseline
does not constrain the composition goal.

## Authority

Owns problem imports, sandbox judging, comparison routes, research answer interfaces, index-only mining, graph datasets, frozen samples and reports. Also owns the user-requested binary-input vocabulary study on permitted reference text; 256one owns its editor UI and runtime packaging. No unsupported generalization or benchmark-acceptance claims.

## Scope

`algsolve/`, `contracts/`, `findings/`, `runs/`.

## Contracts

- Input: [run contract](contracts/run_contract.json), [sample manifest](contracts/sample_manifest.json).
- Output: per-item evidence and rebuilt reports.

## Invariants

- Expected outputs never enter the sandbox; verdicts fail closed.
- Held-out problems/aliases stay outside research retrieval, mining and training. The separate all-corpus service index supplies known-problem retrieval only.
- Answers require query-public-example verification; stored validation is not query correctness. Missing sandbox/examples fails closed.
- Graph proposals cannot bypass vocabulary, binding, resource or execution checks. Report first-prediction correctness/complete latency separately from retries/search.
- Recipes are inspectable expansions, not the primitive vocabulary. Keep bounded-baseline results distinct from finer-grained experiments; learned unfamiliar-composition success requires protected generalization evidence.
- Binary-input studies keep raw references ignored, record pinned sources and measure encoding cost separately from solving correctness and human effort. Public challenge navigation exports metadata only, never hidden tests or solutions.
- Training excludes protected families; shared structural patterns and alternative solutions stay together. Tests do not prove correctness.
- Reserve fresh confirmation families before vocabulary mining. Structural recurrence does not verify components.
- Generative comparisons share model/budget/repair allowance; repairs see public examples only.
- Separate example-passed, independent-tests-passed and benchmark-judge-accepted evidence.

## Acceptance

[Judge](../../tests/test_algorithm_solver_judge.py) and [lane](../../tests/test_algorithm_solver_lane.py) tests pass before runs.

## Non-goals

Unbounded training, automatic downloads, production editor hosting, automatic insertion, assessment use.

## Freedom

Any implementation preserving these boundaries and acceptance evidence.
