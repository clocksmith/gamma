# Reconfiguration experiment standard, v2

This standard is for prospective reconfiguration studies. Each study pins the
content hash and version it uses. It does not rewrite an existing study's frozen
rules: the first channel-gain experiment remains governed by its own
[scope](PREFILL-RECONFIGURATION-SCOPE.md), [protocol](channel_gain/protocol.json)
and explicitly recorded amendments. [SAME-R](../../samer/README.md) is the
comparison protocol, not an experimental arm.

Use the [template](EXPERIMENT-TEMPLATE.md) to register a study in
[EXPERIMENTS.md](EXPERIMENTS.md). A roadmap rung identifies the claim being tested;
it is neither a frozen experiment nor evidence that the claim is true.

## Identity and hypothesis

Name one concrete intervention, the mechanism it changes, the scope of the claim,
and an observable outcome that would contradict it. Separate the owner's purpose,
the implementation's demonstrated capability, and the research hypothesis. State
which weights, activations, cache state, controller, optimizer or external tools
may change. Give the reset and isolation contract for every mutable state.

Pin model/source revision, tokenizer and template, adapters/controllers, artifact
and shard hashes, conversion configuration, runtime code, device/backend, precision,
compiler/verifier identity, and all task and oracle manifests. A changed executable
or artifact gets a new attempt identity. Never silently substitute a smaller model,
precision, cache policy or fallback backend.

## Freeze before selection and confirmation

Before candidate selection, record the search space, candidate order, selection
population, sampling settings and seeds, selection algorithm, tie breaks, resource
budget, stopping rule and failure handling. Declare whether timing-only smoke work
can affect any of these decisions; charge all work used for selection to its budget.
A smoke outcome cannot become a confirmation observation through relabeling.

Before confirmation, seal the selected candidate, every submitted output when
submission selection is permitted, the independent evaluator, exact confirmation
population, checks, primary comparisons, numeric decision thresholds, statistical
method, multiplicity treatment, minimum information requirements and cost limits.
Record hashes and timestamps. Unknown, underpowered and inapplicable outcomes are
separate from pass and fail. Values left undecided mean a study is still a draft;
this shared standard supplies no universal success numbers.

## Populations and evaluator independence

Use separate mechanics/smoke, selection and confirmation populations, with the
independence unit declared explicitly: task family, problem, episode, environment,
organization, time window or another justified unit. Variants of one problem do not
become independent samples by changing a seed or input shape. Audit prior training,
selection, demonstrations and earlier test exposure; state the audit's limits.

The evaluator must derive success independently of the candidate's assertions.
Freeze oracle construction and scoring code, independently check reference cases,
and test rejection of plausible incorrect outputs. Keep evaluator authorship,
validation and access history in the record. The generator or optimizing controller
cannot revise its own evaluator or inspect reserved outcomes while selecting a
candidate. Public sample selection may read only the checks named in its frozen
policy. Model-generated tests are proposals until independently validated.

A failed public check and a held-out semantic failure are different observations.
For WGSL, compilation alone is insufficient: preserve dispatch outputs, CPU-oracle
agreement, buffer canaries, shape/workgroup variations and input permutations under
the study's declared coverage. Other domains must define their corresponding
executable or independently assessed correctness boundary.

## Controls, regressions and costs

Choose controls that isolate the intervention, then freeze them. Relevant controls
include an unchanged base, compute-matched base sampling, shuffled or unrelated
context, random state matched in size and magnitude, permuted channel assignment,
and a trained adapter/controller comparator. Explain omissions and inapplicable
arms without treating them as successes. Reuse identical frozen transforms when a
cache comparison is meant to isolate base-cache versus re-prefill behavior.

Include a declared general-regression population where a specialization could harm
other behavior. Freeze its tolerances and decision role. Count wrong acceptances:
outputs accepted by public/visible checks but rejected by the independent checks.
Measure errors, abstentions, retries, discarded attempts and environment failures
separately. A new capability claim cannot be supported by quietly dropping them.

Record complete cost, with units and measurement boundaries:

- Source/artifact preparation, conversion, adapter extraction/loading and validation;
  any adapter/controller training, search, data generation and evaluator preparation.
- Per-request tokenization, reference/base prefill, statistics collection, transform
  derivation, transfer/readback, re-prefill, decode, tools and verification.
- Cold loads separately from serving time; host/device memory, peak allocation,
  persistent and per-request state, GPU allocation time, CPU time and storage.
- All candidate selection work, including rejected candidates and controls used to
  rank them; all amortization assumptions and compute mismatches between arms.

A reused trained adapter has historical training cost and current preparation cost;
neither is zero merely because it existed before the run. Report unavailable costs
as unavailable. Identify derived bounds, filesystem timing and hardware counters
by their actual evidence class. Do not label a wall interval as GPU active time.

Declare the role of every resource number. An execution limit protects an actual
service, memory constraint, authorized compute allocation or fixed search workload;
give its reason and stopping behavior. An efficiency target scores whether the
method is economical. Missing an efficiency target does not by itself stop an
otherwise authorized quality measurement. Complete the frozen workload and report
quality and cost separately, including an unsuccessful joint criterion where
applicable. Do not extend candidate search or tune settings after seeing reserved
outcomes. If a real execution limit prevents completion, report incomplete evidence
and the concrete resource needed, without interpreting it as a quality result.

This distinction is prospective. Existing frozen studies retain their original
rules and explicit continuation records; v2 does not retroactively change them.

## Execution, deviations and decisions

Run the smallest frozen smoke batch first. Measure it before reporting a throughput
ETA; state the remaining work, measured basis and uncertainty. Preserve live-service
constraints, enforce memory/resource limits, and stop only the experiment's own
processes when its guards trigger. Keep cold, warm and contended measurements
separate. Progress claims require current logs or receipts.

Use append-only attempt records: requested command, input/output hashes, start/end,
exit status, observations, costs, deviations and the exact artifacts produced.
Never overwrite a failed attempt with a repaired run. Record implementation repairs
and their validation; distinguish them from changes to the intervention or study
rules. A rule change after outcomes are visible requires a new study/confirmation
population when it would make the old confirmation selectable. Preserve the original
protocol and explain the disposition of affected evidence.

Confirmation executes once under its sealed contract. Report paired task outcomes,
uncertainty, cost and every predefined criterion, not just aggregate accuracy. A
compound claim passes only when its required criteria pass. A failed rule rejects
that tested rule under that contract; it does not disprove every possible
reconfiguration mechanism. Update the registry with the receipt and explicit claim
boundary. Subsequent rungs require their own evidence and do not inherit success.
