# Associative delta reference v1

A distinct, prompt-demonstration-conditioned **additive weight transform**. This
is not another rotation angle, an instruction-energy gain, an LLM experiment,
a neural quine, or recursive self-improvement. It uses numeric labeled examples
supplied as the request's evidence. No outer model or controller is trained.

## Mechanism

For immutable base matrix W, demonstration key k and desired value v:

```
D_0 = 0
D_(i+1) = D_i + rate * (v_i - (W + D_i) k_i) k_i^T / (k_i^T k_i + epsilon)
y = W q + D q
```

Each update is rank one; the accumulated correction is not necessarily rank one
or rank two. `derive` returns factors U,V with D=UV. The base matrix is never
modified. The same frozen update applies to every subsequent query in that
request. Discarding the factors restores the base exactly. JSON roundtrip in the
runner is ordinary serialization, not neural reproduction.

This follows the established fast-weight delta-rule family, not a novelty claim:
[Schlag, Irie, Schmidhuber, ICML 2021](https://proceedings.mlr.press/v139/schlag21a.html).
Our normalized update and hand-specified numeric evidence are a reference
experiment, not a reproduction of that paper's learned controller.

## Frozen development contract

`protocol.json` fixes two families, seeds, dimensions, noise, arms, and rates before
execution. Thirty-two tasks per family each supply 32 noisy demonstrations and 64
fresh query inputs. One family is a rank-two linear shift; the other is a tanh
shift that cannot generally be expressed exactly by the linear update.

Controls are unchanged base, shuffled labels, wrong-task labels, norm-matched
random updates, and closed-form ridge adaptation. Correct-query targets are
constructed only after all six arms have emitted predictions. Arm order rotates
by task. No hyperparameter or task selection occurs after scoring. All tasks are
development evidence; there is no confirmation population or confirmation claim.

```sh
python3 projects/reconfiguration/associative_delta_v1/test_operator.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 \
  projects/reconfiguration/associative_delta_v1/run.py LOCAL_RECEIPT_PREFIX
```

The source/protocol lock is written exclusively before evaluation. Receipts must
not overwrite an earlier run. Store raw receipts locally unless publication is
authorized. Pin actual source, Python and NumPy versions from the lock.

## Costs and interpretation

Reports separate derive time, query time, and logical update-array bytes. They do
not measure process startup, NumPy import, peak RSS, GPU performance, or full LLM
prefill/decode. The reference repeatedly stacks factor arrays while deriving;
that is convenient, not an optimized implementation. Factors retain one column
per demonstration, even though algebraic rank is bounded by matrix dimensions.
Ridge receives the same evidence, but is an offline batch baseline rather than
an online constant-update-cost competitor. Compare its actual measured costs
instead of assuming outer products must be cheaper.

A win over no-update establishes only that labeled task evidence can improve
this small reference. A win over wrong labels establishes useful conditioning,
not general intelligence. If ridge wins, do not promote delta as optimal.

## Boundary before Doppler integration

The unresolved LLM bridge is **where valid desired values v come from**. A model's
own unmodified activations used as both prediction and target yield zero useful
residual. Hidden evaluator answers must never be supplied as demonstrations.
An LLM study would need permitted support examples, a declared teacher/gradient
or residual-construction mechanism with fully charged cost, a specified matrix
and feature extraction, retention controls, and fresh executable evaluation.
Do not port this toy result into a claim of improved shader generation.

There are no runtime changes, GPU runs, service changes, or effects on existing
frozen gain, rotation, and heredity campaigns.
