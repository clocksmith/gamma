# CATSCAN: Distillation research

Parent: [Gamma research projects](../CATSCAN.md)

## Target

Measure capability transfer from teacher to student models under frozen task, data, checkpoint, and evaluation contracts.

## Authority

- Owns shared distillation run provenance, checkpoint identity, and transfer-study boundaries.
- Does not own task-specific promotion rules or engine installation.

## Scope

- Applies to shared distillation run provenance, checkpoint identity, and transfer-study boundaries.

## Contracts

- Input: Explicit teacher, student, dataset, schedule, runtime, resume, decode, and evaluation identities.
- Output: Checkpoints, raw metrics, evaluation rows, manifests, and normalized reporting bundles.

## Invariants

- Available examples remain distinct from examples actually used.
- Training, checkpoint evaluation, and report rebuilding remain separable workflows.
- Environment or resume drift blocks the run rather than changing it silently.

## Acceptance

- Training and evaluation artifacts retain enough provenance to rebuild reports.
- Evidence: [training tests](../../tests/test_translate_distill_training.py), [evaluation tests](../../tests/test_translate_distill_eval.py), and [WGSL protocol tests](../../tests/test_wgsl_training_protocol.py).

## Non-goals

- Inferring general capability transfer from one task or teacher-student pair.

## Freedom

Any mechanism is permitted if it preserves these boundaries and passes the acceptance evidence.
