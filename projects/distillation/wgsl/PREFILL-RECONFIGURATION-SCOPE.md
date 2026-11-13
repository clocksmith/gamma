# Prefill-derived decode reconfiguration (scope, not authorized)

Scope drafted 2026-11-12 by A1 from the owner's hypothesis and review. It authorizes
no runtime change, training, evaluation or materialization run. SAME-R
(`projects/samer`) is the comparison protocol, not an arm.

## Hypothesis (owner)

A fast rule can extract a useful reconfiguration of one frozen model from that model
and its prefill state, with no additional training: base prefill, then decode through
a request-specific transform, then discard the transform. The weights stay shared,
and each request carries only a small transform state `z`.

The discovery is the mapping from prefill state to a useful transform; any reversible
transform is easy to build. A failed rule rejects that rule, not the idea of fast
reconfiguration.

## Starting evidence (scope only)

- WGSL Writer v2: three trained rank-32 LoRA seeds reached 16/16, 15/16 and 15/16
  semantic passes on 1-D elementwise f32 compute shaders. A compact weight change can
  specialize behaviour; this does not show the change can come from the prompt without
  training.
- Doppler applies LoRA as an effective change around immutable base weights, and
  refuses to change the adapter during generation
  (`doppler/src/inference/pipelines/text/pipeline.js:557`).
- Doppler's Qwen gated-delta kernels (`doppler/src/gpu/kernels/gated_delta_*.wgsl`)
  update a context-written state matrix, a fast-weight mechanism. They change state,
  not model weights.

## Tracks

1. **Primary, no new training:** an analytical rule maps prefill activations to `z`
   and applies it around the frozen weights. Candidate families, each tested
   separately:
   - **first candidate: prompt-conditioned channel reweighting** (owner proposal,
     2026-11-12). In selected late MLP layers with `y = W_down·a` and SwiGLU
     `a = silu(W_gate x) ⊙ (W_up x)`, per-channel energy is the mean of `a²` over a
     fixed token span.
     - Score `sᵢ = (E_instr,i − E_ref,i) / (E_ref,i + ε)`, gain
       `gᵢ = exp(β·clip(sᵢ, −c, c))`, normalized so the mean of `log g` is 0.
     - Decode uses `y = W_down·(g⊙a)`, an effective `W_down·diag(g)`; the base weights
       never change and reset discards `g`.
     - `E_instr` is an exact instruction token span, excluding chat-template tokens.
       `E_ref` is variant A, the same prompt without that span, or variant B, the
       mean over a fixed set of unrelated unlabeled prompts. Variant B controls general
       activation patterns, but controls position only when the reference prompts use
       the same template and the span sits at matched token positions.
     - β (both signs), c, ε, the reference variant and the layer set are chosen on the
       selection population only.
     - Extra control: gains permuted across channels.
     - The multiply fuses into the existing MLP activation kernel; the prefill
       statistics are one per-channel reduction per chosen layer. Overhead is
       measured, not assumed.
     - This is activation scaling equivalent to one diagonal weight change, not a
       universal weight transform. A failure rejects this rule only.
   - additive low-rank, `W + A(z)B(z)ᵀ`, with `A` and `B` taken from prefill
     activations (for example, top singular directions of a layer's prefill inputs);
   - multiplicative, `U(z) W V(z)ᵀ` with near-identity structured `U` and `V`, applied
     as `U(W(Vᵀx))` on vectors, never by rewriting the matrix;
   - structured rotations such as Householder or Givens products acting on vectors.
2. **Upper comparison, trained controller:** a small network maps prefill state to
   `z`. Size it first: start with coefficients over a shared set of fixed bases
   rather than predicting every LoRA parameter, and report its parameter count and
   cost per request. It does not test the no-training claim.

## Cache interface (explicit arms)

Base-prefill keys and values followed by transformed decode is a hybrid computation.
Each track runs three arms:

- transform only the MLP layers. This is still a hybrid: a changed MLP output alters
  every later layer's inputs, so later layers' keys and values for new tokens differ
  from the cached base computation. Measure that divergence;
- transform all projections and keep the base KV cache (the hybrid), with the
  divergence measured directly;
- re-prefill with the transformed weights (exact, at roughly double the prefill
  cost).

## Controls and comparisons (matched budgets)

- the base model, given the transform's extra compute as more samples (best-of-k);
- the trained WGSL v2 adapter as the reference ceiling: seed 47, the selected seed of
  three (11, 29, 47), PEFT tree SHA-256
  `aa8ad92a5e57c04d359fa2a7095f40eda6f85728f4e1ef90f4a9e8e5633d200d`; reported 15/16
  (93.75%) on seed confirmation and 11/16 on checkpoint selection
  (`doppler/docs/status/wgsl-writer-v2-result-2026-07-14.md`). Those populations are
  exposed, so its ceiling on the fresh tasks is measured, not assumed;
- the same rule fed shuffled or unrelated context, a random `z` of the same size, and
  (for gain rules) the same gains permuted across channels, to show whether the
  prompt-specific assignment matters at all;
- end-to-end timing in every arm: prefill, time to compute `z`, decode tokens per
  second and memory.

## Metric

Semantic pass on fresh, family-disjoint executable shader tasks: compilation,
dispatch, CPU-oracle agreement, canaries, workgroup and shape variations,
permutations, one submission per task. Compiler acceptance alone counts for nothing.
No synthetic training data is needed for the primary track; independent tests are
still required.

## Success criteria (proposed by A1; the owner freezes them before any run)

No run starts until these numbers are frozen in this file. Measured once on the
confirmation population after the rule and its settings are fixed on the selection
population. A no-training rule is an interesting result only if all of these hold:

1. **Prompt dependence:** it beats both the shuffled-context and random-`z` controls on
   the same tasks; exact paired sign test on discordant tasks, p < 0.05.
2. **Gap closure:** it closes at least 50% of the semantic-pass gap from the base model
   (with matched best-of-k) to the seed-47 adapter, measured on the same tasks. If that
   gap is under 4 tasks, the comparison is uninformative and the result is reported as
   such, not as a pass.
3. **Setup cost:** zero offline training. Rule settings are chosen on the selection
   population only, using at most 1% of the GPU-hours recorded for one seed-47 SFT run.
   A configuration that this budget leaves unexplored is untested, not evidence that
   the rule or the hypothesis fails.
4. **Serving cost:** computing `z` plus any added decode work adds at most 10% to the
   base model's end-to-end request latency, and at most the memory of one rank-32
   adapter per request.
5. **No new wrong acceptances:** no more shaders that pass visible checks but fail
   confirmation than the base model.

The trained controller (track 2) is reported against the same criteria 1, 2, 4 and 5,
with its training compute stated against one seed-47 SFT run.

## Dependencies and blockers

- Fresh tasks: the v2 confirmation tasks are exposed, and the WGSL v3 populations and
  oracles are not materialized (see `SEMANTIC-EXPERIMENT-SCOPE.md`).
- Runtime: a per-sequence decode-transform path in Doppler, separate from the LoRA
  adapter guard. This is coordinated with A2, who owns the runtime and shader work.
- GPUs: Jupiter's driver needs a reset; the Mac and bee are busy (2026-11-12).
- Owner decisions: authorize the runtime path, task materialization and compute.
