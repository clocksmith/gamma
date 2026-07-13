# SAME-R Selector And Saturation Contract

This document specifies automatic, cross-domain, multi-model, and recursive
SAME-R selection. It is a design contract. Gamma does not yet implement the
shared registry, selector, or recursive evaluator described here.

The [canonical README](README.md) owns the outer method. The
[causal and evidence contract](CAUSAL_AND_EVIDENCE_CONTRACTS.md) owns each
trial. Machine-readable objects live under [`contracts/`](contracts/README.md).

## Selector Claim Boundary

An implemented selector does not become valid because it emits a plausible
next step. A selector capability claim requires a frozen meta-experiment:

```text
Under a frozen registry, history set, domain set, proposal budget, evaluation
budget, meta-evaluator, and replication policy, selector S chooses intervention
sequences that improve declared selector metric M over baseline selector B,
satisfy invalid-selection and guardrail limits, and bind every decision to
selection and child-trial receipts.
```

Without this comparison, automatic selection is mechanics only.

## Typed Approach Registry

The registry is versioned and content-addressed. Every entry records:

- `approachId` and immutable approach revision;
- mechanism type;
- implementation repository, revision, path, and hash;
- eligible domains, capabilities, populations, and trial stages;
- required inputs and produced artifacts;
- allowed participant roles;
- proposal and materialization schemas;
- required causal-control shape;
- proposal, generation, training, evaluation, and human-review budget shape;
- evidence and promotion prerequisites;
- known incompatibilities and blocking conditions;
- current status; and
- accepted, rejected, blocked, invalidated, and saturated history pointers.

Registry status is one of:

- `eligible`;
- `disabled`;
- `blocked`;
- `saturated_for_scope`; or
- `superseded`.

Status is scope-specific. An approach rejected for WGSL compiler repair may
remain eligible for translation. A revision change creates a new entry.

## Typed Trial History

History uses separate collections:

- `accepted`: trial passed its declared causal stage;
- `rejected`: valid trial produced a terminal negative result;
- `blocked`: required authority, artifact, runtime, or evidence was unavailable;
- `invalidated`: contract or contamination failure invalidated the evidence;
- `saturated`: a registry/contract/budget scope reached a terminal stopping
  predicate; and
- `promoted`: candidate passed the complete promotion contract.

Each history row binds:

- domain, capability, population, and grouping;
- approach and intervention IDs;
- causal and run contract hashes;
- selection receipt that opened it;
- trial stage and disposition;
- effect versus anchor and matched control;
- typed primary and guardrail evidence;
- uncertainty and denominator;
- budget debits;
- contamination and invalidation status; and
- immutable receipt pointers.

No result is inferred from collection membership alone. Every disposition has a
reason code and receipt.

## Participant Registry

Humans, Claude, Codex, Gemini, local models, remote models, deterministic
programs, and domain scripts use the same participant contract.

Required participant fields:

- participant ID, kind, provider/model ID, immutable revision, and owner;
- allowed roles and domains;
- data-access boundary;
- wrapper, system prompt, prompt template, tool schema, output schema, decode,
  retry, and timeout hashes;
- label-authority receipts where labeling is allowed;
- proposal, critic, teacher, evaluator, selector, and adjudication budgets;
- allowed child approaches and recursion depth; and
- conflict-of-interest and human-gate policy.

Provider identity is not authority. Claude, Codex, and Gemini can be independent
proposers, cross-critics, qualified teachers, or model judges only within their
registered scope.

## Multi-Model Proposal Modes

Each orchestration mode is itself an approach registry entry.

### Independent proposals

Participants receive the same frozen history summary and proposal schema.
Their outputs are retained independently. The selector may choose one, reject
all, or materialize a matched comparison among proposals.

### Blind cross-critique

Critics inspect causal contracts without provider branding when practical.
They may identify confounders, missing controls, invalid authority, budget
drift, prior negative evidence, or contamination risk. Critique cannot change
the evaluator or promote a candidate.

