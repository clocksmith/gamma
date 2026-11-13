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

- transform only the MLP and output projections, so cached keys and values stay
  consistent;
- transform all projections and keep the base KV cache (the hybrid), with the
  divergence measured directly;
- re-prefill with the transformed weights (exact, at roughly double the prefill
  cost).

## Controls and comparisons (matched budgets)

- the base model, given the transform's extra compute as more samples (best-of-k);
- the trained WGSL v2 adapter (seed 47) as the reference ceiling;
- the same rule fed shuffled or unrelated context, and a random `z` of the same size,
  to show whether the prompt matters at all;
- end-to-end timing in every arm: prefill, time to compute `z`, decode tokens per
  second and memory.

## Metric

Semantic pass on fresh, family-disjoint executable shader tasks: compilation,
dispatch, CPU-oracle agreement, canaries, workgroup and shape variations,
permutations, one submission per task. Compiler acceptance alone counts for nothing.
No synthetic training data is needed for the primary track; independent tests are
still required.

**Interesting result:** a no-training rule that beats its shuffled-context and
random-`z` controls, and closes a stated fraction of the gap from base to adapter at
a small fraction of the adapter's setup cost.

## Dependencies and blockers

- Fresh tasks: the v2 confirmation tasks are exposed, and the WGSL v3 populations and
  oracles are not materialized (see `SEMANTIC-EXPERIMENT-SCOPE.md`).
- Runtime: a per-sequence decode-transform path in Doppler, separate from the LoRA
  adapter guard. This is coordinated with A2, who owns the runtime and shader work.
- GPUs: Jupiter's driver needs a reset; the Mac and bee are busy (2026-11-12).
- Owner decisions: authorize the runtime path, task materialization and compute.
