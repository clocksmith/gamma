# Experiment Register

This directory is Gamma's pointer-only register for verifier-guided learning
experiments across domain repositories. Simulatte visual-construction trials use
the `simulation_rendering` domain and `construction_search` method ID.

- `experiment-register.schema.json` defines the record contract.
- `experiment-register.jsonl` contains one JSON object per experiment.
- `validate_experiment_register.py` validates identifiers, enums, claim
  boundaries, paths, revisions, digests, duplicate IDs, and available artifact
  bytes.

For an available Git repository, validation reads each artifact from its pinned
`revision:path`; later worktree edits cannot change the evidence verdict.

Do not copy domain result bundles here. Point to one primary immutable evidence
artifact and any related artifacts needed to support the claim boundary in
their owning repository. State exactly what the evidence does and does not
prove.

Run:

```bash
python projects/distillation/shared/experiments/validate_experiment_register.py
```

See [`SAME-R`](../../../samer/README.md) for swappable approaches, matched
evaluation, detailed trial stages, and their mapping to the register's coarse
statuses. See
[`docs/VERIFIER_GUIDED_LEARNING.md`](../../../../docs/VERIFIER_GUIDED_LEARNING.md)
for optimizer, reward, and RLVR terminology.
