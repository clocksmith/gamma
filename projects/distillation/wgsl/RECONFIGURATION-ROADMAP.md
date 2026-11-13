# Reconfiguration research roadmap

Owner direction, 2026-11-12. These are nine research rungs, not official AGI levels
and not nine frozen experiments. The ladder describes increasingly strong claims;
each requires a study with its own independent evidence, budgets and numeric
thresholds. No success at one rung grants success at the next.

The working architecture uses shared base weights and a request-specific state
`z`: inspect the prompt/prefill, derive `z`, apply it during computation, then discard
it and recover the base behavior. Cache consistency and request isolation are part
of the mechanism. Retaining a rule that constructs `z` is a separate operation from
retaining one request's `z`; changing base weights is another separate intervention.
Gamma owns experiments and evidence. Doppler owns runtime execution. Existing
project boundaries and frozen studies retain their authority.

The first rule is [MLP channel gain](PREFILL-RECONFIGURATION-SCOPE.md).
[EXPERIMENTS.md](EXPERIMENTS.md) records what actually ran.
[EXPERIMENT-PROTOCOL.md](EXPERIMENT-PROTOCOL.md) defines the prospective shared
standard; [EXPERIMENT-TEMPLATE.md](EXPERIMENT-TEMPLATE.md) makes it operational.

## 1. Fast reconfiguration

**Claim:** prefill can produce request-specific gains, decode can apply them, and
discarding them restores the base computation.

**Evidence bar:** exercise the actual model path; verify immutable shared weights,
request-state isolation, cleanup after success/failure, reset, cache behavior and
measured full overhead. Use the same frozen gains when isolating base-cache versus
re-prefill behavior. Kernel fixtures alone do not establish model integration.

