# WGSL Repair and Writer Training Campaign

This directory holds the WGSL repair (V8 student replay, V9-V13) and WGSL writer
(v1-v3) training campaign, together with the host-teacher qualification and
student code experiment. It moved out of the Doppler runtime repository on
2026-10-29 at the owner's direction. Doppler keeps its runtime and the
`doppler-gpu/training` library surface. Gamma owns the campaign: corpus and
task construction, frozen policies, harness orchestration, evaluation,
selection, finalization, and receipts.

The campaign is historical evidence with frozen acceptance contracts. Moving it
authorizes no new training, evaluation, download, or promotion run.

## Layout and byte identity

`docs/`, `src/`, `tests/`, and `tools/` mirror Doppler's repository layout. Every
moved file is byte-identical to Doppler `53a5a2121a9d9dda31240693309caf9f80d6898a`.
This is required, not cosmetic: Doppler's frozen policies, receipts, and reports
pin the SHA-256 of 80 of the 81 moved tool and library files, and they address
inputs and outputs as Doppler repository paths (`tools/policies/...`,
`reports/training/...`, `src/experimental/training/...`).

Files added in Gamma rather than moved:

| File | Purpose |
| --- | --- |
| `namespace.js` | Builds the Doppler-namespace view described below. |
| `run.js` | Launches a campaign tool or the campaign tests inside that view. |
| `package.json` | Campaign scripts (formerly Doppler `training:wgsl:*`, `training:teachers:*`, `training:students:*`). |
| `src/config/schema/wgsl-campaign-policy-schema-registry.json` | The 20 policy-to-schema bindings removed from Doppler's `policy-schema-registry.json`. |
| `tools/check-wgsl-campaign-policy-schemas.js` | Validates those bindings with Doppler's entry rules. |

One receipt pair did not move: `docs/status/wgsl-writer-v2-result-2026-07-14.{json,md}`
stays in Doppler and is read through the namespace view. Its JSON records an
absolute local filesystem path, and the frozen
`tools/policies/wgsl-writer-v3-campaign-policy.json` pins its SHA-256, so it can
be neither copied into this public repository nor edited.

One moved test changed: `tests/training/wgsl-writer-v3-contract.test.js` now
checks the campaign registry instead of Doppler's registry.

## Running

```bash
cd projects/distillation/wgsl/campaign
export DOPPLER_ROOT=../../../../../doppler   # default: the sibling ../doppler of the Gamma checkout
node run.js --test                           # all campaign tests
node run.js --test tests/training/wgsl-repair-contract.test.js
node run.js tools/build-wgsl-writer-corpus.js --check
npm run training:wgsl:writer:corpus:check    # the same, through package.json
```

Each launch rebuilds `.namespace/` (gitignored) and prints a
`[campaign-namespace]` line to stderr with the Doppler and Gamma revisions in use.
In that directory:

- campaign files are hardlinked, so they keep their bytes and module paths;
- every other Doppler entry is a symlink into `DOPPLER_ROOT`;
- `.git` names Doppler's git directory, so read-only git calls in moved tools
  (`rev-parse HEAD` recorded as `dopplerCommit`, `show`, `cat-file`,
  `merge-base` against frozen base revisions) report Doppler identity rather
  than Gamma's.

The launcher fails closed if `DOPPLER_ROOT` is not a `doppler-gpu` checkout, or
if a path exists in both trees with different bytes. Outputs that tools write
under `reports/` or `artifacts/` land in the Doppler checkout, where the
campaign's existing evidence lives.

## Doppler internals

Moved code imports these Doppler modules by repository path (through the
namespace view). None of them are new Doppler exports. Symbols marked
"exported" are also reachable through a published `doppler-gpu` subpath, but the
pinned bytes import the internal path.

