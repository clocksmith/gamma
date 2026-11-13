# First prefill channel-gain experiment

Status at 2026-11-13 03:09 UTC: **native smoke attempt 03 running; no confirmation**.
The current machine-readable state is [execution-status.json](execution-status.json).
The scope remains the first analytical MLP rule: no training, attention gains,
other transform families, or trained controller.

## Protocol and evidence boundaries

[protocol.json](protocol.json) fixes the numerical criteria, beta ±0.05 candidates,
clip 1, epsilon 1e-6, reference A, layers 30/31, 2/4/16 family splits and generation
settings. [protocol-freeze.json](protocol-freeze.json) binds those bytes and task
sources before [corpus materialization](corpus-v1/manifest.json).

[Amendment 01](protocol-amendment-01.json), recorded before the first model request,
removes the author's extra requirement to charge fixed smoke work to candidate
selection. The owner's numerical 1% criterion is unchanged: all work used to select
settings is charged; smoke and confirmation are separately reported and cannot rank
candidates. Smoke uses the first frozen candidate deterministically, without tuning.

Each task/control reuses identical immutable gains in MLP/base-cache and
MLP/re-prefill. All-projections is **not applicable**, neither passed nor failed.
Controls are base, public-check-selected best-of-k, shuffled-context, random-z,
permuted-gain and the trained seed-47 adapter. Candidate ranking uses complete
selection-family semantic checks. Confirmation-family checks never rank anything.

The exposure audit distinguishes the 22 constructed scalar expressions against
24 historical families at its tested inputs. It does not establish external novelty
or generic WGSL independence. This remains an elementwise-shader study.

## What ran

- [Reference qualification](reference-qualification-summary.json): 22/22 reference
  shaders and 286/286 checks passed on Apple Metal. Verifier intervals were
  285.040, 294.881 and 1015.916 ms. These are reference checks, not model confirmation.
- [Native artifact preflight](native-artifact-preflight.json): all 267 shards
  (17.91 GB) verified, 19,261 scalar samples across all 427 text tensors matched
  source-to-F16 conversion, and all architecture/attention-pattern checks passed.
- Doppler native GPU tests passed on Apple M3 and Jupiter's Radeon 8060S, including
  actual dense-FFN capture/application, both beta signs, controls, immutable gain
  ownership, reset and frozen-state sharing. These are toy operator tests.
- [Attempt 01](native-smoke-01.jsonl): cold model load 60.750 s, adapter preparation
  0.302 s. The first base request generated 273 tokens in 92.660 s end-to-end and
  failed its public contract (`WORKGROUP_SIZE` override missing). Transform capture
  then failed because the scoped pipeline lacked the new method registration.
- [Repair record](runtime-repair-01.json): Doppler `d8806094` fixes registration;
  `79ce17bc` adds exact private-buffer allocation metadata. Gamma now destroys its
  owned device before releasing the host and closes independent resources on error.
  Attempt 01 sources are preserved under [attempt-01-sources](attempt-01-sources/).
- [Runtime lock 02](native-runtime-lock-02.json) binds the repaired driver, native
  sources, model and adapter before retry. It records the one previously observed
  model request. No candidate has been selected and no confirmation has run.

- [Attempt 02](native-smoke-02.jsonl): nine requests completed on the first smoke
  task, all failing the public contract. Same-gain cache arms were measured; the
  layer-31 KV and logits differed under the same forced prefix. The trained adapter
  then failed at a combined query/gate projection shape mismatch. The owned runtime
  unloaded cleanly; the provider stayed active. [Repair 02](runtime-repair-02.json)
  preserves the failure, source snapshot, timing and Doppler `64834f4b` fix.
- [Adapter integration probe](adapter-probe-03.json): four unscored tokens completed
  through the repaired prefill/decode path in 75.694 seconds including model load.
  This is a geometry diagnostic, not a shader comparison or confirmation.
