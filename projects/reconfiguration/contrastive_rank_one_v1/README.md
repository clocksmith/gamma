# Label-free contrastive rank-one transform

A prospective development test of an actual request-local down-projection
update, derived only from the frozen model's own prompt representations. No
labels, external teacher, optimizer, gradient, or learned controller supplies
the desired activation. This is distinct from diagonal activation-energy gains
and norm-preserving rank-two rotations.

## The evidence-to-target bridge

Capture the final layer's last-token post-SwiGLU activation `a` and residual
hidden representation `h` from the complete task prompt. Capture `h_ref` from
the same template and choices with the question replaced by `[question omitted]`.
Define:

```
d = h - h_ref
s = min(1, ||h|| / (||d|| + epsilon))
b = alpha * s * d
Delta W = b a^T / (a^T a + epsilon)
W_down' x = W_down x + Delta W x
```

The rank-one expression is the minimum of
`||Delta W a - b||^2 + epsilon ||Delta W||_F^2`. That makes the **mapping**
principled; it does not establish that amplifying this difference is useful.
The empirical hypothesis is that the direction added by the task content is
worth strengthening. The difference also includes length/position/template
interactions, not a purified semantic direction. It can amplify a mistake.

The desired hidden state is the original `h` plus this bounded correction. It
contains no hidden evaluation answer. The transform retains its fixed factors
for the transformed request. Original weight buffers remain unchanged.

[Context-aware decoding](https://aclanthology.org/2024.naacl-short.69/) provides
related precedent for contrasting model predictions with and without context.
This experiment differs: it contrasts hidden representations and installs an
analytic rank-one FFN update through the existing adapter interface. It is not
a reproduction of CAD or a claim of novelty over all model-editing methods.

## Actual execution

Use `prefillForLoRATraining` only for capture, never an optimizer. Read the final
activation/hidden row, derive factors on CPU, and use `finalizeLoRAAdapter` plus
`setLoRAAdapter` for normal identity, revocation, layout, and execution checks.
Do not bypass those checks. Full logits are used because the selected-token
LM-head helper does not support this artifact's Q4K head.

The target is the final dense full-attention layer. Earlier layer caches do not
depend on this final FFN's output within the prompt. For each candidate, project
the analytically predicted hidden state through the model's own normalization
and head, and compare the actual adapter logits. The frozen absolute tolerance
is 0.005 on the four scored label logits. Zero update must also match base.
These are integration checks, not a quality metric.

## Frozen development screen

Eight fresh JavaScript integer-program questions, balanced four-way labels.
Unit tests execute the supplied trusted fixture bodies to verify their keys.
Answer keys enter only scoring; they are not present in capture or operator
construction. Base, zero, positive alpha 0.25, negative alpha -0.25, and cyclic
other-task direction are fixed before any model output. Other-task directions
are norm matched. Its donor capture cost is charged in addition to own capture.

Write source hashes, tasks, settings, and controls with exclusive creation before
running. Stop at a base floor or ceiling without changing the tasks. Preserve
failed attempts and use a new receipt prefix for a compatibility repair. Once
seen, this population is development only and cannot become confirmation.

```sh
node projects/reconfiguration/contrastive_rank_one_v1/test_operator.mjs
node projects/reconfiguration/contrastive_rank_one_v1/run.mjs \
  DOPPLER_ROOT LOCAL_MODEL LOCAL_RECEIPT_PREFIX
```

## Costs, scope, and boundaries

Charge both capture prefills, readbacks, derivation, adapter identity/attachment,
and full transformed prefill. The auxiliary geometry-validation projection is
a diagnostic and excluded from reported per-request execution cost; it still
uses actual experiment time. Loading is reported separately. Logical factor
bytes are measured; peak process/GPU memory is not measured by this harness.

This study scores only the first answer-token ranking. It is not free-generated
shader execution, multi-token persistence, a full decoding benchmark, retained
learning, or RSI. A useful initial result would still require fresh executable
tasks and a complete decoded-output evaluation. No result authorizes production
promotion. No Doppler runtime, privacy policy, or public provider is changed.

## Position-balanced follow-up (v2)

An optional fourth argument accepts the fixture emitted by
`position_balanced_tasks.mjs`. It replaces the code-question preamble and task
population, without changing alpha, the target layer, the norm bound, or control
arms. Eight fresh non-code cases (lookup, ordering, word editing, constraints,
and codebook mapping) each appear in four cyclic option permutations. Each
semantic answer occupies A, B, C, and D exactly once.

Before any reference/capture prefill or adapter work, run all 32 base requests.
The frozen gate requires 16–30 correct, at least four cases correct on at least
three of their four permutations, and no answer letter selected more than 16
times. A constant-letter strategy scores 8/32 and must fail. A perfect baseline
also stops because there is no accuracy headroom. This is an engineering gate,
not a statistical claim of general capability.

If the gate fails, preserve every base row and stop: zero captures, zero adapter
controls, no replacement cases and no outcome-based prompt rewrite. The result
marks `baseScreenComplete`, while `complete` remains false for the unrun transform
comparison. If the gate passes, proceed with the already-frozen controls.
Costs and interpretation remain separate for the base gate and full comparison.

```sh
node projects/reconfiguration/contrastive_rank_one_v1/test_discrimination.mjs
node projects/reconfiguration/contrastive_rank_one_v1/position_balanced_tasks.mjs > LOCAL_TASKS_JSON
node projects/reconfiguration/contrastive_rank_one_v1/run.mjs \
  DOPPLER_ROOT LOCAL_MODEL LOCAL_RECEIPT_PREFIX LOCAL_TASKS_JSON
```

The gate reports correct answers, each label's count, correctly stable cases,
and cases whose selected semantic option is invariant across permutations.
Correctness alone can hide letter bias; invariance alone can hide consistent
wrong answers. Neither replaces the other.

The semantic other-task donor is the next **distinct question body**, skipping
all option permutations of the current question. Its factors are magnitude
matched and both donor and recipient setup costs are charged. The base rows and
gate verdict are checkpointed to `LOCAL_RECEIPT_PREFIX.base.json` before controls.

The first position-balanced physical development run used the inherited
cyclic-next donor, which usually selected another permutation of the same case.
Its preserved `other-task` rows therefore do **not** qualify as a semantic
other-task control; interpret them only as an option-permutation donor diagnostic.
That mistake does not turn its base/zero/positive/negative observations into
confirmation. The corrected distinct-body donor has a dedicated regression test;
physical execution of that correction must be reported separately, not inferred
from the earlier run.
