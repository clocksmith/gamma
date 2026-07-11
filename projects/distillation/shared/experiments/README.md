# Experiment Register

This directory is Gamma's pointer-only register for verifier-guided learning
experiments across Gamma, Doppler, and Columbo.

- `experiment-register.schema.json` defines the record contract.
- `experiment-register.jsonl` contains one JSON object per experiment.
- `validate_experiment_register.py` validates identifiers, enums, claim
  boundaries, paths, revisions, digests, duplicate IDs, and available artifact
  bytes.

Do not copy domain result bundles here. Point to one primary immutable evidence
artifact and any related artifacts needed to support the claim boundary in
their owning repository. State exactly what the evidence does and does not
prove.

Run:

```bash
python projects/distillation/shared/experiments/validate_experiment_register.py
```

See [`docs/VERIFIER_GUIDED_LEARNING.md`](../../../../docs/VERIFIER_GUIDED_LEARNING.md)
for the method taxonomy and evidence states.
