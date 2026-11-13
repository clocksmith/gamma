# First prefill channel-gain experiment

Status: **implementation and reference qualification; model experiment not run**.
The scope is the owner's first analytical MLP rule only. No new training, attention
projection gains, low-rank transforms, rotations or trained controller are included.
A2 coordination was waived by the owner; live GPU services remain protected.

## Frozen protocol and corpus

[protocol.json](protocol.json) records the numeric decision rule, two candidate
settings (beta +0.05/-0.05, clip 1, epsilon 1e-6, reference A, layers 30/31),
2/4/16 smoke/selection/confirmation families, sampling settings and controls.
[protocol-freeze.json](protocol-freeze.json) binds its raw bytes and task sources
before materialization. [corpus-v1/manifest.json](corpus-v1/manifest.json) binds
all materialized prompts, public/held-out checks, references and source provenance.
No selected candidate or generated-submission confirmation lock exists yet.

Each task/control must reuse the identical frozen gain bytes in MLP/base-cache and
MLP/re-prefill. All-projections is **not applicable**, not passed or failed.
The controls are base, compute-matched public-check-selected best-of-k,
shuffled-context, random-z, permuted-gain and the trained seed-47 adapter.
Confirmation outcomes cannot choose candidates or best-of-k submissions.

The exposure audit distinguishes all 22 constructed scalar expressions against
24 historical families at its tested inputs. It does not prove external novelty
or independence for generic WGSL programming. This remains the scoped elementwise
shader testbed, not a general shader-writing claim.

## What exists

- `rule.py`: analytical gains and deterministic shuffled, random and permuted controls.
- `torch_hooks.py`: optional unfused research reference; not Doppler serving-cost evidence.
- `token_contract.mjs`: exact content/instruction token boundaries; rejects merges
  crossing declared boundaries rather than guessing offsets.
- `tasks.mjs`, `exposure_audit.mjs`: new tasks, CPU oracles and exposure audit.
- `isolated_namespace.mjs`: imports unchanged campaign prompt/parser/verifier modules
  in a private namespace. Shared `campaign/.namespace` is never rebuilt.
- `materialize_tasks.mjs`, `run_verifier.mjs`: hash-checked materialization and
  executable reference/public/confirmation verification. Public verification
  reads only public checks. Confirmation requires locked source hashes and a
  write-once per-arm started marker before opening held-out checks.
- `decision.py`, `evaluate.py`: public sample selection, write-once submission
  locks, exact sign test, gap closure, overhead/budget/acceptance decision arithmetic.
  The reducer assumes authenticated run receipts; fixture inputs are not evidence.
- Doppler owns the native f32 SwiGLU gain multiply, exact-span energy reduction,
  GPU gain derivation and request lifecycle. Its separate receipt establishes
  toy-kernel arithmetic, not full model integration or serving qualification.

## What ran

[reference-qualification-summary.json](reference-qualification-summary.json)
records **22/22 reference shaders and 286/286 checks passed** on Apple Metal.
The reference verifier intervals were 285.040 ms (2 smoke references), 294.881 ms
(4 selection references), and 1015.916 ms (16 confirmation references). Executing
known reference shaders on held-out inputs qualifies the oracle; it is not generated
model-output confirmation. The immutable materialization manifest deliberately
retains its initial `referenceQualified: false`; the linked later receipts hold
qualification status rather than rewriting a frozen manifest.

Focused CPU validation: 17 Python and 14 Node tests passed. The combined checks
cover gain math, hook cleanup, controls, token spans, oracle mechanics, lock binding,
public-only selection and rejection of incomplete/mismatched evidence.

**Zero model requests, zero selected candidates, zero generated-output confirmation
checks, zero training steps.** No model smoke timing exists, so no measured inference
ETA can be reported. Reference dispatch timing cannot substitute for it. Cache
behavior, trained-adapter results, semantic gain and end-to-end overhead are unknown.

## Execution blockers and remaining work

[preflight-receipt.json](preflight-receipt.json) records the live checks at
2026-11-13 02:02 UTC:

1. Jupiter's exclusive GPU timing lock returns 1 while its 27B serving provider is
   active. No process was stopped, reset or reconfigured. Flash-Next GPU work had
   finished, but the provider remains. The model experiment needs a safe device
   allocation; the small Mac shader tests did not load model weights.
2. The exact provisioned Qwen3.5-9B HF snapshot exists on Jupiter, but the pinned
   native `qwen-3-5-9b-f16-af32` RDRR model is absent from the checked model stores.
   No replacement model or quantization was substituted, and no weights downloaded.
   The historical Python runtime is also gone; Gamma's current Jupiter interpreter
   fails `import torch`. A Python fallback cannot establish fused Doppler overhead.
3. Seed-47 adapter weights were verified as SHA-256
   `64cb65bfd2f409278d666d874c4dc2179058cab8e75609f5fe1fdc8644794667`
   (232,821,904 bytes). Historical receipts contain wall timestamps spanning
   3576.012 s, but no explicit GPU-hours counter. That interval is not silently
   substituted for the required recorded SFT GPU-hours selection budget.
4. The end-to-end model driver still needs the verified loaded native model,
   control construction/upload, paired cache lifecycle, per-layer KV and recurrent
   state comparison at an identical forced prefix, sampling and timing wiring.
   Native primitives and verifier commands alone are not a completed experiment.

Once those boundaries are resolved: bind runtime/model/adapter artifacts, run the
fixed two-task model smoke across arms without tuning, report measured request times
and a grounded remaining-request ETA, enforce the selection budget, freeze the chosen
candidate and submitted sources, then run confirmation once. Incomplete candidates
are untested; missing/underpowered comparisons cannot be reported as confirmation.

## Commands

From Gamma, CPU checks:

```sh
.venv/bin/python -m unittest projects.distillation.wgsl.channel_gain.test_rule projects.distillation.wgsl.channel_gain.test_torch_hooks projects.distillation.wgsl.channel_gain.test_decision projects.distillation.wgsl.channel_gain.test_evaluate
node --test projects/distillation/wgsl/channel_gain/test_tasks.mjs projects/distillation/wgsl/channel_gain/test_verify_shaders.mjs projects/distillation/wgsl/channel_gain/test_token_contract.mjs
```

The corpus already exists. Do not regenerate it or rerun freeze commands over it.
`materialize_tasks.mjs` and `freeze_protocol.mjs` use exclusive file creation.
Verifier commands used for the reference checks are recorded in the qualification
summary. Generated public checks take `--scope public --submissions FILE`, where
FILE is `{ "arm": "...", "sources": { "taskId": "WGSL source" } }`.
Generated confirmation additionally requires `--lock FILE --selection-sha256 HASH`.
No model experiment launch command is claimed until the model-driver boundary above
is implemented and verified.
