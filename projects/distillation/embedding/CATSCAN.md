# CATSCAN: Embedding distillation

Parent: [Distillation research](../CATSCAN.md)

## Target

Evaluate embedding capability transfer on declared subsets without conflating representation similarity with downstream quality.

## Authority

- Owns embedding-specific datasets, training/evaluation configuration, and result interpretation.
- Does not own general engine semantics or translation/WGSL promotion.

## Scope

- Applies to embedding-specific datasets, training/evaluation configuration, and result interpretation.

## Contracts

- Input: Declared populations and model/checkpoint identities from [lane documentation](README.md).
- Output: Embedding checkpoints, metrics, and population-bound comparison evidence.

## Invariants

- Dataset subsets and pooling/normalization choices remain explicit.
- Teacher similarity and downstream task performance remain distinct metrics.
- Missing or incompatible embeddings fail explicitly.

## Acceptance

- The transformer and vocabulary paths preserve declared shapes and identities.
- Evidence: [transformer pipeline tests](../../../tests/test_transformer_pipeline.py) and [vocabulary alignment tests](../../../tests/test_vocabulary_aligner.py).

## Non-goals

- Claiming universal semantic quality from one similarity score.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
