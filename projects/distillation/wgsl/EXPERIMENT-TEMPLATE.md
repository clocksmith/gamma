# Experiment template

Copy this template into a study directory. Replace each undecided field before the
corresponding freeze. Keep drafts labeled draft. Pin the content hash of
[EXPERIMENT-PROTOCOL.md](EXPERIMENT-PROTOCOL.md) and retain earlier versions and
attempts. This template adds no approval stage or automatic execution authority.

## Identity

| Field | Study value |
| --- | --- |
| Study ID, version, date, owner instruction | Undecided |
| Status and linked registry entry | Draft |
| Roadmap rung and narrow claim | Undecided |
| Standard version and SHA-256 | v2; compute when adopted |
| Scope/protocol path, hash, parent/amendments | Undecided |
| Owner purpose, hypothesis, falsifying observation | Undecided |
| Component owners and boundaries | Gamma experiment/evidence; name runtime/tool owners |
| Authorized action and resource limits | Undecided |

## Intervention and runtime

Describe the exact rule, equations or algorithm, degrees of freedom, affected
layers/modules and permitted mutable state. Specify collection span/template
exclusions, reference construction, state lifetime, reset, concurrency isolation,
cache arms and which state is identical between paired arms. List unsupported paths
and the errors that reject them.

| Identity | Frozen reference |
| --- | --- |
| Base model/source revision and weight hashes | Undecided |
| Tokenizer, template and preprocessing | Undecided |
| Adapter/controller/history and preparation | Undecided or inapplicable with reason |
| Conversion/configuration and native artifact hashes | Undecided |
| Runtime, compiler/verifier, dependencies | Undecided |
| Device, backend, precision and permitted fallback | Undecided |
| Runtime/driver lock and admission evidence | Undecided |

## Populations and access

| Population | Independent unit/count | Source/manifest/oracle hashes | Permitted use |
| --- | --- | --- | --- |
| Mechanics/smoke | Undecided | Undecided | Fixed mechanics and timing; specify any selection use |
| Selection | Undecided | Undecided | Candidate/settings selection within frozen budget |
| Confirmation | Undecided | Undecided | One sealed independent evaluation |
| General-regression | Undecided | Undecided | Predefined regression decision |

Record exposure/overlap audit, variants and grouping, public versus held-out checks,
reference qualification, evaluator author/reviewer and validation receipts. State
who or what can open each outcome, and how selection is prevented from reading
confirmation. Identify any external or temporal holdout and its limits.

## Selection, controls and numeric decision

| Field | Frozen value |
| --- | --- |
| Candidate space/order, trainable parameters and steps | Undecided |
| Sampling, seeds, length limits and retries | Undecided |
| Ranking and tie breaks; allowed public sample checks | Undecided |
| Fixed selection workload and any execution limit, with reason | Undecided |
| Scored efficiency target and denominator provenance | Undecided |
| Quality measurement after a missed efficiency target | Complete the authorized frozen workload; state any actual execution limit |
| Stop/deadline behavior; incomplete-candidate disposition | Undecided |
| Base and compute-matched baseline | Undecided |
| Context/random/permuted-state controls | Undecided or inapplicable with reason |
| Trained comparator and its full preparation cost | Undecided or inapplicable with reason |
| Primary/secondary outcomes and paired comparison unit | Undecided |
| Numeric success/regression/wrong-acceptance limits | Undecided |
| Statistical tests, multiplicity and minimum information | Undecided |
| Unknown, underpowered and inapplicable dispositions | Undecided |
| Joint decision rule and exact non-claims | Undecided |

## Measurement and execution

List commands, immutable input hashes, environment checks and safe-device guards.
Define synchronized timing boundaries, cold/warm/contended conditions, token counts,
cache/state divergence, host/device memory and transform bytes. Record source,
adapter and evaluator preparation, training/search, failed work, tools and serving
costs separately; state amortization explicitly.

Record measured smoke results and timing before a remaining-work ETA. Seal the
selected candidate, submissions, task/oracle identities and evaluator before
confirmation. Append each attempt and deviation with its input/output identities;
keep repair runs separate from their failed predecessors.

## Freeze checklist

- [ ] Scope, hypothesis, exact intervention and mutable-state lifecycle are fixed.
- [ ] Model/artifact/runtime identities and admission checks are recorded.
- [ ] Populations, exposure audit and independence unit are fixed.
- [ ] Public selection access and independent evaluator are validated.
- [ ] Candidate settings, selection method, seeds, budgets and stops are fixed.
- [ ] Controls, full cost, regression and wrong-acceptance accounting are fixed.
- [ ] Numeric/statistical decision rules and non-claims are fixed.
- [ ] Selection and confirmation locks exist at their required boundaries.
- [ ] Attempt/deviation records and reproducible commands have durable paths.

## Results and disposition

Link raw attempts, selected outputs, verifier receipts and cost records. Give every
predefined criterion its result and evidence. State what ran, did not run, failed,
was underpowered, or was inapplicable. Separate mechanics, smoke, selection and
confirmation. Record the resulting narrow claim, remaining uncertainty and the
registry update; do not turn a follow-up hypothesis into a completed rung.