**Non-claim:** this is an engineering capability, not a learning breakthrough or
proof that the reconfiguration improves an answer. The [first smoke study](channel_gain/README.md) now supplies two-prompt native
cache and exact reset observations. The [27B exploratory screen](../../reconfiguration/cross_domain_screen/RAW-RESULTS-01.md)
adds three exact full-model reset observations, one per domain. A
[Mac synthetic test](https://github.com/clocksmith/doppler/blob/daede6a0/reports/channel-gain-20261113/synthetic-isolation-receipt.json)
exercises two live gain states, alternating tiny dense-FFN dispatches, overlapping
operation lifetimes and failure cleanup. Full-model concurrent isolation and broader
qualification remain unproved.

## 2. Shader improvement

**Claim:** a frozen reconfiguration rule improves fresh executable shader correctness.

**Evidence bar:** complete the current channel-gain study against the same-prompt
base, shuffled context, permuted gains and its other frozen controls, with
independent semantic execution and all selection/inference costs. Require the
study's predefined meaningful, reproducible gain rather than compiler acceptance
or success on exposed training examples.

**Non-claim:** a positive result would be promising research in the scoped shader
testbed. It would not establish general coding improvement, cheap specialization or
recursive self-improvement. The original attempt stopped at budget admission.
The owner-directed [continuation](channel_gain/protocol-continuation-02.json)
completed all eight selection and 176 confirmation generations. The
[confirmation report](channel_gain/CONFIRMATION-RESULTS-04.md) records 0/16 for base,
best-of-2 and every gain/control arm, versus 11/16 for the trained adapter. Gain
closure of the adapter gap was zero; gain/control comparisons have zero discordant
tasks and remain underpowered. All non-adapter outputs failed the source contract
before compilation; the result tests failure to produce compliant shaders, not
a comparison of their executed numeric accuracy. This first rule did not establish
shader improvement.
The [experiment registry](EXPERIMENTS.md) retains all attempts and costs.

## 3. Efficient specialization

**Claim:** reconfiguration provides comparable or better specialization faster or
more cheaply than strong alternatives at equal total compute.

**Evidence bar:** compare additional base samples, prompt variations and a trained
adapter, including preparation/training where relevant, selection, inference,
verification and amortization. Freeze the quality/cost tradeoff before testing and
show it survives fresh tasks and replication. Existing adapter-comparator evidence
alone does not exhaust these alternatives. The completed first study consumed
822.030 seconds in selection, missed its 1% efficiency target, and measured added
latency of 11.69% / 25.34% for base-cache / re-prefill, with contended timing. It
produced no gain quality advantage and does not establish this rung.

**Non-claim:** an advantage could be a practical breakthrough; a shader pass-rate
increase with uncounted setup or weaker baselines does not establish it. No study
for this stronger claim is frozen or scheduled here.

## 4. Cross-domain reconfiguration

**Claim:** the same frozen rule improves coding, mathematics, writing and other
declared tasks without domain-specific tuning.

**Evidence bar:** freeze the rule before opening held-out task families in each
domain; use domain-appropriate independent evaluators, strong matched controls and
a general-regression population. Require the prospective study's substantial,
consistent gains, including failures and negative transfer.

**Non-claim:** a separate tuned rule per domain does not pass this rung. Shader
results alone say nothing about the untested domains. The owner-authorized
[27B screen](../../reconfiguration/cross_domain_screen/REPLAY-RESULTS-01.md) completed
six families and 24 requests across arithmetic, Python and structured text. Base,
channel gain and shuffled context each passed 4/6 under the frozen oracle, with
zero gain wins or losses. The original permuted-gain 3/6 includes a restricted
interpreter rejection. The completed versioned replay expands bounded syntax
support and scores all four conditions at 4/6, with zero wins or losses against
base; behavioral cases are unchanged. Both model and domains changed, so
this is not same-model 9B transfer. It provides exploratory evidence, not this
rung's substantial, consistent gain or general-regression evidence.

## 5. Switching and persistence

**Claim:** fast specialization remains correct across concurrent requests, unrelated
task transitions and returns to a previously used configuration.

**Evidence bar:** test many requests and transitions under a declared concurrency
and load contract; verify immutable shared weights, per-request state isolation,
reproducible restoration/reconstruction of prior configurations, cache ownership,
failure recovery and measured switching/storage costs. Compare answers as well as
throughput. State exactly what persists and what is recomputed.

**Non-claim:** this establishes a fast specialist system architecture, not a single
benchmark trick, broad intelligence or learning from the transitions. It requires
useful rules plus runtime evidence beyond the current serial model studies. The
[Mac toy receipt](https://github.com/clocksmith/doppler/blob/daede6a0/reports/channel-gain-20261113/synthetic-isolation-receipt.json)
covers independent live gain handles, reset/discard and failure cleanup on tiny
shared inputs/weights; one serialized GPU queue and a minimal reset fixture do not
establish full-model concurrency. The three 27B reset checks were sequential.

## 6. Self-proposed rule improvement

**Claim:** a model can propose an improved rule within a bounded rule language.

**Evidence bar:** define the proposal language and budget; keep evaluator and
acceptance rules independent of the proposer; test proposals on selection tasks and
retain a successor only after it beats its predecessor under the frozen contract.
Seal an independent confirmation and preserve the proposal, predecessor, costs and
rejected candidates.

**Non-claim:** one retained successor is not recursive self-improvement. The model
cannot declare its own proposal successful or change its test to make it pass.
No proposal loop is started by this roadmap.

## 7. Repeated bounded recursive self-improvement

**Claim:** a retained rule participates in proposing the next rule, and this loop
produces repeated improvements within its bounded reconfiguration mechanism.

**Evidence bar:** demonstrate multiple retained generations, each evaluated on fresh
tasks, against the fixed original rule and equal-budget nonrecursive/search controls.
Persist the actual rule and its evidence, trace its participation in the next
proposal, and count the whole search history. Freeze the number of generations and
retention/confirmation requirements in the prospective study.

**Non-claim:** repeated search run by an unchanged external proposer is insufficient.
Base weights may remain frozen; the supported claim is bounded recursive improvement
of the reconfiguration mechanism, not unrestricted intelligence growth.

## 8. Broader self-improvement

**Claim:** independently verified improvement extends beyond channel gains to the
transform family, routing, runtime allocation or proposal method itself.

**Evidence bar:** define the expanded action space and resource/access limits before
running; keep evaluation and permissions outside the proposed changes. Demonstrate
repeated cross-domain gains against strong equal-budget controls and general
regression checks, with provenance for changes to the search/proposal mechanism.

**Non-claim:** a larger menu or one successful architecture change is not sufficient.
This would support a stronger recursive-improvement claim only within the tested
scope. It does not authorize modifying unrelated services or rewriting acceptance.

## 9. Open-ended improvement and ASI

**Claim under investigation:** improvement can extend beyond a predefined menu.
This is an open research ambition; the earlier bounded tests cannot establish it.
Evidence would need to show independently evaluated advances outside the initial
proposal space across changing, novel problems, while preserving evaluator
independence and accounting for the enlarged search and resources.

**ASI is a separate claim:** extraordinary performance across most important
cognitive domains would have to be independently demonstrated under its own explicit
scope and standards. Neither repeated recursive improvement nor an open-ended
proposal mechanism automatically implies ASI. No ASI criterion is frozen here,
and no current result supports that claim.

## Dependency and execution order

The original 9B shader confirmation remains active (59/176 generated requests
observed at 13:19:17 UTC on 2026-11-13; no terminal result or quality conclusion).
The owner authorized the bounded 27B screen and Mac synthetic checks in parallel;
those have completed with separate evidence and recorded GPU contention. Stronger
matched-compute comparisons and substantial cross-domain gains remain unestablished.
Build a recursive proposal loop only after there is a useful, reproducible mechanism
to improve. Rungs 6–9 remain unstarted.
Request isolation and cache correctness remain prerequisites wherever the rule is
used; concurrent switching needs separate system evidence. The broader rungs require
new frozen studies, not reinterpretation of earlier receipts.

A failed gain rule rejects that rule under its tested settings and budget. It does
not reject every transform family or the whole reconfiguration architecture.
Stronger claims beyond the registered studies remain draft and unscheduled;
this document is not a compute reservation or a speculative engineering timeline.
