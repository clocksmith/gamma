# Self-target training objective ablation v3

The smallest change from v2: **train for the adaptation quality of a self-produced
child**, rather than only for the initial rule's task adaptation. Operator, four
coefficients, scalar-probe mechanism, radius, update limits, reconstruction and
controls are unchanged. This is a bounded CPU toy, not an LLM or RSI claim.

## Training without held-out leakage

Each of three independently seeded replicates draws 32 initial parameter vectors.
For every candidate, derive one self-target update on 32 training-support tasks.
Evaluate the parent and resulting child on a separate 32-task training-query set.
Two initializers choose from the identical pool:

- `task_only`: smallest parent training-query loss.
- `self_target`: smallest child training-query loss.

In both cases the selected **parent** becomes the initial rule; the child used for
training fitness is not adopted. Both initializers pay the complete identical
candidate-evaluation budget, including unused self-training work for task-only.
The implementation shares this computation but charges it to both hypothetical
methods. Per replicate it costs 501,760 scalar loss calls, 61,472 transforms and
256 meta-objective evaluations. Initialization is trained random search, not a
training-free claim. Neither objective sees evaluation holdouts.

Each initializer then runs three unconditional generations against hereditary,
fixed initial proposer, serialization-only and conventional SPSA controls. Every
arm pays v2's eight meta-objective calls per update; no hidden acceptance search.
All eight candidates are produced in clean subprocesses before scoring that
generation. Parent and child are reconstructed in independent scoring processes.
Each generation receives 128 fresh quadratic tasks, shared by all arms and both
initializers. Every generation's meta-training population is also fresh. Scoring
never changes future selection, seeds, algorithm, stopping or budgets.

The external scalar-loss oracle and fixed interpreter remain essential. The
operator forms an internal derivative estimate from those losses. Neither
self-targeting nor reconstructing a child makes the process independently
intelligent, a strict quine, or autonomous learning without an external objective.

## Frozen development results

Both objectives selected the **same initial candidate in all three replicates**
(indices 3, 12 and 20). Consequently their subsequent losses and artifacts are
identical. The modified training objective had no measured effect in these pools;
reporting both cohorts as independent evidence would double-count observations.

For the three distinct hereditary chains, parent to child mean held-out losses:

| Replicate | Generation 1 | Generation 2 | Generation 3 |
| --- | --- | --- | --- |
| 31000 | 1.900070 to 1.937500 | 1.727274 to 1.735662 | 1.490780 to 1.538176 |
| 41000 | 2.035271 to 1.986623 | 1.553615 to 1.525378 | 1.487239 to 1.440346 |
| 51000 | 1.654690 to 1.629843 | 1.679448 to 1.617664 | 1.350472 to 1.371348 |

Lower is better. These are within-row-generation comparisons on fresh populations,
not a single absolute learning curve. Hereditary improved five of nine comparisons;
one chain improved all three times. But **SPSA children had lower loss than the
hereditary children in all nine matched comparisons**. Hereditary was better than
fixed proposer in only three of the six nonidentical later-generation comparisons;
first-generation results are necessarily identical. Serialization alone changed
nothing. There is no demonstrated advantage from updating the proposer itself.

The first run took 7.39 seconds total CPU including training, 72 proposal
subprocesses and 144 scoring subprocesses. Per-stage costs and paired task losses
are retained locally. This is a development observation, not statistical
confirmation; all executed seeds are now exposed. Prior v1/v2 files and evidence
remain unchanged.

## Interpretation and next decision

This minimal objective change did not alter candidate selection. It does not
establish that self-target training cannot help. A subsequent separately frozen
experiment could optimize a multi-step self-target training objective directly,
rather than re-rank the same small random pool. It must compare equal initial
search cost, retain the fixed-proposer control and conventional optimizer, and
use new evaluation seeds. Do not retrofit these held-out outcomes into selection.

## Run and checks

```
node projects/self_transform/self_transform_v2/test.mjs
node projects/self_transform/self_transform_v3/test.mjs
node projects/self_transform/self_transform_v3/run.mjs .work/self-transform-v3-new.json
```

The runner reuses v2's operator and isolated worker. Every dependency is source
hashed before work begins, and exclusive receipt creation prevents overwriting
prior protocols. Tests verify training selection, determinism, immutable target
ownership and exact equal-budget counts. No GPU, network or model download.
