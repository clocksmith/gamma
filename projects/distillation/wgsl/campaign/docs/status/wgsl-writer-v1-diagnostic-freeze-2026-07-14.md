# WGSL Writer v1 Zero-Shot Diagnostic Freeze

The reference mechanics passed and were committed in `bfd97ec1`. A separate
policy now permits one deterministic, zero-shot diagnostic submission from each
of two initializations:

1. the unchanged Qwen 3.5 9B F16 base; and
2. the same base with the V13 external20 seed-29 repair adapter active.

Both candidates receive byte-identical prompts containing only the natural
language specification and explicit interface contract. They use the same
greedy, no-chat-template generation settings and the exact same Doppler model
artifact. Each candidate may run once; retries, prompt changes, sampler changes,
and output filtering are forbidden.

The population remains the three visible mechanics-only tasks. Its authority is
`none`. The comparison asks only whether replacement-only adaptation transfers
zero-shot to complete-shader output. It cannot calibrate, select, confirm,
promote, or productize a writer, regardless of the result.

Canonical policy:
`tools/policies/wgsl-writer-v1-diagnostic-policy.json`.

After both completion receipts exist, the frozen semantic harness must compile
and dispatch them unchanged. The paired diagnostic receipt must preserve failed
outputs and report response-contract, compilation, semantic, bounds,
metamorphic, and regression outcomes for both initializations.
