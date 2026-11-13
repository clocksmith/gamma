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
proof that the reconfiguration improves an answer. Current native primitives and
artifact checks are partial evidence; the full model/cache comparison is incomplete.

## 2. Shader improvement

**Claim:** a frozen reconfiguration rule improves fresh executable shader correctness.

**Evidence bar:** complete the current channel-gain study against the same-prompt
base, shuffled context, permuted gains and its other frozen controls, with
independent semantic execution and all selection/inference costs. Require the
study's predefined meaningful, reproducible gain rather than compiler acceptance
or success on exposed training examples.

**Non-claim:** a positive result would be promising research in the scoped shader
testbed. It would not establish general coding improvement, cheap specialization or
recursive self-improvement. This is the current experiment; no confirmation exists.

## 3. Efficient specialization

**Claim:** reconfiguration provides comparable or better specialization faster or
more cheaply than strong alternatives at equal total compute.

**Evidence bar:** compare additional base samples, prompt variations and a trained
adapter, including preparation/training where relevant, selection, inference,
verification and amortization. Freeze the quality/cost tradeoff before testing and
show it survives fresh tasks and replication. Existing adapter-comparator evidence
alone does not exhaust these alternatives.

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
results alone say nothing about the untested domains. This is draft research scope,
not an authorized multi-domain run or a frozen set of thresholds.

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
useful rules plus runtime evidence beyond the current single-request experiment.

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

Finish the current shader experiment first. If it yields a useful signal, compare
stronger matched-compute alternatives and test another domain. Build a recursive
proposal loop only after there is a useful, reproducible mechanism to improve.
Request isolation and cache correctness remain prerequisites wherever the rule is
used; concurrent switching needs separate system evidence. The broader rungs require
new frozen studies, not reinterpretation of earlier receipts.

A failed gain rule rejects that rule under its tested settings and budget. It does
not reject every transform family or the whole reconfiguration architecture.
Future rungs remain draft and unscheduled until a concrete study is registered;
this document is not a compute reservation or a speculative engineering timeline.
