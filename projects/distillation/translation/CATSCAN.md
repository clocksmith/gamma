# CATSCAN: Translation distillation

Parent: [Distillation research](../CATSCAN.md)

## Target

Produce and evaluate translation students against frozen in-domain and external populations with explicit human-review promotion.

## Authority

- Owns translation datasets, run contracts, checkpoint evaluations, scoreboards, candidate selection, and promotion contracts.
- Does not own generic distillation behavior or silently change evaluation populations.

## Scope

- Applies to translation datasets, run contracts, checkpoint evaluations, scoreboards, selection, and promotion.

## Contracts

- Input: Training/evaluation pairs and the [promotion contract](promotion/promotion-contract.v1.json).
- Output: Run manifests, comparison rows, scoreboards, review records, and promotion decisions.

## Invariants

- Population, decode mode, checkpoint, and baseline identity remain explicit.
- External and in-domain results remain separate.
- Human review cannot be inferred from automatic metrics.

## Acceptance

- Promotion predicates validate and reports rebuild from raw manifest-backed rows.
- Evidence: [promotion tests](../../../tests/test_translation_promotion_contract.py), [reporting tests](../../../tests/test_translation_reporting.py), and [human-review tests](../../../tests/test_translation_human_review.py).

## Non-goals

- Presenting a selected checkpoint as generally superior outside its measured populations.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
