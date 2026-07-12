# WGSL Verifier-Guided Training

This project is Gamma's optimization plane for the Doppler WGSL repair
program. Doppler owns task construction, source and license lineage, WebGPU
compilation and regression verification, reward vectors, rollout-group
receipts, and promotion decisions. Gamma owns model loading, completion-masked
SFT, DPO, sampled rollout log-probabilities, and GRPO-style policy updates.

The protocol is JSON and fail-closed:

```bash
python projects/distillation/wgsl/training/train_wgsl.py \
  --request request.json \
  --response response.json
```

Supported actions are `preflight`, `sft`, `dpo`, `rollout`, and
`grpo_update`. Every request must name a local or locally cached model. The
trainer passes `local_files_only=True`; it never downloads model weights.
Rollout accepts either an `adapterPath` or an explicit base-policy request with
`policyMode: "base"` and a frozen `policyHash`. This keeps base and adapted
pass-rate receipts on the same generation and verifier path.
Grouped rollout writes `rollout-state.json` before generation and appends one
complete task group at a time. A matching request resumes that verified prefix;
a changed model, policy, dataset, sampling, or training contract fails closed
instead of mixing samples.
Generation disables gradient checkpointing and enables the model KV cache;
training keeps checkpointing enabled and the cache disabled.
Grouped sampling runs all declared samples in one model batch while preserving
an independent frozen RNG seed per row after temperature and top-p filtering.
Policy and reference token log-probabilities are collected in a bounded batch,
with token-mask alignment checked by Doppler before optimizer use.
GRPO excludes zero-advantage samples from optimizer input, then applies the
declared training seed to a deterministic shuffle before its microstep budget
is consumed. This enforces the declared `zero_advantages` behavior and prevents
task ordering from silently excluding late mixed-reward groups. Gradients are
accumulated against the rollout policy and applied in exactly one optimizer
update; requests other than one update per rollout batch with zero stale-policy
updates fail closed. The response records the ordering rule, signal sample
count, microsteps, optimizer steps, and stale-policy contract.
DPO treats completions as exact code artifacts: it preserves leading/trailing
whitespace and permits empty or whitespace-only rejected samples instead of
normalizing away verifier-observed failures. The frozen base-policy
chosen/rejected sequence scores are cached once per pair; trainable-policy
scores remain current on every optimizer update.

The primary V9 student is `Qwen/Qwen3.5-9B`. `Qwen/Qwen3.5-2B` is an
efficiency control, not a gate on the 9B lane. The already provisioned
`Qwen/Qwen3.6-27B` snapshot is a teacher and ceiling, not a silent replacement
student.

The ROCm contract was exercised with Torch `2.12.1+rocm7.2`, HIP
`7.2.53211`, Transformers `5.13.1`, and BF16 on Radeon 8060S. The provisioned
Qwen 3.6 27B snapshot passes model/runtime preflight. Qwen 3.5 9B at exact
revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` is now operator-provisioned
and also passes model/runtime preflight.

A one-step Gemma 3 270M fixture executed SFT, grouped rollout, DPO, and GRPO
only to validate mechanics. Its sampled repairs produced zero compiler passes,
and it is excluded from every V9 capability comparison.

The first prepared Doppler corpus is compiler-reproducing replacement repair.
It establishes a training substrate, not a semantic-kernel capability claim.
Promotion remains dependent on Doppler's sealed semantic repair suite and the
frozen multi-seed policy.
