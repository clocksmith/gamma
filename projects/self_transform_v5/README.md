# Positive-step hereditary updater v5

This changes the mechanism, not just the training budget. V2-v4's unconstrained
weight/bias terms could produce uphill self-updates even with useful evidence.
V5 instead learns a bounded positive step-size along its internal scalar-probe
estimate. Original files and failed results remain unchanged.

## Rule and closure

For each coordinate, using the same four symmetric loss probes as v2:

```
g_i = mean_j [(Lplus_j - Lminus_j) direction_ji / (2 radius)]
z_i = phi_0 + phi_1 tanh(theta_i) + phi_2 tanh(g_i)
      + phi_3 log(1 + abs(g_i))
eta_i = 0.125 (1 + tanh(z_i))
T_phi(theta, experience)_i = theta_i - eta_i g_i
```

The learning rate lies in [0, 0.25]; zero estimated gradient gives exact identity.
Every coordinate displacement opposes its **estimated** gradient. Random-direction
estimates need not match true gradients, so this does not guarantee descent of the
actual objective. There is no unconditional drift from weight/bias terms.
The same function accepts target weights or its own four coefficients. Artifacts
have a distinct v5 rule identity; v2 artifacts are not silently reinterpreted.

## Frozen experiment and costs

Reuse v4's multi-generation self-target and task-only initialization procedures,
with new seeds 91000, 101000, 111000. Three training self-generations, 33 candidates
per initializer, three subsequent fresh-test generations. Each initial training
arm pays 776,160 scalar losses, 95,139 transforms and 792 meta-objective calls.
Each evaluation generation has 128 new targets, shared across arms. Every candidate
proposal and score reconstructs exact weights in a clean subprocess. No held-out
outcome changes training, search, stopping or successor selection.

Controls remain hereditary, fixed initial proposer, serialization-only and
conventional SPSA with rate 0.1. Each adaptation receives eight meta-objective
queries, 12,544 task scalar-loss calls and 1,537 transforms. An unchanged control
explicitly wastes its charged probe computation. Training, proposal and scoring
costs are separate in local receipts. External scalar-loss oracle, fixed probe
geometry and interpreter are required: no oracle-free or autonomous RSI claim.

## First development result

All 18 hereditary parent-to-child comparisons improved mean fresh-target loss
(three replicates, two distinct trained initializers, three generations). This is
more consistent than v4, but is not proof that evolving the proposer is useful.
Final-generation self-target-trained outcomes, lower is better:

| Replicate | Parent | Hereditary child | Fixed proposer child | Serialization only | SPSA 0.1 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 91000 | 0.106770362 | 0.105282910 | 0.105286469 | 0.107866176 | 0.106650776 |
| 101000 | 0.199619418 | 0.171468218 | 0.174059534 | 0.334294519 | 0.210194342 |
| 111000 | 0.101408432 | 0.099165587 | 0.098729667 | 0.322359104 | 0.146100413 |

First-generation hereditary and fixed-proposer results necessarily match. In the
six later self-target comparisons, hereditary beats fixed proposer four times,
but two of those wins are only roughly 0.0000002 and 0.0000036 absolute loss. It
loses both later comparisons in replicate 111000. That is not a robust hereditary
advantage. The task-only initializer also shows improvements, so self-target
training is not necessary for the observed parent-to-child gains.

Hereditary beats the preset SPSA 0.1 control in all 18 comparisons. However its
learned step-size can reach 0.25: a **properly tuned conventional rate** remains a
necessary stronger baseline. Do not label this a general optimizer win, evidence
of novelty, AGI or sustained autonomous RSI. The learned operator's architecture
is more stable by construction; gains alone do not isolate value from inheritance.

The first CPU run took 6.85 seconds, including training and isolated processes.
A repeated run checks deterministic reproduction, not independent confirmation.
All executed seeds become exposed development evidence. Different generations
use different test populations; compare parent and child within each generation,
not absolute losses across generations. No LLM or cross-domain study was run.

## Next discriminating comparison

On newly frozen seeds, select a conventional constant step-size using training
only and the same charged search budget. Retain fixed-proposer, serialization and
independent reconstructed child controls. This distinguishes learned/adaptive
behavior from merely using a larger step. Do not retrofit rate choices to v5's
now-exposed holdouts or count tiny differences as meaningful progress.

## Run

```
node projects/self_transform_v5/test.mjs
node projects/self_transform_v5/run.mjs .work/self-transform-v5-new.json
```

Focused tests cover deterministic selection, equal training budgets, zero-signal
identity, bounded direction-aligned updates and exact reconstructed behavior.
Protocol/source hashes are written first; receipt files cannot be overwritten.
No GPU, network, production services or private receipt publication.
