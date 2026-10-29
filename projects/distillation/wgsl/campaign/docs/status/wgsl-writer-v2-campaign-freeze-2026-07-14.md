# WGSL writer v2 campaign freeze (2026-07-14)

## Decision

The v2 development campaign is frozen and admitted to training. It targets one
narrow capability: authoring a complete 1-D elementwise f32 WGSL compute shader
from a natural-language operation specification and an explicit interface
contract. It is not a general WGSL writer experiment.

The v1 mechanics population remains excluded from every v2 scientific role.
The v1 zero-shot result remains a rejection: neither the unchanged Qwen 3.5 9B
base nor the V13 replacement-repair adapter wrote a passing full shader on the
visible mechanics tasks.

## Frozen data contract

- Construction policy: `tools/policies/wgsl-writer-v2-corpus-policy.json`
  (`560bccb7269f1dae5b8d426bb90414097eb82e1b5f4fdaee211daa6498522c44`)
- Blueprint catalog: `tools/data/wgsl-writer-v2-blueprints.json`
  (`85ff008bbdfb86800296e08779186d0f23d938e8cf5c3418f9b5127d448dfc61`)
- Corpus manifest:
  `reports/training/wgsl-writer/doppler-wgsl-writer-v2/corpus-v1/corpus-manifest.json`
  (`dc507148075cff97d1faf05c848c471f97b33dacd88905bd31a81e45b01f528c`)
- Training dataset: 720 rows, 15 semantic families
  (`8e50b9fe9efa5c59ebd922ba51b6bbbb0d84b6643b53038ad5b5740431d2a8e7`)
- Calibration: 16 rows, two held-out semantic families
- Checkpoint selection: 16 rows, two further held-out semantic families
- Seed confirmation: 16 rows, two further held-out semantic families
- Semantic-family overlap across roles: zero
- Duplicate row IDs: zero
- Duplicate prompts: zero
- Visible mechanics tasks used for training: false

The generated rows and shaders are Doppler-owned Apache-2.0 parametric
blueprints. They do not incorporate Zero-TVM or another external source and do
not support a data-curation attribution claim.

## Reference qualification

The blocking reference receipt is
`reports/training/wgsl-writer/doppler-wgsl-writer-v2/corpus-v1/reference-qualification.json`
(`3230d5b58bad1f3eb07f9add7b0c38088cab75d6c98ede1c5a5ebe728d99a664`).

- All 768 materialized target shaders compiled in Chromium WebGPU.
- All 63 semantic reference tasks passed.
- All 189 primary shape variants passed.
- Each variant also passed alternate-workgroup and input-permutation dispatch.
- Bounds canaries, output padding, read-only inputs, CPU-oracle agreement, and
  historical logical-shape regressions passed.

This receipt admits training. It contains no model output and establishes no
writer capability.

## Frozen training contract

`tools/policies/wgsl-writer-v2-training-policy.json`
(`a8b58555edbcefa88f0b6e769a1a3c35bf2f55c943b4ef4208b64e1b3daff06e`)
freezes three independent base-model initializations at seeds 11, 29, and 47.
Each run consumes all 720 training rows exactly once in seed-hash order and
trains a rank-32 LoRA over the Qwen 3.5 9B attention and MLP projections.

Generation is frozen to greedy decoding with a 384-token ceiling. The ceiling
comes only from training targets: the longest target is 263 tokens including
EOS, the longest joined prompt and target is 924 tokens, and no held-out result
informed the limit.

Calibration cannot select a checkpoint. Checkpoint selection receives one
submission per seed. Seed confirmation opens only after selection. The exact
selected adapter must then pass Gamma-to-Doppler prompt, first-token-logit,
selected-token, and completion parity.

## Remaining boundary

Promotion is intentionally unmaterialized. A one-use promotion population must
come from an external custodian; the training operator cannot author, inspect,
and later call the same rows sealed. Until that population and exact Doppler
artifact pass, v2 cannot authorize a general WGSL-writer claim or productization.
