# CATSCAN: Model engines

Parent: [Gamma Python runtime](../CATSCAN.md)

## Target

Present compatible, capability-explicit model execution across supported local and remote engine backends.

## Authority

- Owns engine interfaces, backend selection, capability reporting, and backend-specific execution.
- Does not own game rules, benchmark claims, or model provisioning.

## Scope

- Applies to engine interfaces, backend selection, capability reporting, and backend execution under this directory.

## Contracts

- Input: Model, device, decoding, and backend settings described in [engine documentation](README.md).
- Output: Normalized generation, token, probability, timing, and capability results.

## Invariants

- Backends never fabricate unsupported logits, tokenization, streaming, or timing.
- Selection and fallback are observable and preserve requested semantics.
- Model weights are never installed implicitly.

## Acceptance

- Every backend satisfies the shared interface and sampling contracts it claims.
- Evidence: [engine interface test](../../tests/test_engine_interface.py), [factory test](../../tests/test_engine_factory.py), and [sampling tests](../../tests/engines/test_sampling_utils_phase1.py).

## Non-goals

- Guaranteeing identical numerical output across inherently different model implementations.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
