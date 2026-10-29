# WGSL Repair V13 Seed Selection

V13 selected external20 seed 29 for a future, disjoint seed-confirmation
evaluation. This is checkpoint selection, not confirmation, promotion,
semantic capability proof, or WGSL Doctor authorization.

The selection policy, tasks, source hashes, adapter identities, generation
settings, and lexicographic ranking rule were committed and pushed at
`acb423da` before any adapter saw the checkpoint-selection prompts.

## Frozen execution

All candidates used the exact `qwen-3-5-9b-f16-af32` Doppler artifact with
manifest SHA-256
`2ff1f1eec0345bd379614b8b0bafd66957bbec1c22072132661a6e35300ad398`,
the production runtime profile, no chat template, greedy decoding, and a
64-token limit. Adapter manifests and 232,808,939-byte adapter weights were
verified before generation. The three exact manifests are tracked with these
receipts; the weight streams remain revision-pinned by the V12 preservation
manifest rather than duplicated in the report tree.

The six checkpoint-selection families were disjoint from mechanics
qualification, calibration, V12 training, V12 diagnostic, and V12 public
evaluation. Every completion was spliced into the broken shader and executed
through the V13 Chromium WebGPU dispatch, CPU-oracle, hash-binding, bounds,
shape, workgroup, metamorphic, and historical-regression checks.

## Result

| Rank | Seed | Semantic tasks | Compiler passes | Passing primary variants | Exact references |
|---:|---:|---:|---:|---:|---:|
| 1 | 29 | 4/6 | 6/6 | 13/18 | 4/6 |
| 2 | 11 | 1/6 | 4/6 | 4/18 | 1/6 |
| 3 | 47 | 1/6 | 4/6 | 4/18 | 1/6 |

Seed 29 repaired subtraction, square-plus-bias, absolute value, and pairwise
minimum semantically. Its `mix` completion used `0.0` instead of
`params.alpha`, and its threshold-negation completion used `0.0` instead of
`params.threshold`; both compiled but failed numerical oracles. This is direct
evidence that compilation alone is insufficient.

Seeds 11 and 47 tied on every scored metric. The precommitted lowest-seed
tie-break ranked seed 11 second. No post-hoc metric or task was introduced.

The canonical selection receipt is
`wgsl-repair-v13-seed-selection-2026-07-14.json` with file SHA-256
`8f33d219a6a757e19e22beb2d809b9f9a2770aaf3d563da541c26d0b67b701ef`.
It binds all candidate completion and semantic dispatch receipts under
`reports/training/wgsl-repair/doppler-wgsl-repair-v13/checkpoint-selection/`.

## Current boundary

The post-selection readiness receipt is
`wgsl-repair-v13-semantic-readiness-post-selection-2026-07-14.json`.
It verifies the seed-29 selection receipt and removes
`external20_seed_checkpoint_not_selected`.

The remaining blockers are the unmaterialized seed-confirmation and one-use
promotion populations. `seedConfirmationAllowed`,
`promotionEvaluationAllowed`, `semanticClaimAllowed`, `wgslDoctorAllowed`, and
`autonomousShaderAuthorAllowed` remain false. The selection population is now
spent for ranking and cannot be reused as confirmation evidence.

The result is also narrow: these are six constructed replacement-only repair
tasks. It does not establish performance on naturally occurring WGSL errors,
complete shader generation, cross-platform execution, or deployment.