### Structured debate

Participants exchange a fixed number of turns under a frozen transcript and
call budget. The final output is a candidate causal contract plus dissent
ledger. Persuasiveness and consensus are not evaluation metrics unless a
separate meta-experiment validates them.

### Tournament or routing

Candidate approaches may be routed by declared domain features or compared in
matched shadow trials. The router is an inner approach and requires its own
random/control baseline and external selector metric.

### Human-model adjudication

A human may resolve proposal validity or evidence disagreement under a frozen
rubric. The receipt retains all model outputs, machine evidence, human edits,
dissent, abstention, and final authority.

## Proposal Contract

`propose(history, frozen_contract, proposal_budget)` returns:

```text
proposal = {
  proposal_id,
  participant_id,
  participant_revision,
  approach_id,
  history_hash,
  frozen_contract_hash,
  proposal_prompt_hash,
  causal_contract,
  expected_artifacts,
  predicted_effect,
  predicted_failure_modes,
  required_budget,
  conflicts,
  receipt_hash
}
```

A proposal is schema-valid only if it identifies one intervention, matched
operation, primary metric, guardrails, failure interpretation, budgets, and
saturation rule. Invalid proposals remain in history and debit the proposal
budget.

## Cross-Domain Normalization

The selector MUST NOT compare raw domain metrics directly. It consumes a
normalized decision record:

```text
normalized_trial = {
  domain,
  capability,
  population_hash,
  approach_id,
  trial_stage,
  disposition,
  primary_effect_direction,
  effect_vs_anchor,
  effect_vs_control,
  standardized_uncertainty,
  guardrail_pass,
  contamination_pass,
  evidence_quality_vector,
  denominator_completeness,
  budget_fraction_spent,
  claim_boundary,
  receipt_hashes
}
```

Normalization preserves the underlying metric and receipt. It may express
effect direction, threshold margin, confidence, evidence quality, and budget
fraction. It may not convert BLEU, pass@1, F1, bytes, and latency into a single
scientific capability score without a separately validated meta-metric.

Cross-domain history provides hypotheses about search behavior, for example:

- evaluate dense checkpoints around an observed external peak;
- preserve random controls for data-selection claims;
- reject more-training-is-better assumptions;
- require parity before serving promotion; or
- stop a continuation axis after repeated external regression.

Every transferred hypothesis is tested again under the target domain contract.

## Selection Policy

The selector filters before ranking:

1. reject schema-invalid proposals;
2. reject participant-role or label-authority violations;
3. reject population, sealed-holdout, or contamination access violations;
4. reject proposals that change undeclared frozen axes;
5. reject proposals exceeding remaining budget or recursion limits;
6. reject approaches blocked, disabled, superseded, or saturated for scope;
7. reject repetitions covered by a terminal negative receipt unless the new
   causal contract declares the changed axis;
8. rank remaining proposals under the frozen selector policy; and
9. emit one selected intervention or a no-selection/saturation receipt.

Ranking features and weights are frozen and hashed. Learned selector policies
record training histories, features, labels, calibration, and held-out
meta-evaluation. A model selector records its prompt, tools, decode, calls, and
all considered outputs.

## Selection Receipt

Every decision records:

- selector and participant identities;
- registry, history, causal program, and budget hashes;
- exact candidate list;
- validation status for each candidate;
- rejection and blocking reasons;
- ranking features and scores;
- selected approach and intervention;
- selection policy and tie-break;
- budget before, debit, and remaining;
- saturation decision before and after selection;
- human gate and override;
- recursive parent and child pointers; and
- receipt hash.

A human override creates an adjudication receipt; it does not rewrite the
selector output.

## Search Budget

The budget is a typed vector, not one scalar:

