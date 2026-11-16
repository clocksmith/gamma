# Self-applicable weight transformer, v1

Separate CPU-only **toy development experiment**, not the no-training rotation
study and not a claim of RSI or AGI. The initial operator is trained by bounded
random search. This intentionally permits training, unlike the rotation track.

## Mechanism

A coordinate-shared four-parameter neural update rule accepts any finite vector
of weights and an equally sized gradient supplied as experience:

```
T_phi(theta, g)_i = theta_i + 0.1 (1 + tanh(phi_3))
                    tanh(phi_0 g_i + phi_1 theta_i + phi_2)
```

The identical function transforms task-model weights or its own four coefficients:
`child = T_phi(phi, meta_gradient)`. It never branches on target identity, invokes
an evaluator, reads history, or uses unexported parent state. Original weights
remain unchanged. Updates are bounded per coordinate; they are not restricted to
multiplicative diagonal gains. This is a tiny learned optimizer, not a transformer
language model or a general hypernetwork architecture.

**Crucial boundary:** the fixed external evaluator computes the meta-gradient by
eight finite-difference evaluations of task-adaptation loss. This is external
optimization signal, not self-generated insight or independent autonomous learning.
A successful child would establish useful self-application under that oracle, not
unassisted recursive improvement. The interpreter and evaluator do not self-modify.

## Frozen experiment

`protocol.json` specifies all seeds, counts, budgets and arms before execution.
32 random initial rules compete only on 32 training tasks. The chosen parent then
undergoes three unconditional generations, each with 32 new meta-training tasks
and 128 independently seeded held-out tasks. Tasks are rotated positive-definite
2D quadratics with known minima. Each target receives 12 update steps. These are
fresh instances of one distribution, not new domains or evidence of generality.

Four parallel chains start at the same initialized parent: unchanged, self update,
ordinary gradient descent of the four coefficients, and a random update whose norm
matches the self update from its own parent. Each pays eight meta evaluations;
unused gradients in unchanged/random arms are explicitly wasted budget. Each also
computes one self candidate, even when discarded. Initialization cost is shared
and reported once. No arm searches extra children, and no holdout score selects,
rejects or tunes descendants. This equalizes expensive objective-call budgets,
not identical wall time; runtime includes differing algebra and subprocess work.

All children of a generation are frozen before its holdout is constructed. Raw
paired losses, counts, parameters, gradients, phase times and evaluator calls are
saved. No significance threshold or general superiority claim is registered.
Every executed seed becomes exposed development evidence; later confirmation
needs separately frozen fresh seeds and multiple independent initializations.

## Reconstruction and limits

Artifacts encode exact float64 little-endian bytes with SHA256, schema and rule
identity. The receipt pins interpreter/evaluator source hashes and Node version.
Each child is reconstructed in a fresh process given only its artifact and a test
input; exact output and reserialization are checked. The interpreter remains an
explicit dependency. That is reproducible model-state reconstruction, **not a
strict quine**, which would reproduce its own program source.

There is no network, GPU, parent-model reference or closure hidden in the operator.
Process separation prevents accidental in-memory history, not a hardened security
boundary against malicious code. The controlled evaluator is fixed trusted code.

## Run

```
node projects/self_transform/self_transform_v1/test.mjs
node projects/self_transform/self_transform_v1/run.mjs .work/self-transform-01.json
```

The runner writes the protocol and source lock first with exclusive creation and
refuses reuse. Receipts stay local. No model download or Python dependency needed.

## First development observation

The frozen v1 run demonstrated reconstruction and same-interface self-application,
not sustained improvement. Lower mean held-out loss is better:

| Generation | Unchanged | Self child | Gradient child | Random child |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.576566 | 0.573704 | 0.525274 | 0.556560 |
| 2 | 0.551517 | 0.597269 | 0.482977 | 0.620565 |
| 3 | 0.431880 | 0.501851 | 0.345134 | 0.594803 |

Each row uses a different fresh population shared by all arms. Do not compare
absolute losses between rows as learning curves. The self parent's losses on
those same populations were 0.576566, 0.554178 and 0.472883, respectively: its
first small average improvement was followed by two regressions. Even generation
1 improved only 54 of 128 tasks and worsened 74; a mean gain is not uniform benefit.
The ordinary meta-gradient control improved all three generations and beat the
self chain on each held-out population. This is one seeded development run, not a
significance claim or a reason to tune against these now-exposed held-out tasks.

The first local run took about 286ms total, including approximately 7ms initial
search and twelve isolated child reconstruction subprocesses. Timings are CPU
smoke measurements, not a performance benchmark. Each adaptation arm is charged
3,072 task-gradient calls and 3,073 transform calls per generation; initialization
costs 12,288 task gradients. Holdout evaluation and reconstruction probe work are
reported separately from adaptation budgets. No result implies LLM transfer.