| Doppler module | Symbols | Published subpath |
| --- | --- | --- |
| `src/experimental/training/wgsl-repair.js` | WGSL repair tasks, mutations, reward vectors, rollout groups, DPO pairs, promotion decisions, artifact hashing/validation | none |
| `src/experimental/training/policy-artifacts.js` | `buildTrainingPolicyCheckpoint`, `buildTrainingPolicyUpdate` | none |
| `src/experimental/training/lora-pipeline.js` | `runLoraPipeline` | none |
| `src/experimental/training/suite.js` | `loadDistillModelHandle` | none |
| `src/experimental/training/datasets/teacher-traces.js` | `serializeTeacherTraceTextPairs` | none |
| `src/experimental/training/workloads.js` | `loadTrainingWorkloadCapsule` | exported: `./training` |
| `src/experimental/training/export.js` | `exportLoRAAdapter` | exported: `./training` |
| `src/experimental/adapters/lora-loader.js` | `loadLoRAFromManifest` | exported: `./orchestration` |
| `src/client/runtime/lora.js` | `activateLoRAFromTrainingOutputForPipeline`, `unloadLoRAAdapterForPipeline` | none |
| `src/config/runtime.js` | `getRuntimeConfig`, `setRuntimeConfig` | exported: `./tooling` |
| `src/inference/browser-harness-runtime-helpers.js` | `applyRuntimeProfile` | exported: `./tooling` |
| `src/memory/buffer-pool.js` | `destroyBufferPool` | exported: `./tooling` |
| `src/inference/test-harness.js` | `initializeInference` | none |
| `src/inference/pipelines/text/chat-format.js` | `formatChatMessages` | none |
| `src/gpu/device.js` | `destroyDevice`, `resetDeviceState` | none |
| `src/tooling/node-webgpu.js` | `bootstrapNodeWebGPU` | none |
| `src/tooling/node-file-fetch.js` | `installNodeFileFetchShim` | none |
| `src/tooling/node-browser-command-runner.js` | `createStaticFileServer` | none |
| `src/utils/sha256.js`, `src/utils/stable-sort-object.js` | hashing and stable key ordering | none |
| `src/formats/plain-object.js`, `src/formats/sha256.js`, `src/formats/stable-sort-object.js` | used by the moved `src/tooling/wgsl-repair-semantic-gate.js` | none |
| `tools/trainers/gamma-wgsl-trainer.js` | `runGammaWgslRequest`, `readGammaAdapterTensors`, `buildGammaProcessEnv` | none (Doppler tool) |
| `tools/node-test-file-bootstrap.js` | test bootstrap used by `run.js --test` | none (Doppler tool) |

`tools/trainers/gamma-wgsl-trainer.js` stays in Doppler: Doppler's workload
capsules under `src/experimental/training/workload-capsules/` name it as their
trainer module, and Doppler's Qwen-Gamma SFT parity oracles import it. It runs
this lane's `../training/train_wgsl.py`.

Moved policies and tests also read Doppler data by path: `reports/training/wgsl-*`
(131 files), workload capsules, kernel sources under `src/gpu/kernels/`, and
the conversion and kernel registries under `src/config/`. The browser tools
use Doppler's installed `playwright`.

## Large evidence

Large binaries stay out of Gamma, which has no Git LFS. The campaign references
them by Doppler repository path and SHA-256 only:

| Doppler path | SHA-256 | Size |
| --- | --- | --- |
| `artifacts/wgsl-repair/v12/external20/seed11/checkpoint-001200.adapters.safetensors` | `8631f512fe8ce481ade2e29a476bb1ade4e2ab6fd8627c7e27c7c093b4824af6` | 233 MB |
| `artifacts/wgsl-repair/v12/external20/seed29/checkpoint-001200.adapters.safetensors` | `0d9ab8e1348a3fcdd6ef2973b624cc1a3d962de90a571976a5a222df27b69394` | 233 MB |
| `artifacts/wgsl-repair/v12/external20/seed47/checkpoint-001200.adapters.safetensors` | `3e3895f062ae99d67c22ef3220a44ffe8081ba2021473de357e70216c50fd7d8` | 233 MB |

`models/adapters/wgsl-repair-qwen35-9b-v12/` (PEFT config and per-seed runtime
adapter manifests) also remains in Doppler.

## Known pre-existing test failures

At Doppler `53a5a212`, `tests/training/host-teacher-qualification.test.js` and
`tests/training/student-code-experiment.test.js` fail in some environments. They
fail identically from this directory. The first snapshots the Doppler checkout
into a temporary archive and needs free disk space for it. The second requires
`node_modules` in the Doppler checkout to be a real directory, not a symlink.
