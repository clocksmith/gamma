# Multi-generation self-target training v4

A bounded CPU follow-up to v3. The operator, scalar-loss probes and test controls
remain v2's. The change is an explicit optimization of a three-generation training
objective, rather than choosing among an unchanged random pool. This is externally
trained initialization followed by self-application, not autonomous RSI.

## Frozen training experiment

Three fresh seeds independently initialize four coefficients. Two training arms
start at the identical vector and receive the same 32 bounded mutation draws
(each coordinate uniform in [-0.2, 0.2]). Each draw perturbs that arm's current best
candidate. Greedy acceptance uses training fitness only. Thus candidate trajectories
may diverge, but their search and evaluation budgets remain equal.

Every candidate undergoes three self-target updates on three fixed training-support
sets. At every step, the original parent and that step's descendant are evaluated
on the corresponding independent training-query set. The two fitnesses are:

- `task_only`: mean original-parent loss across the three query sets.
- `self_target`: mean descendant loss across the three query sets.

The chosen artifact is the candidate parent, not a descendant. Both arms compute
all losses and unrolls even where unused. Each initializer pays 33 candidates,
776,160 scalar task losses, 95,139 transforms and 792 meta-objective calls. The
training populations remain fixed within a replicate: selection can overfit them,
which is why the evaluation populations are separate. No fresh-test outcome changes
training, budgets, seeds or acceptance. This is an intentionally bounded search,
not a claim of converged or optimal training.

## Evaluation

Three unconditional generations, four controls (hereditary, fixed initial proposer,
serialization-only, SPSA), 128 fresh test targets per generation, new meta-training
populations. Each proposal and each parent/child score executes in a fresh process
from exact serialized weights. All children are frozen before that generation's
holdout is scored. Each adaptation arm receives exactly eight scalar meta-objective
queries, totaling 12,544 task losses and 1,537 transforms per round. The external
oracle and immutable interpreter remain necessary. Only the coefficient state
changes and is inherited.

Prior v1-v3 protocols and results are unchanged. Source locks include all reused
workers/evaluator dependencies. The runner rejects receipt-path reuse. All executed
holdouts are subsequently exposed development evidence, not future confirmation.

## Outcome: no hereditary advantage

Self-target training now selected different coefficients in two of three replicates,
so this intervention actually changed the trained operator. It nevertheless did not
beat task-only training. Final-generation fresh-target mean losses (lower is better):

| Replicate | Initialization | Hereditary | Fixed proposer | Serialization only | SPSA |
| --- | --- | ---: | ---: | ---: | ---: |
| 61000 | Task only | 2.178392 | 2.126364 | 2.115387 | 1.805216 |
| 61000 | Self target | 4.396178 | 4.395558 | 4.369559 | 4.272291 |
| 71000 | Task only | 1.500528 | 1.511300 | 1.339561 | 1.300325 |
| 71000 | Self target | 1.676441 | 1.655737 | 1.659614 | 1.499411 |
| 81000 | Both, identical | 2.853155 | 2.863232 | 3.081020 | 2.274049 |

The self-target cohort improved against its own parent in five of nine generation
comparisons; one chain improved all three times. Conventional SPSA had lower child
loss in all nine matched comparisons. The third replicate's initializations were
identical, so its duplicate cohort is not independent evidence. Serialization
alone preserved behavior exactly. Do not treat successive rows/generations with
different targets as a single learning curve.

First run took 7.07 seconds CPU including all search, 72 proposal subprocesses and
144 scoring subprocesses. Training cost was 4,656,960 scalar task losses across six
initializers, plus separately charged evaluation/adaptation work. Raw candidate
trajectories, acceptance decisions, losses, weights and budgets are retained locally.

## What this does and does not establish

Multi-generation fitness made a real selection difference but did not improve the
measured outcome. The four-parameter updater can learn task behavior, reconstruct,
apply to itself and sometimes improve its successor, but this test provides no
reliable advantage to hereditary self-updates over a fixed conventional optimizer.
Changing the objective alone is not the missing proof. Inspect training trajectories
and representation limits before spending GPU or claiming scalable self-improvement.
No LLM, generalization across domains, AGI or autonomous RSI was tested.

## Run

```
node projects/self_transform_v2/test.mjs
node projects/self_transform_v4/test.mjs
node projects/self_transform_v4/run.mjs .work/self-transform-v4-new.json
```

Focused checks verify equal training budgets, deterministic mutation trajectories,
correct selection, immutable original targets, source reconstruction and unchanged
serialization controls. No network, model download, GPU or production changes.
