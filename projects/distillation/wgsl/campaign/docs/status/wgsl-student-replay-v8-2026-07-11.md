# WGSL Student Replay v8 Evidence Receipt

## Decision

Run `doppler-js-wgsl-2026-07-11-v8` is terminally `rejected` at the capability
gate. Its WGSL mechanics subreceipt remains valid: execution-qualified teacher
repairs drove completion-masked LoRA training, changed every adapter tensor,
reduced learning-receipt loss, and produced a checksummed adapter.

The frozen held-out replay then measured no WGSL improvement. Baseline and
adapter both passed 0 of 6 replays, and the adapter produced 30 policy
violations from wrapped or invalid edit records. The preregistered mixed
candidate also failed its learning receipt before replay because its loss
regressed. `controlProven` is false, all challengers remain blocked, and no
model, adapter, release, or demo tier is promoted.

V8 is execution-verified SFT, not RLVR, GRPO, or logit KD.

The compact machine-readable terminal receipt is
[`wgsl-student-replay-v8-2026-07-11.json`](wgsl-student-replay-v8-2026-07-11.json).

## Run Identity

- Run root:
  `reports/training/student-code-replay/doppler-js-wgsl-2026-07-11-v8`
- Final repository revision recorded by the run:
  `1c9c0850b5efe8c342baeec3eae26c471656e7f6`
- The WGSL training result was produced while HEAD still named
  `cf1a9a38b26f25363ffc297a07877dd46fdd01cb`; the policy, task-bank, and
  harness hashes bind the exact bytes, which were committed in the final
  revision above.
- Base model: `gemma-3-270m-it-f16-af32`
- Teacher qualification run:
  `reports/training/teacher-qualification/doppler-js-wgsl-2026-07-11-v4`
- Qualified teacher: `gpt-5.6-sol` through `codex-cli 0.144.1`
- Teacher labels: 10 accepted, split as 6 JavaScript and 4 WGSL
- WGSL dataset: 4 source repairs materialized into 8 text-pair rows
- WGSL dataset SHA-256:
  `5520bfec792121714f5e83e968c4a640a995599fa41d0739bfd9aa766d90702b`
- Objective: completion-only causal-LM cross-entropy
- Student seed: `1337`
- Optimizer: AdamW, learning rate `0.0001`, no weight decay
- Adapter: rank 4, alpha 8, `q_proj` and `v_proj`, frozen base
- Training: 8 steps, batch size 1, F16 activations/gradients, F32 LoRA
- Experiment policy SHA-256:
  `7117bcb0ea365872d80065459f2015ae654099cb05c4de0a480aea7531a0593b`
- Training harness SHA-256:
  `41edacdff8a36657c157e19ca71b4d81b2734f46d8a2141b50f99c7bf477348b`

## Learning Receipt

| Gate | Result |
| --- | ---: |
| Expected/observed steps | 8 / 8 |
| Steps with nonzero gradients | 8 / 8 |
| Parameterized steps | 8 / 8 |
| Adapter tensors changed | 72 / 72 |
| Adapter tensors nonzero after training | 72 / 72 |
| Aggregate adapter L2 delta | 0.23221625547152977 |
| Base completion loss | 1.7594943249029105 |
| Adapter completion loss | 1.7594215848313548 |
| Absolute loss improvement | 0.00007274007155566586 |

The exported checkpoint is `checkpoint-000008`. Its safetensors artifact is
743,652 bytes with SHA-256
`15f2697050b3c52d5e1937a842ea2411dc2907a63875d9d3a6e47be9af4ba9d7`.

The canonical local evidence artifact is:

```text
reports/training/student-code-replay/doppler-js-wgsl-2026-07-11-v8/
  training/wgsl/student-training-result.json
```

Its SHA-256 is
`c83ebc03ab960855c6be3e502980bd38ef45bd2ac5f137900843c73056d68ea0`.

## Frozen Held-Out Replay

The policy evaluated two `student_holdout` WGSL tasks three times each with
greedy deterministic decoding.

| Gate | Baseline | WGSL adapter |
| --- | ---: | ---: |
| Tasks | 2 | 2 |
| Replays | 6 | 6 |
| Constructive passes | 0 | 0 |
| Constructive pass rate | 0.000 | 0.000 |
| Applicable patches | 0 | 0 |
| Validation passes | 0 | 0 |
| Policy violations | 30 | 30 |
| Deterministic tasks | 2 / 2 | 2 / 2 |

The adapter outputs parsed as JSON but violated the required response
contract. The observed failure classes were `output_wrapper`,
`invalid_edit_record`, `invalid_edit_keys`, and `changed_paths_mismatch`.
Because the candidate pass rate did not strictly exceed baseline and policy
violations were nonzero, the WGSL lane failed its frozen gate.

