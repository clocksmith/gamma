# B2 v4 development: can the proposer beat the optimizer it contains?

Development only. Seeds are disjoint from every v3 seed, nothing is pre-registered, and no v3
file or receipt was changed. The pooled-embedding "Qwen" family from v3 is left out.

## Why this exists

A code read of the sealed v3 study found the proposer could not have won as built:

- It starts as K-FAC at a worse setting (step about 0.036, weight decay about 0.0008) than the
  tuned baseline (0.075 and 0.025), with decay capped at 0.03.
- It gets 20 small meta-steps in total.
- Its self-update runs with gradients off, so nothing trains it to modify itself well.
- Its regulariser is a no-op: the anchor is a copy of the current weights.

Here the proposer is rebuilt as an adjustment on top of the tuned K-FAC settings (generation 0
reproduces `kfac_no_proposer` to 5.7e-10; `test_identity_v4dev.py`), the decay cap is lifted, the
regulariser is deleted, and it is trained with Adam for 250 meta-steps with no accept/reject filter.

## Stage 1: proposer against K-FAC

8 lineages, 36 held-out tasks each. Lineage-mean normalised loss ratio, lower is better.

| Proposer (0.4111) against | Reference | Wins / losses | Paired t p |
|---|---:|---:|---:|
| Sealed-grid `kfac_no_proposer` | 0.4803 | 8 / 0 | 7.8e-8 |
| Eight trained constants, same budget | 0.4127 | 4 / 4 | 0.56 |
| Proposer outputs replaced by their mean | 0.4107 | 4 / 4 | 0.86 |
| Proposer outputs averaged within each layer | 0.4114 | 5 / 3 | 0.71 |

The win over the sealed baseline is real but is not the proposer's doing: the sealed grid stopped
at a weight decay of 0.025 and the best value is about four times higher. Plain constants trained
on the same budget tie the proposer, and replacing its per-row outputs by one constant costs
nothing. It learned better constants and no state-dependent behaviour.

## Stage 2: is there anything state-dependent to learn?

Same 8 lineages, 18 held-out tasks each, a 40-point K-FAC menu, scored on a held-out half of
each query set.

| Comparison | Loss ratio | Wins / losses | p |
|---|---|---:|---:|
| Tuned per task against one global setting | 0.3883 against 0.4153 | 8 / 0 | 0.002 |
| Tuned per task family against global | 0.3909 against 0.4153 | 8 / 0 | 0.002 |
| Per task against per family | difference 0.003 | 6 / 2 | 0.19 |

There is headroom, almost all of it at the level of the task family. Per-task selection used
query labels, so it is an upper bound. Accuracy does not move.

## Stage 3: self-modification

Not run. The gate was that the proposer first beat tuned K-FAC, and it only ties.

## Read

- The v3 loss to K-FAC was a tuning artefact on both sides.
- A learned per-row proposer adds nothing here over eight constants.
- The one opening is conditioning on the task family, which a proposer trained on other families
  cannot do. Training within the family is the next test.
- There is still no evidence for or against recursive self-improvement, and no reason yet to
  expect it in a test bed where constants are all there is to learn.

## Close-out (2026-11-19)

**Status: closed on 2026-11-19 on the owner's approval** (relayed to the B owner by the X1 session; no new
experiment was run to close it). Self-modification stays marked untested in this rebuild, and the
uncorrected secondary comparisons below stay as recorded.

Closing result for B2, written by the B owner. `analyze_v4dev.py` was re-run on a CPU host
from the retained Stage 1 and Stage 2 outputs and reproduced `summary_v4dev.json` byte for byte.

What the evidence supports:

- **Training the rule helps against a weak baseline.** Sealed v3: the proposer improved over its own
  generation 0 in 12 of 12 lineages (p 2.6e-6). Here it beat the sealed-grid K-FAC in 8 of 8.
- **That gain is tuning, not the proposer.** Eight constants trained on the same budget tie it on
  normalised loss (0.4111 against 0.4127, 4 / 4, p 0.56), and replacing its per-row outputs with their
  mean leaves the loss unchanged (p 0.86).
- **"No state-dependent behaviour" above is slightly too strong.** The per-row outputs trade one task
  type for another. Against their own mean they give better regression R² (0.7876 against 0.7756, 8 / 0,
  p 0.034) and worse classification accuracy (0.4444 against 0.4487, 2 / 6, p 0.027). Against the trained
  constants: R² 7 / 1 (p 0.018) for the proposer, accuracy 2 / 6 (p 0.14) for the constants. These are
  two of about twenty comparisons in the analysis, uncorrected, and they point in opposite directions:
  no net task benefit.
- **Self-modification has not shown a benefit, and here was not tested.** Sealed v3 found no detectable
  benefit from recursive self-application (p 0.66), on a test bed whose "real model" family runs one MLP
  layer on pooled embeddings, not the model (see the v3 post-seal note). In v2's five lineages the
  self-modifying proposer had lower loss than the fixed one in 4 of 5 (mean difference -0.0019,
  p 0.63). Stage 3 here was gated on the proposer first beating trained constants, and it did not run.

So the closing statement is: learning an update rule beat a badly tuned optimizer; it did not beat
trained constants; and no experiment has shown that letting the rule modify itself adds anything. This
is the absence of a demonstrated advantage, not proof that self-modification cannot help.

**Reopen only if** one development test, within a single task family (the only place Stage 2 found
headroom, 0.3909 against 0.4153 on loss, with accuracy unchanged), shows a differentiable self-modifying
arm beating eight trained constants, a matched non-recursive rule and the mean-output ablation on
**accuracy**, with all meta-training, reconstruction and inner updates charged to the same measured
compute. Otherwise B2 stays closed.

## Rerun

```
.venv/bin/python -m unittest projects/self_transform/self_transform_neural_proposer_v4_dev/test_identity_v4dev.py -v
.venv/bin/python projects/self_transform/self_transform_neural_proposer_v4_dev/run_dev_v4.py stage1
.venv/bin/python projects/self_transform/self_transform_neural_proposer_v4_dev/run_dev_v4.py stage2
.venv/bin/python projects/self_transform/self_transform_neural_proposer_v4_dev/analyze_v4dev.py
```

Outputs are in `.work/self-transform-neural-proposer-v4-dev/`. Limits: 250 meta-steps, 8
lineages, hyper-parameters chosen on one pilot lineage, and the Stage 2 menu was defined after
reading Stage 1.
