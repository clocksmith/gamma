# Reconfiguration experiment registry

This registry separates experiments from the [research roadmap](RECONFIGURATION-ROADMAP.md).
Only the first channel-gain study below has a frozen concrete protocol. Later rungs
are draft, unscheduled research directions, not nine completed or frozen studies.
Prospective studies use [standard v1](EXPERIMENT-PROTOCOL.md), pin its content hash
and begin from the [template](EXPERIMENT-TEMPLATE.md). Existing freezes are not
retroactively rewritten by that standard.

## Active study

| Field | Recorded value |
| --- | --- |
| Study ID | `wgsl-prefill-channel-gain-v1` |
| Target | Roadmap rungs 1–2: native fast reconfiguration and fresh shader correctness |
| Intervention | First analytical MLP channel-gain rule; no offline training |
| Model | Qwen/Qwen3.5-9B, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Arms | MLP/base-cache and MLP/frozen-gain re-prefill, sharing identical gains |
| All-projections | Not applicable to this rule; neither passed nor failed |
| Populations | 2 smoke / 4 selection / 16 confirmation semantic families |
| Status snapshot | Active work, experiment incomplete; no confirmation result |
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
