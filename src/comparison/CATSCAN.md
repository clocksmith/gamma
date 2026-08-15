# CATSCAN: Model comparison

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Compare model outputs and decoding behavior while preserving each arm's identity and shared evaluation conditions.

## Authority

- Owns comparison plans, alignment, paired output presentation, and comparison-specific aggregation.
- Does not own inference backend truth or benchmark timing claims.

## Scope

- Applies to comparison plans, alignment, paired presentation, and comparison aggregation.

## Contracts

- Input: Normalized engine outputs and settings from [comparison documentation](README.md).
- Output: Paired or multi-arm comparison records with visible provenance.

## Invariants

- Arms remain attributable to their selected models and settings.
- Missing output or capability is not silently imputed.
- Aggregation never erases material per-arm disagreement.

## Acceptance

- Blending, strategy, and compatibility behavior remains explicit and reproducible.
- Evidence: [blending tests](../../tests/test_blending.py), [strategy tests](../../tests/test_strategies.py), and [compatibility tests](../../tests/test_compatibility.py).

## Non-goals

- Declaring broad model superiority from an unmatched prompt sample.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
