# Step 3: memorization ladder on the fit targets (owner-approved)

[memorize.py](memorize.py) on Jupiter (CPU, 4 threads), frozen settings in
[memorize/frozen.json](memorize/frozen.json) committed before training
(`1c7f35512`): pilot model, codec (320 slots), loss, AdamW 0.001, seed 17,
embeddings and retrieval unchanged; S1 = lcd:1732 (fewest active slots), S8 =
first 8 by SHA-256 of UID, S61 = all 61 qualified targets; evaluation at 400,
1000, 2000 and 4000 steps on each subset's own targets, all reported.

| Subset | Step | Loss | op active | Valid | Exact reconstruction | Public correct | Independent correct | Interior EMPTY | Train s |
|---|---|---|---|---|---|---|---|---|---|
| S1 | 400 | 0.038 | 100% | 1/1 | 1 | 1 | 1 | 0 | 1.9 |
| S1 | 4000 | 0.0004 | 100% | 1/1 | 1 | 1 | 1 | 0 | 18.1 |
| S8 | 400 | 0.134 | 99.7% | 6/8 | 1 | 2 | 1 | 0 | 8.7 |
| S8 | 1000 | 0.018 | 100% | 8/8 | 8 | 8 | 8 | 0 | 22.6 |
| S8 | 4000 | 0.001 | 100% | 8/8 | 8 | 8 | 8 | 0 | 91.1 |
| S61 | 400 | 1.470 | 47.4% | 0/61 | 0 | 0 | 0 | 42 | 69.4 |
| S61 | 1000 | 0.215 | 88.8% | 0/61 | 0 | 0 | 0 | 3 | 178.0 |
| S61 | 2000 | 0.021 | 100% | 61/61 | 34 | 39 | 37 | 0 | 352.8 |
| S61 | 4000 | 0.003 | 100% | 61/61 | **61** | **61** | **61** | 0 | 709.0 |

Per-checkpoint details per problem: [memorize/S1.json](memorize/S1.json),
[S8.json](memorize/S8.json), [S61.json](memorize/S61.json).

## Reading

- S61 at step 400 reproduces the pilot exactly (loss 1.4696, op active 47.4%,
  42 interior EMPTY), so the run is deterministic and the pilot's failure is the
  same model at the same point.
- Under the decision rule frozen in advance: S1 succeeds (implementation and
  representation work), S8 succeeds, and S61 succeeds once trained longer. The
  pilot's zero-validity result is a training-duration effect at the frozen 400
  steps, not a capacity limit: with model, codec, loss and optimizer unchanged
  the predictor reconstructs all 61 targets exactly by step 4000 (about 12 CPU
  minutes). Step 4 (a structural decoder) is not indicated by this evidence.
- At step 2000 every S61 graph is valid but only 34 reconstruct exactly; 37 are
  nonetheless independently correct, so some non-identical graphs are correct.

## Limits

Memorization of the training targets only; not evidence of generalization. The
held-out results of the original pilot are exposed and must not be reused for
tuning or presented as fresh confirmation; a later held-out evaluation needs a
new, untouched final set and a separately authorized run.
