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
