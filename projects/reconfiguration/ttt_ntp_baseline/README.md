# TTT-NTP baseline assessment

Inspected 2026-11-15. No upstream code executed, packages installed, weights
downloaded, continual pretraining launched, or inference comparison claimed.

## Scientific distinction

[Paper, version 2](https://arxiv.org/html/2606.21803): the value is a learned
projection of the next position's same-layer normalized MLP input. Backbone and
projection are jointly continually pretrained, then inference fits a prompt-local
ridge update to selected down projections. Reported RULER average gains over
released backbones are 2.9–4.1 points, not universal per-length wins. Tested
backbones are full-attention models, not our hybrid Qwen3.5 artifact. The paper
explicitly ties meaningful regression to its pretraining. This does not establish
that identity-projection adaptation helps an untouched checkpoint, or establish
RSI. Its prompt labels are already observed next tokens, not unseen answers.

## What the code actually requires

Pinned repository: [`c11da918d9a5aebf3f3cb0f45a79c2e66d9ad79a`](https://github.com/yancyou/TTT-NTP/tree/c11da918d9a5aebf3f3cb0f45a79c2e66d9ad79a).
The public release list was empty when checked. The inspected README supplies a
train/export/evaluate recipe, not a downloadable trained-checkpoint link.
A broader model-index search subsequently located public candidate checkpoints,
so absence from that README is **not** evidence that weights are unavailable.

Verified candidate: [YoungXuan/Qwen3-0.6B-NHS](https://huggingface.co/YoungXuan/Qwen3-0.6B-NHS)
at revision `786708b3d940e139edf60a62995f5b2c5a8059a4`. Public metadata and a bounded
safetensors-header read confirm all seven BF16 `[1024,1024]` projection matrices,
with the expected `sgd`, `diag_shared`, eta 2.6, chunk 1024 and adapted-layer
configuration. The repository has no README/model card or detailed training
receipt; matching configuration is not independently verified training provenance.
The weight file is 1,517,981,192 bytes; advertised LFS SHA-256 is
`bbd600491d2c5dff5fc73d429fb5b4f62e5bde9777f72ed31c09eae01798bc4e`.
Only metadata/configuration/header bytes were read, not the model tensors.

The related [Llama 8B NHS card](https://huggingface.co/YoungXuan/Llama-3.1-8B-NHS)
reports a `specnorm`/small-initialization variant with single-seed caveats and
some task regressions. It is not interchangeable with the paper's `sgd` recipe.
Its larger reported aggregate gain must not be attributed to the exact paper
baseline without verifying the variant and evaluation settings.

The [0.6B configuration](https://github.com/yancyou/TTT-NTP/blob/c11da918d9a5aebf3f3cb0f45a79c2e66d9ad79a/configs/pretrain/qwen3_0p6b.yaml)
uses 100 steps × 64 sequences × 32768 tokens = 209,715,200 nominal training tokens,
AdamW at 5e-6, and seven adapted layers `[0,4,8,12,16,20,24]`. It is not 100
inference steps. Initializing its projection with a diagonal does not remove the
subsequent training cost.

The [closed-form patch](https://github.com/yancyou/TTT-NTP/blob/c11da918d9a5aebf3f3cb0f45a79c2e66d9ad79a/inference_closed_form_patch.py):

- Hooks MLP **inputs**, recomputes gated activations, aligns current key with the
  following observed hidden state, and applies the stored projection transpose.
- Uses primal/dual ridge according to dimensions, caps perturbation, optionally
  restores original row norms, and backs up/restores down-projection weights.
- Missing learned projections fall back to identity. Our comparator must reject
  this fallback, including partially missing layer projections.
- KV reuse crops the cache to `T-1` and processes the last prompt token again.
  Thus it differs from our old base-cache arm's unchanged first-token logits.
- Restoration follows generation rather than an encompassing `finally`. An
  isolated evaluation wrapper must restore on failures before another sample.

The [evaluation launcher](https://github.com/yancyou/TTT-NTP/blob/c11da918d9a5aebf3f3cb0f45a79c2e66d9ad79a/eval_cf_ruler.sh)
sets eta 0.1, per-layer perturbation cap 0.1, lambda 1.0, next-position shift 1,
last 8192 fitting tokens, and row-norm preservation. These defaults differ from
some direct Python CLI defaults; pin the effective values, not the script name.
GPU count controls parallel evaluation and must not be misreported as required
for a single inference. The provided training quickstart uses eight GPUs.

## Comparison with our work

| Method | Evidence and target | Extra learned components | Existing evidence |
|---|---|---|---|
| Channel gain | instruction/reference channel energy | none | no demonstrated quality gain |
| Rank-two rotation | instruction/complement activation plane | none | no demonstrated quality gain |
| Contrastive rank-one | full-minus-ablated final hidden representation | none | valid native geometry; discriminative development accuracy regressed |
| Associative delta reference | numeric labeled demonstrations | none, but support labels supplied | synthetic adaptation works; ridge is stronger |
| TTT-NTP | observed next-position normalized MLP state through trained projection | jointly trained backbone/projections | authors' long-context results; not reproduced locally |

Our `prefillForLoRATraining` returns post-FFN residual hidden states, not the
normalized MLP inputs required here. Relabeling those captures, using identity
projection, substituting the hybrid 2B model, or omitting CPT would create a new
ablation. None may inherit the paper's result or name as a faithful reproduction.

## Small fair development comparison after artifacts exist

Use one exact Qwen3-0.6B TTT-NTP checkpoint and tokenizer for the primary arms:
(1) no write, (2) published closed-form write, (3) our fixed contrastive rank-one
transform. Keep released-base and CPT-only results separate to expose training
contributions; do not attribute all checkpoint gains to inference adaptation.

Before model outputs, freeze sixteen fresh key-value retrieval documents: eight
cases each at 4096 and 8192 token budgets, needles balanced across early/middle/
late positions, unique answer strings and distractors. Serialize tasks before
loading the model. Use free generation with 32-token cap and exact normalized
answer matching, not answer-letter logits. Test the oracle on correct values,
wrong values, swapped keys, and answers missing from the source.

Run no-write first. Continue only with 4–14/16 correct; otherwise preserve and
stop without replacing tasks. This is a development feasibility gate, not a
statistical significance threshold. Alternate arm order by case. Use the same
prompt IDs, artifact, quantization, output cap and resource limit. Record the
implemented cache behavior rather than pretending full re-prefill and last-token
replay are identical algorithms.

Charge capture, activation storage, projection, solve, update application,
first-token recomputation, decode, and restoration. Report total latency,
first-token latency, decode interval, peak memory, output validity, paired
wins/losses and regression counts. Count CPT separately as setup, never as zero.
No hyperparameter tuning against these observed tasks; fresh confirmation follows
only after a development signal and a separately frozen candidate.

## Next concrete action

Review provenance and license for the pinned public 0.6B candidate above, then
obtain explicit model-acquisition approval before fetching its tensors. Verify
the SHA-256 and retain all seven projections plus tokenizer/config. Validate untouched-checkpoint restoration and cache first-token behavior
on one sample before the sixteen-case study. If only raw base weights are
available, label any identity-projection experiment as an **untrained ablation**.
Do not silently start 210M-token pretraining or claim an unperformed benchmark.


## Handoff status

Research stopped at the owner's request before acquisition or execution. The
candidate is located, but has not been loaded, converted, qualified, or compared
locally. No claim of reproducing TTT-NTP is made. The sixteen-case protocol above
is prospective and has not generated model outputs. Continue only in the owner's
separate Gamma research track.
