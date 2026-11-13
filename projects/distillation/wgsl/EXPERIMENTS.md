# Reconfiguration experiment registry

This registry separates experiments from the [research roadmap](RECONFIGURATION-ROADMAP.md).
Only the first channel-gain study below has a frozen concrete protocol. Later rungs
are draft, unscheduled research directions, not nine completed or frozen studies.
Prospective studies use [standard v2](EXPERIMENT-PROTOCOL.md), pin its content hash
and begin from the [template](EXPERIMENT-TEMPLATE.md). Existing freezes are not
retroactively rewritten by that standard.

## Current study

| Field | Recorded value |
| --- | --- |
| Study ID | `wgsl-prefill-channel-gain-v1` |
| Target | Roadmap rungs 1–2: native fast reconfiguration and fresh shader correctness |
| Intervention | First analytical MLP channel-gain rule; no offline training |
| Model | Qwen/Qwen3.5-9B, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Arms | MLP/base-cache and MLP/frozen-gain re-prefill, sharing identical gains |
| All-projections | Not applicable to this rule; neither passed nor failed |
| Populations | 2 smoke / 4 selection / 16 confirmation semantic families |
| Status snapshot | Selection complete, gain-negative frozen; confirmation generation active; no confirmation result yet |
| Authority | Owner's first-rule request and MLP-only clarification, 2026-11-12 |

The comparison protocol is SAME-R, not a model arm. The trained seed-47 adapter is a
reference comparator, not a proven upper bound. Full controls and numeric decision
criteria belong to the frozen study documents, not this registry summary.

## Evidence map

| Boundary | Source of truth | What it establishes |
| --- | --- | --- |
| Hypothesis, first rule, limits | [Scope](PREFILL-RECONFIGURATION-SCOPE.md) | Owner-authorized question and decision criteria |
| Concrete settings and initial freeze | [Protocol](channel_gain/protocol.json), [freeze receipt](channel_gain/protocol-freeze.json) | Candidate/settings, splits, controls and source identities before materialization |
| Explicit pre-model accounting correction | [Amendment 01](channel_gain/protocol-amendment-01.json) | Restores scope's selection-only budget accounting before any model request; numeric criteria, tasks and candidate settings unchanged |
| Fresh tasks and exposure audit | [Corpus manifest](channel_gain/corpus-v1/manifest.json), [exposure registry](channel_gain/exposure-registry.json) | Materialized identities and bounded audit; not external novelty or generic task independence |
| Executable reference checks | [Reference qualification](channel_gain/reference-qualification-summary.json) | 22 known reference shaders passed 286 checks; not generated-output confirmation |
| Model conversion/admission | [Artifact preflight](channel_gain/native-artifact-preflight.json) | All shard integrity, exact architecture and sampled source-to-F16 parity; not model capability |
| Budget denominator | [Selection-budget receipt](channel_gain/selection-budget-receipt.json) | Conservative single-GPU residency bound: 3,559 seconds, giving a 35.59 GPU-second selection cap; not measured GPU active time |
| First model attempt | [Runtime lock 01](channel_gain/native-runtime-lock-01.json), [smoke attempt 01](channel_gain/native-smoke-01.jsonl) | One measured base request and a preserved transform-path integration failure |
| Implementation status and commands | [Study README](channel_gain/README.md), [execution-status receipt](channel_gain/execution-status.json) | Dated snapshots; read later attempt receipts for subsequent progress |

Admission and runtime receipts retain their own observation times and immutable
hashes. Their presence does not promote them to confirmation, and a later attempt
does not erase an earlier blocked or incomplete record.

## Append-only observations

**2026-11-13, before model execution:** criteria, candidate settings and populations
were frozen; 22 reference shaders passed 286 checks on Apple Metal. All 267 converted
model shards later passed BLAKE3 verification, and 19,261 scalar samples across 427
text tensors matched the source-to-F16 conversion. These are mechanics and artifact
admission evidence.

**2026-11-13, smoke attempt 01:** one same-prompt base request emitted 273 tokens in
92.6599 seconds of measured physical request time (92.6603 seconds including its
public verifier). Its public contract check failed because the required
`WORKGROUP_SIZE` override was absent. The attempt then stopped at the missing
operation contract for `beginChannelGainRequest`, before any transformed result.
The failed attempt and its output remain in the linked JSONL.