- [Runtime lock 03](native-runtime-lock-03.json) starts a complete smoke rerun, with
  request cleanup and the entire verifier call included in timing. A separately
  timed reset diagnostic compares original base-prefill logits after all gains are
  discarded. Criteria, candidates, splits and sampling settings are unchanged.

Focused validation: 17 original Python tests, 14 original Node tests, and 13 native
orchestration/memory/selection tests passed; see [driver validation](runtime-02-cpu-receipt.json).
A failed model shader is a task outcome; the subsequent integration failure is not
an outcome for or against the gain rule. No transformed-model improvement is claimed.

## Runtime, timing and budget

The exact provisioned Qwen3.5-9B revision was converted in an isolated Jupiter
execution directory, using the checked-in F16/F32 recipe. Source weights were not
downloaded. The existing dirty Doppler checkout and live services were not changed.
All arms use the same explicit split-F32 execution overlay in
[native-jupiter-config.json](native-jupiter-config.json).

Jupiter's provider remains active. A separate read-only [service guard](service_guard.py)
checks service status, admission count, observation freshness and 32 GiB available
RAM. The model driver checks admission before requests and every decoded token.
No provider process is stopped or reset. Attempt 01's already-failed experiment
process alone was terminated after its missing device teardown left it alive.

[Selection-budget provenance](selection-budget-receipt.json) establishes a
conservative 3,559-second single-GPU residency lower bound from original metric
inode timestamps and retained training code. Its 1% cap is **35.59 GPU-seconds**.
This is derived allocated residency, not a GPU active-time meter. The old outer
3,576.012-second wall interval is not used as an exact GPU-time denominator.

No full-smoke ETA exists yet. One base timing cannot establish all-control throughput.
After the two-task smoke, the runner reports measured request timings, cold load,
cache-diagnostic cost and an ETA derived from the remaining frozen request count.
Selection admission compares the complete eight-request workload to the cap before
loading another model. If it cannot fit, all unexplored candidates remain untested
and confirmation is not admitted. The cap is not expanded to force a result.

Memory reports distinguish exact logical/allocated gains, baseline-subtracted owned
snapshots, extra re-prefill storage, preparation ownership and complete model-device
GPUBuffer live/process-lifetime peak counters. Process-lifetime peak is not relabeled
as request peak or physical VRAM. Cache diagnostics use the same forced token prefix
and compare per-layer KV, recurrent state and logits.

## Implementation and commands

`native_smoke.mjs` owns the bounded two-task smoke and runtime lock.
`native_experiment.mjs` owns the later stage lock, budget admission, complete
selection checks and single-use confirmation. `verify_selection.mjs` reads only
selection-family checks. All confirmation submissions are locked before the first
confirmation oracle read, with no subsequent model calls used for selection.

The unchanged campaign prompt/parser/verifier is imported through
`isolated_namespace.mjs`; shared `campaign/.namespace` is never rebuilt.
`rule.py` and `torch_hooks.py` remain CPU/unfused research references, not native
serving-cost evidence. `token_contract.mjs` rejects approximate token spans.
`decision.py` and `evaluate.py` reduce authenticated experiment receipts; their
unit fixtures are not experiment results.

From Gamma:

```sh
node --test projects/distillation/wgsl/channel_gain/test_native_smoke.mjs projects/distillation/wgsl/channel_gain/test_native_memory.mjs projects/distillation/wgsl/channel_gain/test_native_experiment.mjs
```

Native driver actions are `lock`/`smoke`, then `stage-lock`/`selection`/`confirmation`.
Every action requires explicit protocol, original freeze, amendment, budget, native
config, corpus and runtime-lock paths. Model execution additionally requires the
live service guard and `--gpu-authorized`. The corpus and locks already exist;
exclusive creation prevents overwriting them. These tools do not silently relax
rules or repair failed shaders.

The broader roadmap and prospective standards live one directory above. They do
not retroactively replace this study's frozen records.
