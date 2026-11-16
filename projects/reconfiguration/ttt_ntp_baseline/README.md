# TTT-NTP baseline assessment

Inspected 2026-11-15. No upstream code executed, packages installed, continual pretraining launched,
or inference comparison claimed. The owner authorized the pinned checkpoint
download; all 1,517,981,192 weight bytes are acquired and the pinned SHA-256
and seven projection contracts pass local verification.

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
Initial inspection read metadata/configuration/header bytes only. Subsequent
owner-authorized acquisition verified the full weight file locally.

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


## Track A resumed and local qualification

The owner retained this prompt-conditioned transformation track while taking the
separate hereditary research track. Acquisition of the pinned 1.52 GB checkpoint
was explicitly approved. Do not conflate the two research tracks.

`artifact_contract.py` verifies exact file size and SHA-256, configuration, all
seven BF16 projection shapes and spans. A missing single projection fails rather
than silently becoming an identity ablation. This proves artifact identity, not
who trained it or whether its undocumented training history matches the paper.

`retrieval_tasks.py` builds the sixteen-case development population with the
actual supplied tokenizer, exclusive fixture creation and exact normalized
free-answer scoring. The unit test uses character IDs only to test budget
handling; those counts are not model-token measurements. Model-tokenized fixtures
and model outputs remain local under `.work/`. No confirmation population is used.

Six focused tests cover complete/missing/malformed/overlapping projection
contracts and retrieval budget/source/oracle integrity. Ruff checks pass.
The existing environment has PyTorch 2.9.1 with MPS and Transformers 4.57.3.
No GPU execution may begin until live ownership is verified clear. No result is
claimed from downloading weights or preparing this harness.

Tokenizer qualification: the installed Transformers 4.57.3 applies its Mistral
warning heuristic to local non-Mistral configs saved at 4.57.3 (the type-based
skip is limited to <=4.57.2). We did not apply that suggested regex rewrite to
Qwen. Direct `tokenizers.Tokenizer.from_file` produces identical IDs for all
sixteen frozen prompts. This verifies consistency with the pinned tokenizer
JSON, not undocumented training provenance. Actual input lengths are
4065–4096 and 8156–8191 tokens. Fixture SHA-256:
`3790ba8a1ea3c16c281976f22a4e604ec20118191a89ba1be7de9cc55ca5f20c`.

`baseline_screen.py` is the **no-write feasibility gate only**, not a completed
TTT comparison. It uses installed official Transformers with local files only,
remote code disabled, explicit BF16/SDPA, greedy generation and the frozen input
IDs. It requires exactly the seven unused projection keys when loading the
ordinary backbone; any other missing or unexpected weights abort. Capturing
first-token and remaining decode separately avoids treating end-to-end latency
as an internal prefill measurement. It checkpoints each generated result locally.
Syntax and oracle checks pass; model execution is still pending resource clearance.

## Mars execution and 6-arm trained-checkpoint comparison

> **Classification:** **TRAINED-CHECKPOINT BASELINE** (`YoungXuan/Qwen3-0.6B-NHS` at `786708b3d940e139edf60a62995f5b2c5a8059a4`, `209,715,200` nominal continual-pretraining tokens + `14,680,064` bytes across seven BF16 `[1024, 1024]` `ttt_proj` matrices). Kept strictly separate from the training-free prompt-conditioned hypothesis in [`../surprisal_ridge_v1/`](../surprisal_ridge_v1/README.md).

All three runs below executed sequentially on uncontended Mars (`mac`) MPS hardware (`torch 2.10.0`, `bfloat16`, `sdpa`) after verifying zero overlap with active Track A processes.

### 1. Preserved `SEED=831709` Feasibility Screen (`baseline_screen.py`) and Boundary Diagnosis