```text
search_budget = {
  approach_ids,
  candidate_family_hash,
  search_method,
  adaptive,
  proposal_calls,
  critic_calls,
  teacher_calls,
  generation_calls,
  model_tokens_by_participant,
  materializations,
  training_runs,
  lane_runs,
  seed_runs,
  checkpoint_evaluations,
  item_evaluations,
  evaluator_looks,
  adjudications,
  human_decisions,
  sealed_holdout_looks,
  recursion_depth,
  child_count,
  nominal_candidate_budget,
  adjusted_decision_budget,
  multiplicity_policy
}
```

Attempted calls count, including malformed proposals and rejected generations.
A predeclared infrastructure failure may refund a budget unit only through a
machine-readable attempt disposition. Descendant calls debit the parent.

### Adaptive search adjustment

Adaptive search declares:

- candidate-family size or construction rule;
- maximum adaptation rounds;
- evaluation looks per round;
- public and sealed data access;
- multiplicity, false-discovery, confidence-sequence, or holdout-once policy;
- nominal candidate budget;
- adjusted decision budget after adaptivity; and
- stopping rule.

The selector may not enlarge these values after observing results. A larger
budget starts a new search contract and cannot reuse the old promotion claim as
if the search were unchanged.

## Formal Saturation

`is_saturated(history, declared_budget)` is deterministic under the frozen
saturation policy.

### Preconditions

The function verifies:

- contract, registry, history, and budget hashes;
- history disposition and receipt completeness;
- pending required lane, seed, checkpoint, guardrail, contamination, and
  promotion evaluations;
- budget accounting reconciliation; and
- eligible untried approaches for the exact scope.

### Pseudocode

```text
function is_saturated(history, budget):
    require hashes_and_accounting_valid(history, budget)

    pending = required_pending_trials(history)
    if pending is not empty:
        return decision(false, "required_evaluations_pending", pending)

    if promotion_rule_passed(history):
        return decision(true, "promotion_achieved")

    eligible = eligible_untried_approaches(history, budget.registry)
    if eligible is not empty and budget_can_fund_any(eligible, budget):
        return decision(false, "eligible_candidates_remain", eligible)

    if declared_budget_exhausted(budget):
        return decision(true, "candidate_budget_exhausted")

    if eligible is empty and all_eligible_trials_terminal(history):
        return decision(true, "eligible_registry_exhausted")

    if predeclared_diminishing_returns_rule_passed(history, budget):
        return decision(true, "predeclared_diminishing_returns_rule_met")

    if domain_owner_stop_receipt_exists(history):
        return decision(true, "domain_owner_stop")

    return decision(false, "budget_or_evidence_unresolved")
```

### Saturation decision

The receipt records:

- saturated boolean and reason code;
- capability, population, contract, registry, history, and budget scope;
- declared, spent, remaining, refunded, and disputed budget counters;
- eligible untried approaches;
- pending, blocked, invalidated, terminal, and promoted trials;
- evidence for the stopping predicate;
- decision policy hash; and
- human stop or override receipt.

Blocked is not saturated. An unprovisioned model, unavailable teacher, missing
authority, or absent evaluator is a blocker unless the contract says the
eligible registry is intentionally limited without it.

Saturation never means universal impossibility. It means this capability,
population, registry, contract, and budget reached a declared terminal state.

## Recursive SAME-R

### Child contract

A child SAME-R instance receives:

- parent experiment and intervention IDs;
- parent selection receipt;
- fixed sub-capability and population;
- allowed child approach registry;
- fixed evaluator and guardrails;
- sub-budget;
- maximum depth and child count;
- required return schema; and
- parent-visible failure and saturation rules.

The child may select recursively but cannot change parent fields. It returns
one candidate, one aggregate child receipt, all descendant receipts, and one
saturation decision.

### Parent accounting

The parent records:

- recursion path;
- every descendant registry and policy hash;
- proposal, model, generation, training, evaluation, and human calls at every
  depth;