Artifact hashes:

- Baseline receipts:
  `6f3e5e057b1289c288a6fd81f330af3a0f2e807de08661d093a1cf03596485da`
- WGSL adapter receipts:
  `6b054f7a0439307b409255c2b16a807f8583d1dc0da87e7561efbb7053d53da5`
- Final report:
  `3655c5e674ca74c52ef0bc6f2deffa21c255068714d8e4241df4e1c973d5622f`
- Redacted failure-only queue:
  `e4097a485489f257037c98c47b240faf16253d0e0d77f04f0b955120fa6739a6`

## Mixed Control Candidate

The mixed lane was preregistered before held-out evaluation and remained the
only candidate that could still satisfy both required language lanes after the
specialized WGSL failure. It used 8 source rows, balanced as 4 JavaScript and 4
WGSL, materialized over two dataset passes into 16 training rows.

| Learning gate | Result |
| --- | ---: |
| Expected/observed steps | 16 / 16 |
| Steps with nonzero gradients | 16 / 16 |
| Parameterized steps | 16 / 16 |
| Adapter tensors changed | 72 / 72 |
| Adapter tensors nonzero after training | 72 / 72 |
| Aggregate adapter L2 delta | 0.4372571839979604 |
| Base completion loss | 1.7467704704098914 |
| Adapter completion loss | 1.7469165558029276 |
| Absolute loss improvement | -0.00014608539303617718 |

The loss gate failed. The exported bytes with SHA-256
`92d00840cc9261184a61166ebefca5250e7684ca96b5c5645afe5583a7a119a2`
remain a rejected artifact; they were not added to `adapter-index.json` and
were not replayed. The mixed training-result SHA-256 is
`c65d357b175c1eb708d8a1d432f45e56cb6e0d78ec5fe85bc06c5770e0ff980d`.

The JavaScript specialist was not trained. Once the specialized WGSL lane
failed, a JavaScript-only result could not make the specialized candidate
eligible, so running it would not change the terminal policy decision.

## Evidence Reset

Earlier optimizer evidence is excluded from this chain. Recycled buffer bytes
could reach newly allocated Adam moments before the runtime explicitly zeroed
them. The repaired path uploads zero-filled state for both moment buffers and
uses logical tensor element counts in immediate and recorded Adam dispatches.

The regressions are:

- `tests/training/runtime-cleanup.test.js`, which poisons released pool buffers
  and requires new Adam moments to contain zeros; and
- `tests/gpu/adam-logical-shape-contract.test.js`, which requires both Adam
  paths to ignore pooled bucket padding.

The v8 receipt comes from a separate run root with freshly initialized
optimizer state. No result from the contaminated run is part of the promotion
evidence.

## What This Establishes

- Accepted WGSL repairs preserve teacher and policy lineage.
- Prompt tokens are excluded from the completion loss.
- The intended eight optimizer steps execute.
- Gradients are nonzero on every step.
- Every declared LoRA tensor changes and finishes nonzero.
- The adapter reduces token-weighted completion loss on the learning-receipt
  rows.
- A checksummed external safetensors adapter is emitted.
- The trained adapter does not improve the frozen WGSL constructive pass rate.
- The primary observed failure is response-contract adherence before patch
  execution, not a passed patch with a failed kernel check.
- The mixed candidate changes weights but fails its declared loss gate.
- The frozen policy rejects both available control paths without changing its
  thresholds after observing results.

## Final Claim Boundary

- `controlProven` is not established.
- No policy-required lane matrix has passed.
- No model, adapter, package release, or demo tier is promoted.
- Larger Qwen and Gemma challengers remain `blocked_until_control_proven`.
- No on-policy rollout, reward vector, advantage, or policy-gradient receipt
  exists, so this run is not RLVR.

## Next Experiment

1. Treat v8 as a negative result; do not resume or promote either adapter.
2. Use only the redacted failure-only queue. Do not expose holdout prompts,
   paths, outputs, or recovery edits to the next training set.
3. Add generic response-contract demonstrations and rejection examples for
   unwrapped `{ "edits": [...] }` output, exact edit keys, and allowed-path
   discipline.
4. Preserve a random/control data lane so any improvement can be attributed to
   the response-contract curriculum rather than row count alone.
5. Freeze a new policy ID, run root, and sealed WGSL holdout bank before the
   next capability claim; v8's evaluated tasks are no longer a fresh sealed
   test for a data lane designed from its failure signals.
6. Keep RLVR as a separate experiment after the rollout runtime can emit the
   artifacts in [the RLVR contract](../rlvr-training-contract.md).