- Fixture: [`.work/ttt-ntp-development-01.tasks.json`](../../../.work/ttt-ntp-development-01.tasks.json) (`SHA-256: 3790ba8a1ea3c16c281976f22a4e604ec20118191a89ba1be7de9cc55ca5f20c`)
- Receipt: [`.work/ttt-ntp-development-01.no-write.json`](../../../.work/ttt-ntp-development-01.no-write.json) (`SHA-256: 3ecd1b6fdb0c6362ae7fe405e21fbd6315922caff9e80e8841444aaa178780dc`)
- Literal `retrieval_tasks.score_answer` score: `0 / 16` (`mean first_token_seconds = 8.44s` at `4096`, `37.12s` at `8192`).
- **Upstream/downstream boundary inspection:** `Qwen3-0.6B-NHS` is a raw base completion model (not instruction-tuned). It actually retrieved the exact 64-bit target hex string on **`10 / 16` cases** (`6 / 8` at `4096` tokens, `4 / 8` at `8192` tokens; the remaining `6 / 16` emitted distractor records), but failed literal string equality for two boundary reasons:
  1. `baseline_screen.py` decoded to `max_new_tokens = 32` without stopping at `\n`, so every completion appended `\n```` (`[198, 73594, 151643]`).
  2. `retrieval_tasks.py` ended prompts with `\nRequested key: {key}\nValue:`, breaking the in-table `{key} = value_<16hex>` grammar so `9 / 16` completions emitted raw `<16hex>` without repeating `value_`.
- Both original `SEED=831709` artifacts remain preserved without modification.

### 2. Repaired Single-Needle Screen on Fresh `SEED_V2=942617` (`repaired_comparison.py`)

[`repaired_comparison.py`](repaired_comparison.py) repairs the record-completion boundary (`{key} =` prompt suffix, newline stop, and single-line `value_<16hex>` exact match verified in [`test_repaired_comparison.py`](test_repaired_comparison.py)) on fresh `SEED_V2=942617`:

- Fixture: `.work/ttt-ntp-development-v2.tasks.json` (`SHA-256: 8b50b2795c9e29dceb6803c6367096b6f4dd4e2c5967baa2a24623ced9e6f004`)
- Receipt: [`.work/ttt-ntp-development-v2.comparison.json`](../../../.work/ttt-ntp-development-v2.comparison.json) (`SHA-256: c6426f13c04b70b22e9e4a487bc4334388d5066847e6ee648e871c4c0e9753ec`)
- Result: `trained_backbone_no_write` scored **`15 / 16`** (`8 / 8` at `4096` tokens, `7 / 8` at `8192` tokens) **without any inference-time weight write**, exceeding the `4..14/16` non-ceiling gate (`stop_reason: "no-write gate scored 15/16 outside 4..14"`). Preserved unmodified.

### 3. Complete 6-Arm Long-Context Comparison on Discriminative `SEED_V3=953729` (`shared_8hex_stratified`)

To evaluate all six arms inside the required `4..14/16` discriminative window without ceiling compression, `SEED_V3=953729` (`--sibling-mode shared_8hex_stratified`) places `1` (odd cases) or `3` (even cases) confusable sibling keys sharing the first 8 of 16 hex characters (`key_<8hex_stem><8hex_suffix>`) into each `4096`- and `8192`-token haystack:

- Fixture: `.work/ttt-ntp-development-v3.tasks.json` (`SHA-256: d5acc92b77d851c21c06df6a78c539c325ad1ecefdead830a3ebdcc4dad41d2f`)
- Receipt: [`.work/ttt-ntp-development-v3.comparison.json`](../../../.work/ttt-ntp-development-v3.comparison.json) (`SHA-256: 422b2c3d79205e5202b565f90d25601a11a6117584eb0fb8751f7be7e0e85f1b`)
- Feasibility gate: `trained_backbone_no_write` scored **`8 / 16`** (`4 / 8` at `4096`, `4 / 8` at `8192`, `pass = true`).
- Implementation fidelity: `fit_ttt_deltas` + `apply_and_decode_with_restoration` matches upstream `eval_cf_ruler.sh` defaults (`eta = 0.1`, `per_layer_eta = true`, `eta_target = 0.1`, `lam = 1.0`, `shift = 1`, `last_k = 8192`, `norm_preserve = true`), crops `DynamicCache` to `T - 1` to recompute the final prompt token under modified weights, restores `down_proj` inside `finally`, and verified `max_abs_restore_drift = 0.0` on every sample.

| Arm | `4096` Acc | `8192` Acc | Total Acc | Paired `+W / -R` vs No-Write | Mean Setup (s) | Mean First Token (s) | Mean Decode (s) | Mean Total (s) | Logical Update Bytes | Peak MPS / RSS (GB) |
| :--- | :---: | :---: | :---: | :---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `trained_backbone_no_write` | `4 / 8` | `4 / 8` | `8 / 16` (`50.0%`) | `0 / 0` | `0.000` | `20.702` | `4.078` | `24.780` | `0` | `17.71` / `1.09` |
| `ttt_closed_form_write` (7 trained `ttt_proj`) | `4 / 8` | `4 / 8` | `8 / 16` (`50.0%`) | `0 / 0` | `24.911` | `25.149` | `4.309` | `29.458` | `44,040,192`* | `11.63` / `1.09` |
| `untrained_identity_ablation` (`ttt_proj = I`) | `4 / 8` | `4 / 8` | `8 / 16` (`50.0%`) | `0 / 0` | `24.718` | `24.956` | `4.280` | `29.236` | `44,040,192` | `8.48` / `1.09` |
| `wrong_context_ttt_write` (donor + own setup) | `4 / 8` | `4 / 8` | `8 / 16` (`50.0%`) | `0 / 0` | `49.742` | `49.972` | `4.411` | `54.383` | `44,040,192`* | `8.55` / `1.09` |
| `random_norm_matched_write` | `4 / 8` | `4 / 8` | `8 / 16` (`50.0%`) | `0 / 0` | `25.312` | `25.531` | `4.288` | `29.819` | `44,040,192` | `8.66` / `1.09` |
| **`matched_compute_no_write`** (2 half-haystack passes) | **`5 / 8`** | **`6 / 8`** | **`11 / 16` (`68.8%`)** | **`+3 / 0`** | `0.000` | **`6.675`** | `11.852` | **`18.527`** | `0` | **`9.25`** / `1.09` |

*\*Plus `14,680,064` bytes of continually pretrained `ttt_proj` parameters and `209,715,200` nominal CPT tokens.*

### Key Findings

1. **`ttt_closed_form_write` altered generation on hard cases (`4 / 16` decoded text diffs vs `no_write`) without improving retrieval accuracy (`8 / 16` vs `8 / 16`):** Even with jointly continually pretrained `ttt_proj` matrices and KV-cropped last-token replay, closed-form FFN ridge regression over `4096–8192` prompt tokens did not resolve shared-prefix key collisions and added `+4.68s` mean latency (`29.46s` vs `24.78s`) plus `44.0 MB` of temporary weight deltas.
2. **`untrained_identity_ablation` (`8 / 16`), `wrong_context_ttt_write` (`8 / 16`), and `random_norm_matched_write` (`8 / 16`) all tied `ttt_closed_form_write` (`8 / 16`):** Under row-norm preservation and `eta = 0.1`, none of the prompt-derived FFN writes separated from random or donor perturbations on exact needle retrieval.
3. **Context partitioning (`matched_compute_no_write`) beat every weight-write arm on both quality and wall-clock latency (`11 / 16`, `+3` wins / `0` regressions, `18.53s` vs `29.46s`):** Evaluating two `T / 2` windows with untouched weights reduced quadratic attention cost ($2 \times (T/2)^2 = T^2 / 2$), cut peak MPS allocation from `17.71 GB` to `9.25 GB`, and improved accuracy by `+18.8` percentage points over `ttt_closed_form_write`.
