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

The primary V9 student is `Qwen/Qwen3.5-9B`. `Qwen/Qwen3.5-2B` is an
efficiency control, not a gate on the 9B lane. The already provisioned
`Qwen/Qwen3.6-27B` snapshot is a teacher and ceiling, not a silent replacement
student.

The ROCm contract was exercised with Torch `2.12.1+rocm7.2`, HIP
`7.2.53211`, Transformers `5.13.1`, and BF16 on Radeon 8060S. The provisioned
Qwen 3.6 27B snapshot passes model/runtime preflight. Qwen 3.5 9B currently
fails closed as `model_not_provisioned`.

A one-step Gemma 3 270M fixture executed SFT, grouped rollout, DPO, and GRPO
only to validate mechanics. Its sampled repairs produced zero compiler passes,
and it is excluded from every V9 capability comparison.

The first prepared Doppler corpus is compiler-reproducing replacement repair.
It establishes a training substrate, not a semantic-kernel capability claim.
Promotion remains dependent on Doppler's sealed semantic repair suite and the
frozen multi-seed policy.