**2026-11-13, integration repair:** Doppler
[`d8806094`](https://github.com/clocksmith/doppler/commit/d8806094) repairs the native
operation boundary for the next attempt. A code fix is not a transformed-output
result, completed smoke batch or confirmation. At this registry snapshot no gain
candidate has completed selection, no cache/overhead comparison is established and
no confirmation checks have been used to select a candidate.

**2026-11-13, smoke attempt 02 and repair:** [nine model requests](channel_gain/native-smoke-02.jsonl)
completed before the trained adapter hit a query/gate shape mismatch. All nine
failed the visible contract. A same-prefix diagnostic measured layer-31 KV and
logit differences between same-gain cache arms; this is mechanics evidence only.
[Repair 02](channel_gain/runtime-repair-02.json) records the failure and narrow
Doppler fix. A [four-token adapter probe](channel_gain/adapter-probe-03.json)
subsequently completed without shader scoring. [Runtime lock 03](channel_gain/native-runtime-lock-03.json)
starts a full rerun with complete request lifecycle timing and base-reset logits.
No candidate or numerical criterion changed, and no confirmation ran.

**2026-11-13, completed smoke 03 and public repair:** [22 generated responses](channel_gain/native-smoke-03.json)
completed in 2,050.177 seconds plus 60.668 seconds of model loading. Both reset
checks restored all 248,320 base logits exactly. Same-gain cache diagnostics measured
layer-31 differences. An automatic bind-layout bug falsely blocked a valid unused
input; a [versioned repair](channel_gain/layout-repair-smoke-qualification.json) was
qualified without changing historical bytes. All sources/tokens were then sealed
and [public checks replayed](channel_gain/public-replay-03.json) on the same device,
with k=2 unchanged and zero additional model requests. Corrected public smoke:
base/gain/control/best-of-2 each 0/2, trained adapter 1/2. This is not confirmation.

**2026-11-13, budget decision:** the [stage lock](channel_gain/native-stage-lock-03.json)
binds original generation plus repaired public verification. The [admission receipt](channel_gain/native-selection-03/selection-receipt.json)
projects 782.517–843.332 seconds for eight selection requests against the unchanged
35.59-second cap. Selection was not admitted; both candidates remain untested, no
candidate was chosen and no confirmation-population checks were read. The estimate
is empirical and implementation-specific. The [final report](channel_gain/README.md)
retains failures, costs, cache/memory boundaries and the explicit mixed provenance.
The provider stayed active with zero restarts; owned experiment resources exited.

**2026-11-13, owner correction and continuation 02:** the owner rejected stopping
at the efficiency target before answering the shader question. The [explicit continuation](channel_gain/protocol-continuation-02.json)
retains that target in the scorecard and authorizes completion of the unchanged
fixed selection/confirmation workload. [Stage lock 04](channel_gain/native-stage-lock-04.json)
binds the runner and policy before any selection request. Prior smoke, failed
attempts and budget-stop receipts remain unchanged. Quality and efficiency will be
reported separately; hidden checks still cannot select candidates or samples.

**2026-11-13, completed selection 04:** all eight candidate-task requests ran.
Both candidates scored 0/4. The frozen timing tie-break selected `gain-negative`
(410.902 versus 411.100 seconds total attributed request time). The [selection receipt](channel_gain/native-selection-04/selection-receipt.json)
records 822.030 seconds of continuous allocated selection time, excluding cold
load; the 35.59-second efficiency target was missed. Confirmation generation has
started with that fixed candidate. No confirmation quality result exists yet.
A [CPU contract audit](channel_gain/selection-contract-audit-04.json) traced the
first six observed failures to malformed model WGSL, not a rejected valid override.

**2026-11-13, owner-authorized service retirement during confirmation:** after
39 completed confirmation generations, the owner explicitly retired the unused
27B Reploid provider. The [retirement receipt](channel_gain/service-retirement-04/service-retirement-04.json)
records the guard handover, stopped service, absent process IDs and an observed
18,268,540,928-byte increase in available host memory. The new read-only monitor
checks the stopped service and retains the memory floor. The original runtime,
inputs and quality criteria are unchanged; serving-environment timing changes are
recorded rather than presented as an unchanged isolated measurement window.

Append subsequent attempts, deviations, costs and decisions here with their own
receipts. Preserve these observations if a rerun succeeds. Smoke timing can support
a scoped ETA only when the measured arm mix represents the remaining work; this
single base measurement does not supply transformed-arm throughput.

## Future studies

Efficient specialization, cross-domain transfer, concurrent switching, bounded
rule proposals, repeated bounded recursive improvement, broader self-improvement,
and open-ended improvement are roadmap directions only. They have no allocated
experiment IDs, task populations, numeric thresholds, resource budgets or execution
schedule here. Register a concrete study and freeze its contract before claiming
that one is underway. ASI remains a separate extraordinary claim requiring
independent evidence beyond this ladder's current experiments.