- child accepted, rejected, blocked, invalidated, and saturated histories;
- selected child candidate and all rejected siblings; and
- total budget debit.

Hidden child calls invalidate the recursive selection receipt.

### Recursive next approach

The next approach is selected in this order:

1. evaluate the current scope for required pending work;
2. compute saturation;
3. enumerate registry-eligible approaches not terminal for scope;
4. obtain proposals under participant budgets;
5. validate causal contracts and authority;
6. reject repetitions that do not declare a changed axis;
7. rank valid proposals under the frozen selector policy;
8. allocate a child sub-budget if the selected approach is recursive;
9. run the child and ingest its receipt as one candidate; and
10. repeat only while the parent budget and saturation decision permit.

## Recursive Selector Evaluation

Selector evaluation is separate from domain candidate evaluation.

### Frozen meta-population

Define:

- history snapshots available at each decision event;
- training, development, public diagnostic, and sealed meta-evaluation history
  splits;
- domain grouping so held-out domains cannot leak through near-duplicate trial
  histories;
- eligible registry at each event;
- budgets and unavailable approaches;
- accepted next actions or outcome-derived utility labels; and
- human authority for ambiguous histories.

### Baselines

Compare against at least one declared baseline:

- human operator decisions;
- deterministic decision table;
- seeded random eligible approach;
- greedy best historical approach; or
- non-recursive selector with the same participant budget.

### Meta-metrics

Potential primary and guardrail metrics include:

- promotion-qualified outcome yield under equal budget;
- regret against the best discoverable sequence under the frozen registry;
- external capability gain obtained per declared budget vector;
- invalid proposal and contract-violation rate;
- guardrail and contamination violation rate;
- negative-result retention rate;
- saturation precision and recall;
- calibration of predicted effect and failure risk;
- diversity of independently tested mechanisms; and
- human override and adjudication rate.

The metric and aggregation rule are frozen. A selector cannot be rewarded for
unsafe exploration, hidden calls, omitted failures, or redefining saturation.

### Replication

Evaluate across required history seeds, proposal seeds, participant-order
permutations, and held-out domains. Report item-level decisions, paired deltas,
uncertainty, failure families, and all recursive call traces.

### Promotion boundary

A selector is promotion-ready only when it beats its baseline under the frozen
meta-metric, passes invalid-selection and guardrail limits, reproduces, and can
replay every selected sequence from receipts. A successful domain candidate
does not prove the selector; the selector must outperform the selection
baseline across the meta-population.

## Selector Failure Taxonomy

| Failure | Correct disposition |
|---|---|
| Raw cross-domain metric comparison | Invalid selector policy. |
| Majority model agreement treated as truth | Evidence-type violation. |
| Participant accesses sealed domain or meta holdout | Contamination failure. |
| Selector changes evaluator or budget after results | Contract invalidation. |
| Repeats rejected method without changed axis | Reject proposal as covered. |
| Hidden descendant calls | Invalidate recursive receipt. |
| Child changes parent objective or guardrail | Reject child contract. |
| Blocked approach called saturated | Saturation error. |
| Budget exhausted claimed as universal impossibility | Claim-boundary failure. |
| Selector finds one winner but loses meta-evaluation | Mechanics proven; selector capability unproven. |
| Human override omitted | Invalidate selection lineage. |
| Negative children dropped from aggregate receipt | Invalidate recursive receipt. |

## Implementation Gate

Before Gamma may claim automatic SAME-R selection, it needs:

- typed approach and participant registry implementation;
- canonical causal/run/metric/selection/saturation object validation;
- content-addressed history store;
- deterministic budget accounting;
- role, data-access, and label-authority enforcement;
- selection receipt generation;
- recursive child accounting;
- formal saturation implementation;
- selector replay; and
- a frozen selector meta-evaluation with a baseline and receipts.

Until all gates exist, operators may manually follow this contract, but status
must remain `operator_selected` rather than `automatically_selected`.
