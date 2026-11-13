# Reconfiguration experiment registry

This registry separates experiments from the [research roadmap](RECONFIGURATION-ROADMAP.md).
The original 9B channel-gain study and a separate 27B exploratory screen have
frozen concrete protocols. Synthetic runtime checks supply narrower engineering
evidence. These are not nine completed or frozen studies; later claim rungs retain
their own evidence requirements.
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
| Status snapshot | Completed 8/8 selection requests, 176/176 confirmation generations and 16 cache diagnostics; terminal receipt observed 16:21:07 UTC, 2026-11-13. Base, best-of-2 and every gain/control arm 0/16; trained adapter 11/16. Original joint decision: not confirmed. |
| Authority | Owner's first-rule request and MLP-only clarification, 2026-11-12 |

The comparison protocol is SAME-R, not a model arm. The trained seed-47 adapter is a
reference comparator, not a proven upper bound. Full controls and numeric decision
criteria belong to the frozen study documents, not this registry summary.

## Additional registered evidence

| Study or check | Frozen scope / actual execution | Evidence and limits |
| --- | --- | --- |
| 27B cross-domain screen 01 | Same analytical gain-negative formula mapped to dense layers 62/63; six families, 24 requests, base-cache only; arithmetic, Python and structured text | [Protocol](../../reconfiguration/cross_domain_screen/protocol.draft.json), [runtime lock](../../reconfiguration/cross_domain_screen/screen-runtime-lock-01.json), [corrected replay](../../reconfiguration/cross_domain_screen/REPLAY-RESULTS-01.md), [original report](../../reconfiguration/cross_domain_screen/RAW-RESULTS-01.md), [raw archive](../../reconfiguration/cross_domain_screen/screen-run-01/archive.json). Completed; corrected behavioral scores 4/6 for all four conditions, no gain benefit. Original permuted 3/6 preserved; versioned syntax repair replayed all 24 existing outputs. Model and domains both changed. |
| Mac synthetic gain/isolation/reset checks | Two live gain handles, alternating tiny dense-FFN dispatches, overlapping operation lifetimes, immutable shared input/weights, reset/discard and failure cleanup | Doppler [commit daede6a0](https://github.com/clocksmith/doppler/commit/daede6a0), [receipt](https://github.com/clocksmith/doppler/blob/daede6a0/reports/channel-gain-20261113/synthetic-isolation-receipt.json). Passed on Apple M3; zero model loads, one GPU queue, no full-model concurrency or quality claim. |

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

**2026-11-13, completed 27B exploratory screen:** all 24 outputs were sealed
before scoring. Base, channel gain and shuffled context each passed 4/6; gain and
shuffled context each had 0 wins, 0 losses and 6 ties against base. The original
permuted score was 3/6 because the restricted Python interpreter rejected
`sorted(..., key=lambda ...)`; the unchanged function passes all six frozen cases
in ordinary Python. [The CPU diagnostic](../../reconfiguration/cross_domain_screen/screen-run-01/audit-summary.json)
retains that distinction without rewriting the original scores. The versioned
repair and all-output replay are recorded in the subsequent observation below.
Three serial
full-model resets reproduced all 248,320 logits exactly, and no response hit the
256-token cap. The measured model-load-through-cleanup interval was 639.994 seconds.
[Environment records](channel_gain/environment-04.jsonl) preserve overlap with the
ongoing 9B confirmation; timings are contended, not isolated speed evidence.

**2026-11-13, completed versioned evaluator replay:** the
[corrected report](../../reconfiguration/cross_domain_screen/REPLAY-RESULTS-01.md)
and [replay receipt](../../reconfiguration/cross_domain_screen/screen-run-01/oracle-replay-v2.json)
record CPU-only scoring of all 24 original sealed outputs. The new interpreter
accepts bounded pure inline lambdas and ordinary `sorted` key/reverse keywords;
this is an explicit syntax interpretation/expansion. Expected behavioral cases,
exact answers and pass combination are unchanged. Only the permuted-gain Python
interval score changes, bringing all four conditions to 4/6. Every comparison
against base has 0 wins, 0 losses and 6 ties; there is no observed gain benefit.
Original scores remain preserved. Replay took 5.185 seconds with no new samples,
model calls, GPU calls or selection. This is exploratory repaired evaluation,
not confirmation or broad cross-domain transfer evidence.

**2026-11-13, completed confirmation 04:** all 176 unique generations were sealed
before reserved scoring, producing 224 submission references across both cache
arms and 16 cache diagnostics. The [authenticated report](channel_gain/CONFIRMATION-RESULTS-04.md)
and [exact-byte archive](channel_gain/archive-04/archive-manifest.json) retain the full run.
Base, public-selected best-of-2, actual gains, shuffled-context, random and permuted
gains all scored 0/16 semantic passes in both cache arms; the trained adapter scored
11/16. The adapter gap was 11 tasks and gain closure was zero. Paired gain/control
comparisons had no discordant tasks and remain underpowered, not evidence of
statistical equivalence. No condition produced a wrong acceptance. The
[CPU failure/cache audit](channel_gain/CONFIRMATION-AUDIT-04.md) distinguishes the
failure boundary: all 160 non-adapter outputs failed the required source contract
before compilation, chiefly missing `WORKGROUP_SIZE`; all 16 adapter outputs
compiled and dispatched. The zero scores therefore do not compare executed
numeric correctness of base versus gains.

Selection consumed 822.030 seconds against the unchanged 35.59-second target.
Confirmation physical stage time was 16,729.217 seconds (4 h 38 min 49 s), including
cold loading and ending before final receipt serialization/teardown. Added attributed
latency was 11.69% with base cache and 25.34% with re-prefill. Base-cache incremental
peak memory remains unqualified; re-prefill retained increment exceeded the adapter
threshold. The environment ledger records provider retirement and a 639.994-second
27B screen overlap; timings are contended, not isolated performance. This completed
study does not establish shader improvement or efficient specialization. It tests
this rule and implementation, not every reconfiguration architecture.

Append subsequent attempts, deviations, costs and decisions here with their own
receipts. Preserve these observations if a rerun succeeds. Smoke timing can support
a scoped ETA only when the measured arm mix represents the remaining work; this
single base measurement does not supply transformed-arm throughput.

## Future studies

Efficient specialization, substantial cross-domain improvement with general
regression checks, full-model concurrent switching, bounded rule proposals, repeated
bounded recursive improvement, broader self-improvement and open-ended improvement
remain unestablished. The small registered cross-domain screen and synthetic
isolation check do not satisfy those stronger claims. Rungs 6–9 are unstarted and
have no frozen task populations, numeric thresholds, resource budgets or execution
schedule here. Register a concrete study and freeze its contract before claiming
that one is underway. ASI remains a separate extraordinary claim requiring
independent evidence beyond this ladder's current experiments.
