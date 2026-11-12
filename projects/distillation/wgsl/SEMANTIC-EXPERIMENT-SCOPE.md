# WGSL semantic experiment: SFT vs inference-time search vs GRPO (scope, not authorized)

Scope drafted 2026-11-12 by A1 at the owner's direction. It authorizes no
materialization, training, evaluation, download or promotion run. SAME-R
(`projects/samer`) is the comparison protocol; it is not one of the arms.

## Starting point (evidence, not claims beyond it)

- WGSL Writer v2 (Doppler `docs/status/wgsl-writer-v2-result-2026-07-14.md`):
  three Qwen 3.5 9B rank-32 LoRA seeds, one greedy submission per role,
  blocking Chromium WebGPU compilation, dispatch, CPU-oracle agreement, bounds
  canaries, workgroup/shape variation and input permutations. Seed confirmation
  16/16, 15/16, 15/16 on a constructed, family-disjoint population of 1-D
  elementwise f32 compute shaders; selected seed 47 has exact PEFT/Doppler
  completion parity (247/247 tokens). Not external promotion, not general WGSL.
- Writer v3 (`campaign/tools/policies/wgsl-writer-v3-campaign-policy.json`) is
  frozen with status `developmental_policies_reconciled_prospective_materialization_blocked`;
  its next valid transition is `frozen -> materialized`. Recorded blockers:
  no immutable external URL for the selected v2 weights; executable CPU and
  raster oracles not materialized; depth/stencil/blend/indirect/query contracts
  not represented; mipmapped and multisampled resources unsupported; development
  and external promotion populations not materialized.
- Compiler-repair GRPO (V11) improved compile pass@1 88.29% -> 94.98% with one
  update and one seed; compilation is not semantic correctness, and the
  matched DPO lane collapsed (36.79%).

## Question

Within one declared shader family set, does GRPO or inference-time search add
semantically correct shaders over the SFT adapter, under matched budgets, on a
fresh family-disjoint population, without new wrong acceptances?

## Proposed contract (to freeze before any run)

- **Capability scope:** start from v2's executable scope (compute shaders with
  CPU oracles) and add only families whose oracles exist; graphics-pipeline
  contracts (depth/stencil/blend, mipmaps, multisampling) stay out until their
  oracles are materialized.
- **Populations:** new family-disjoint training, selection and confirmation
  populations plus an externally custodied one-use promotion set, materialized
  under v3's `frozen -> materialized` rules (custody, exposure registration,
  duplicate and connected-component checks) before any arm runs.
- **Arms (same base, same tokenizer, same data):**
  1. SFT: the v2 recipe on the new training population.
  2. Inference-time search: the SFT adapter samples k candidates per task;
     candidates are filtered and ranked using only the task's public
     checks; one submission per task.
  3. GRPO: initialized from the SFT adapter; groups of sampled shaders per
     training task; reward from the semantic harness on training-visible
     checks (compile and dispatch are gates, CPU-oracle agreement is the
     reward; efficiency terms only after correctness); KL to the SFT
     reference; clipped updates.
  4. Controls: the base model with the same search budget, and an SFT
     continuation with GRPO's extra update compute (the equal-budget
     supervised-only control).
- **Matched budgets:** training compute (GPU-hours and optimizer steps) and
  inference compute (samples and verifier executions per task) are declared and
  equal per arm; any unequal arm is reported as such, never compared silently.
- **Metric:** semantic pass on the confirmation population (compilation,
  dispatch, CPU-oracle agreement, canaries, variations, permutations), one
  submission per task. Compiler acceptance alone counts for nothing.
  Guardrails: wrong acceptances (shaders passing visible checks but failing
  confirmation), regressions against SFT, parity of the selected adapter in
  Doppler.
- **Replication:** three seeds per training arm; selection and confirmation
  use separate populations; the promotion set is opened once, after the
  candidate is frozen.

## Dependencies and blockers

- Population and oracle materialization (v3 blockers above) comes first.
- GPU hosts: Jupiter's GPU driver is wedged until a sudo reset; the Mac and
  bee GPUs are busy with scoreboard runs (A2, 2026-11-12). Runtime, Doe/Dawn
  adapter parity and Doppler execution are coordinated with A2, not duplicated.
- Owner decisions: authorize materialization, the training compute, and the
  promotion-set custody.
