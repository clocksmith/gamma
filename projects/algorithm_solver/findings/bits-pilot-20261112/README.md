# BITS pilot: TypedPredictor vs retrieval vs bounded search (2026-11-12)

Owner-authorized single run (contract in [contract.json](contract.json)) of
`algsolve/synth/bits_pilot.py` at `2acbb6f57` on Jupiter (host 128, CPU, torch
2.12.1+rocm7.2). Training on the 61 qualified development_fit targets of
[the step 1 manifest](../bits-step1-20261112/TARGET-MANIFEST.md) with the
pilot's frozen configuration: 400 full-batch AdamW steps, seed 17, width 64, two
layers, lr 0.001, minimum loss over qualified alternatives, retrieval memory
from the 61 fit target graphs only. Held-out payloads were not used in
training, teacher generation, retrieval or tuning; their public inputs were
read to decide, and independent tests only after the decisions were sealed.
Decision budget 2 s. Final training loss 1.47 at step 400 (24.7 at step 1;
[metrics.jsonl](metrics.jsonl)).

## Results ([summary.json](summary.json))

Accepted correct (wrong acceptances) per split and route:

| Split (problems) | raw | constrained (first pass) | repaired | nearest training graph | bounded base-v2 search |
|---|---|---|---|---|---|
| development_fit (145) | 0 (0) | 0 (0) | 0 (0) | 42 (1) | 0 (10); 72 unsupported |
| heldout_combination (11) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0); 6 unsupported |
| heldout_family (76) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 1 (4); 34 unsupported |

Learning does not beat retrieval or bounded search in this run.

## Observed reasons ([reasons.json](reasons.json))

- The predictor produced no valid program on any split, including the
  problems it was trained on. Raw decode rejections: `invalid_root_or_trailing`
  201 of 232 (an empty slot inside the predicted program, or an invalid root),
  `invalid_edge` 15, `root_shape` 9, `invalid_statement_shape` 5,
  `expected_expression` 2. With this configuration the model did not fit its
  61 training targets.
- Structural correction ended at its time bound (`correction_budget`) on 141 of
  145 fit problems. Query embedding on CPU takes a median 0.95 s of the 2 s
  decision budget; prediction 0.006 s.
- Nearest-training-graph's 42 fit answers are training problems retrieving
  their own qualified graph (lookup, not transfer); it solved no held-out
  problem.
- Bounded search's wrong acceptances (10 fit, 4 held-out family) fit every
  public example and fail independent tests.

## What this does and does not establish

One seed and one fixed configuration; nothing was tuned on these results.
It shows the frozen 400-step configuration does not learn valid program
structure from 61 targets, under a decision budget that CPU embedding halves.
It does not show that the TypedPredictor cannot learn this corpus under another
configuration, budget or device; any change is a new, separately authorized
run. Retained on Jupiter (problem test data): decisions.json `3efeda61…`,
scores.json `c3aeb9ca…`, model.pt `ae6a3304…`.
