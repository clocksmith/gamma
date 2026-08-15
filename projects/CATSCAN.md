# CATSCAN: Gamma research projects

Parent: [Gamma](../CATSCAN.md)

## Target

Host bounded research lanes whose objectives, evidence, and promotion rules remain distinct from Gamma's supported runtime.

## Authority

- Owns separation and navigation of domain research under `projects/`.
- Does not grant product support or combine evidence across unrelated lanes.

## Scope

- Applies to domain research candidates, contracts, receipts, reports, and conclusions under `projects/`.

## Contracts

- Input: Repository evidence discipline from the [Gamma charter](../CATSCAN.md) plus each lane's declared objective.
- Output: Lane-specific candidates, contracts, receipts, reports, and maintained conclusions.

## Invariants

- Every lane names its target and source of measurement truth.
- Forecasts, diagnostics, and external artifacts retain their epistemic class.
- Cross-lane reuse preserves original authorship, licensing, and evidence boundaries.

## Acceptance

- Controlled experiments retain matched evaluation and registered evidence.
- Evidence: [SAME-R contract tests](../tests/test_samer_contracts.py) and [experiment-register tests](../tests/test_experiment_register.py).

## Non-goals

- Treating the existence of a project directory as a public product commitment.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
