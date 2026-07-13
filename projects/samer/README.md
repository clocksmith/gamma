# SAME-R

**SAME-R** (identifier `samer`) means **Swappable Approaches under Matched
Evaluation and Replication**. Its recursive reading is **SAMER Applies Methods,
Evaluates, Repeats**.

> Different inners. Same rims.

SAME-R is Gamma's implementation-neutral outer method for testing changes to
data, prompts, teachers, training algorithms, models, rules, routers, kernels,
and execution plans. The inner approach may change; the comparison, evaluation,
replication, receipt, and promotion boundaries remain matched.

`Hybrid distillation` is one SAME-R inner approach: teacher-assisted
controlled-lane training. It is not the umbrella term because SAME-R can also
run construction-gold generation, verifier-filtered SFT, active data selection,
prompt search, preference or policy optimization, compact rule distillation,
checkpoint selection, routing, and serving experiments.

This README is canonical for the SAME-R outer method and its capability-transfer
profile. [`VERIFIER_GUIDED_LEARNING.md`](../../docs/VERIFIER_GUIDED_LEARNING.md)
owns the broader optimizer, reward, and RLVR taxonomy. Domain projects own their
data, executors, evaluators, artifacts, and promotion decisions.

## Algorithm Contract

A SAME-R implementation maintains:

- a typed registry of eligible inner approaches;
- a frozen objective, evaluator, guardrails, and comparison budget;
- accepted, rejected, blocked, and saturated trial history;
- immutable run contracts and receipt pointers; and
- a selection policy for the next approach and intervention.

Each inner approach must satisfy this conceptual interface:

```text
propose(history, frozen_contract, proposal_budget) -> intervention
materialize(intervention) -> candidate
execute(candidate, frozen_contract) -> run_artifacts
summarize(run_artifacts) -> receipt
select_approach(history, frozen_contract, selector_budget) -> selection_receipt
is_saturated(history, declared_budget) -> saturation_decision
```

The outer method owns matched evaluation, replication, retention, and promotion.
An inner approach does not select its own promotion metric or silently change
the frozen contract. A SAME-R instance may itself be registered as an inner
approach when it returns one candidate and one receipt under the enclosing
contract; that is the recursion boundary.

Gamma currently executes these operations through domain-specific project
scripts, manifests, scoreboards, and human-selected next interventions. A shared
automatic approach registry and `select_approach(history)` implementation do not
yet exist. Until they do, SAME-R is the canonical algorithm and experiment
contract, while operator selection remains explicit rather than claimed as
automated.

## Automatic Cross-Domain Multi-Model Selector

This section specifies the intended selector. It is not a description of a
currently implemented Gamma service and is not evidence that automatic or
recursive selection works.

### Typed approach registry and history

The registry is immutable by revision and contains one entry per eligible inner
approach:

```text
approach_entry = {
  approach_id,
  approach_revision,
  mechanism_type,
  implementation_pointer,
  eligible_domains,
  eligible_capabilities,
  required_inputs,
  produced_artifacts,
  allowed_roles,
  proposal_contract,
  budget_contract,
  evidence_requirements,
  incompatibilities,
  status,
  accepted_trial_ids,
  rejected_trial_ids,
  blocked_trial_ids,
  saturated_scope_ids
}
```

`status` is `eligible`, `disabled`, `blocked`, or `saturated_for_scope`.
Accepted, rejected, blocked, invalidated, and saturated histories are separate
typed collections; absence from the accepted set is not a rejection receipt.
Every history entry binds the approach revision, causal contract, run contract,
budget debit, disposition reason, and evidence hashes. Registry edits create a
new registry hash and therefore a new selector input.

### Registered participants and roles

Humans, Claude, Codex, Gemini, local models, deterministic programs, and
domain-specific scripts may all be registered participants. A provider name
does not grant authority. Each registration freezes:

- participant ID, provider/model ID, immutable revision when available, and
  owning organization;
- allowed roles: `proposer`, `critic`, `teacher`, `materializer`, `executor`,
  `evaluator`, `selector`, or `adjudicator`;
- allowed domains and data-access boundary;
- wrapper, system instruction, prompt template, tool contract, decoding,
  retry, and timeout hashes;
- proposal, generation, evaluation, token, and human-review budgets; and
- conflict policy when one participant occupies more than one role.

Claude, Codex, and Gemini may propose different interventions, critique each
other's causal contracts, or serve as qualified teachers. Agreement among them
is not capability evidence. A participant may not inspect a sealed holdout,
change the evaluator, enlarge its own budget, or promote its own candidate.
Domain evaluation and the frozen promotion rule remain authoritative.

### Selector inputs and output

The selector consumes normalized summaries rather than comparing raw BLEU,
pass@1, F1, codelength, and latency as if they shared a scale. Each history row
exposes:

```text
trial_summary = {
  domain,
  capability,
  population,
  contract_hash,
  approach_id,
  intervention_id,
  trial_stage,
  disposition,
  effect_vs_anchor,
  effect_vs_random_control,
  uncertainty,
  guardrail_status,
  evidence_quality,
  budget_spent,
  receipt_hashes
}
```

`select_approach(...)` returns a receipt, not only an approach name:

```text
selection_receipt = {
  selector_id,
  selector_revision,
  selector_prompt_or_policy_hash,
  history_hash,
  registry_hash,
  frozen_contract_hash,
  budget_before,
  candidates_considered,
  candidates_rejected_with_reasons,
  selected_approach_id,
  selected_intervention_id,
  causal_contract_hash,
  budget_debit,
  saturation_check,
  human_gate,
  receipt_hash
}
```

Cross-domain history may supply a prior such as "dense checkpoint evaluation
often finds an earlier external peak." It may not transfer a domain conclusion
such as "GRPO wins" or "replacement wins" without a new matched domain trial.

### Recursive selection boundary

A SAME-R instance may be registered as one inner approach of another SAME-R
instance. The child receives a fixed sub-contract and sub-budget, may run its
own registered approaches, and must return exactly one candidate plus one
complete child receipt. The parent treats the child as an approach with:

- a declared maximum recursion depth and maximum child count;
- all descendant proposal, model, training, and evaluation calls charged to
  the parent-visible budget;
- no authority to alter the parent objective, population, evaluator,
  guardrails, or promotion threshold; and
- explicit propagation of every rejected, blocked, and saturated descendant.

Recursion is orchestration, not proof. An automatic-selector claim requires a
frozen meta-evaluation that compares the selector against a named operator or
policy baseline under the same histories, registries, domains, and total
budget. The primary selector metric, regret or opportunity-cost metric,
guardrails, replication policy, and receipt set must be declared before the
comparison. Until such a receipt exists, recursive self-selection remains a
specified capability, not a demonstrated one.

## Capability-Transfer Profile

Capability transfer is the primary SAME-R profile: an intervention attempts to
move a named externally measured behavior into a model, router, rule system, or
other learned component. A transfer claim is an outcome of the trial, not an
assumption built into the method name.

## One-Sentence Contract

A SAME-R capability-transfer claim has this form:

```text
Under a frozen student, training recipe, dataset budget, evaluator, and split,
intervention X improves external capability Y over both anchor and matched
random control, satisfies guardrails G, reproduces across required seeds, and
is bound to complete receipts R.
```

If any clause is missing, the result is evidence for a narrower statement, not
a capability-transfer claim.

## The Questions SAME-R Separates

SAME-R exists to keep these questions from collapsing into one aggregate score:

1. Did the teacher, generator, selector, or curator produce a different data
   distribution?
2. Did the student fit that distribution?
3. Did external behavior improve on untouched evaluation items?
4. Did the named intervention cause the improvement, rather than row count,
   order, schedule, model capacity, evaluator drift, or seed variance?
5. Did important guardrails remain valid?
6. Is the selected artifact reproducible and eligible for promotion?
7. Is a serving improvement changing capability, or only latency and cost?

Training loss directly addresses only question 2.

## Scope

SAME-R applies to:

- supervised fine-tuning;
- logit or representation distillation;
- verifier-filtered synthetic data;
- construction-gold data generation;
- controlled pruning and replacement;
- compact rule, tree, router, and table distillation;
- active-learning acquisition comparisons;
- checkpoint and adapter selection;
- retrieval and reranking students;
- compression predictors and expert routers;
- serving changes that might alter outputs.

SAME-R does not imply:

- policy-gradient reinforcement learning;
- grouped rollouts or advantages;
- hidden teacher reasoning;
- that synthetic data is suitable as the promotion holdout;
- that teacher agreement is a capability metric;
- that lower loss proves useful behavior;
- that a runtime optimization is a model-quality improvement.

## Method Taxonomy

| Term | Meaning | Required comparison |
|---|---|---|
| Controlled-lane training | One frozen recipe is trained on matched data variants. | Anchor, targeted intervention, matched random control. |
| Teacher-assisted distillation | Teacher outputs, scores, logits, or representations supervise a smaller system. | Teacher-qualified intervention versus teacher-free or prior-teacher anchor. |
| Construction-gold training | A generator emits both an input and exact labels because it created the labeled objects. | Constructed targeted rows versus count-matched constructed random rows. |
| Verifier-filtered training | A deterministic or adjudicated verifier accepts candidate rows before training. | Filtered rows versus matched unfiltered or random-filter rows. |
| Compact mechanism distillation | A large teacher guides a small rule, tree, table, sketch, or router. | Tiny mechanism versus same-budget random or hand-designed mechanism. |
| External-behavior selection | Saved checkpoints are ranked by an untouched capability metric. | All eligible checkpoints under one frozen evaluator. |
| Receipt-bound promotion | A result cannot advance without complete lineage and evidence artifacts. | Candidate receipt versus the promotion-state contract. |
| State-reuse serving | Shared prefixes, KV state, or cached features reduce repeated compute. | Output parity first; latency and memory second. |

These mechanisms may be combined only after each new axis is independently
measured.

## Trial Stages

A SAME-R project ledger may record one current detailed trial stage. These
stages describe progress inside SAME-R; they are not the coarse `status` enum
enforced by the cross-repository experiment register.

| State | Minimum evidence | Permitted claim |
|---|---|---|
| `proposed` | Written hypothesis and named metric. | The experiment is specified. |
| `harness_ready` | Frozen splits, evaluator, contracts, and dry-run receipts. | The experiment can be executed comparably. |
| `mechanics_proven` | Training/evaluation completes and artifacts validate. | The pipeline works mechanically. |
| `teacher_qualified` | Teacher clears task and category thresholds on a disjoint qualification set. | The teacher may label only qualified scopes. |
| `transfer_observed` | Targeted lane beats anchor on the primary external metric. | One run observed a capability delta. |
| `control_confirmed` | Targeted lane also beats matched random control. | The selection or construction heuristic has evidence. |
| `seed_confirmed` | Required additional seeds preserve the declared conclusion. | The result is not a single-seed observation. |
| `capability_proven` | External win, guardrails, controls, seeds, and receipts all pass. | The named intervention moved the named capability. |
| `promotion_ready` | Deployment/package constraints and final lineage checks pass. | The selected artifact may enter promotion review. |
| `deployed` | Deployment receipt identifies the exact promoted artifact. | The capability artifact is active in the named environment. |

Stages advance only while their evidence remains valid. A changed dataset,
evaluator, prompt, model, or package may invalidate an earlier stage. A
teacher-free approach skips `teacher_qualified`.

The pointer-only cross-repository register intentionally uses fewer statuses:

| SAME-R trial stage | Experiment-register `status` |
|---|---|
| `proposed` | `proposed` |
| `harness_ready` | `harness_ready` |
| `mechanics_proven` through `seed_confirmed` | `mechanics_proven` |
| `capability_proven` or `promotion_ready` | `capability_proven` |
| `deployed` | `promoted` |

Terminal dispositions map directly to `rejected` or `blocked`. The register
must not claim `capability_proven` from `transfer_observed`,
`control_confirmed`, or `seed_confirmed` alone.

## Ownership Contract

A SAME-R program assigns these roles explicitly:

| Role | Responsibility |
|---|---|
| Domain owner | Defines legal data, target behavior, category semantics, and human authority. |
| Method owner | Defines lanes, controls, trial stages, and causal claim boundary. |
| Executor | Runs training and evaluation under the frozen contract. |
| Teacher owner | Freezes teacher identity, wrapper, instruction, decoding, and qualification evidence. |
| Evaluator owner | Versions the scorer, thresholds, category rules, and malformed-output policy. |
| Artifact owner | Maintains manifests, hashes, scoreboards, and promotion receipts. |
| Serving owner | Proves output parity and records latency, memory, and cache behavior. |

One repository may own several roles, but the receipt must still name them.

## Scientific Claim Template

Before generating rows or launching training, write:

```text
capability:
population:
baseline_artifact:
intervention:
causal_hypothesis:
primary_external_metric:
guardrail_metrics:
anchor_lane:
targeted_lane:
random_control_lane:
sealed_holdout:
promotion_threshold:
seed_policy:
failure_interpretation:
```

Example:

```text
capability: exact grounded legal-span extraction
intervention: construction-gold rows targeting weak categories
causal_hypothesis: exact typed manifestations improve weak-category recall
primary_external_metric: sealed real-document macro span F1
guardrails: zero malformed JSON; no category precision below threshold
control: equal-count deterministic random construction templates
```

## Per-Intervention Causal Contract

Every proposed intervention has its own immutable causal contract before any
prompt generation, row selection, training, or evaluation call. The contract
is narrower than the experiment program: it identifies one independent
variable and the exact matched operation used to test it.

The machine-readable contract records at least:

```json
{
  "schema_version": 1,
  "experiment_id": "",
  "intervention_id": "",
  "capability": "",
  "population": {
    "definition": "",
    "inclusion_rule": "",
    "exclusion_rule": "",
    "unit_of_analysis": "",
    "split_manifest_hashes": {}
  },
  "baseline_artifact": {
    "model_id": "",
    "model_revision": "",
    "base_checkpoint_id": "",
    "base_checkpoint_sha256": ""
  },
  "intervention": {
    "approach_id": "",
    "independent_variable": "",
    "causal_hypothesis": "",
    "matched_operation": {
      "operation": "replace",
      "count": 0,
      "positions": [],
      "position_policy_hash": "",
      "ordering_policy": "",
      "prompt_template_hash": "",
      "generation_call_limit": 0
    }
  },
  "primary_metric": {
    "metric_id": "",
    "direction": "maximize",
    "evaluator_id": "",
    "evaluator_hash": "",
    "promotion_threshold": null
  },
  "guardrails": [],
  "failure_interpretation": {
    "targeted_equals_anchor": "",
    "targeted_equals_random": "",
    "guardrail_failure": "",
    "seed_failure": "",
    "budget_exhaustion": ""
  },
  "lanes": {
    "anchor": "",
    "targeted": "",
    "random_control": ""
  },
  "search": {
    "method": "",
    "adaptive": false,
    "candidate_budget": 0,
    "prompt_generation_call_budget": 0,
    "model_call_budget": 0,
    "evaluation_call_budget": 0,
    "evaluation_look_budget": 0,
    "adjusted_budget_policy": "",
    "multiplicity_policy": ""
  },
  "saturation_rule": {
    "rule_id": "",
    "eligible_reason_codes": [],
    "minimum_effect": null,
    "no_improvement_window": null
  },
  "contract_sha256": ""
}
```

The matched operation includes operation kind, count, exact positions or a
hashed position policy, row-order policy, prompt/instruction hashes, generation
calls, retries, and evaluator looks. If the targeted lane replaces 16 rows,
the random control also replaces 16 rows at the matched positions unless
position is the declared independent variable.

The contract declares the search method: exhaustive, grid, seeded random,
Bayesian, bandit, human-proposed, model-proposed, multi-model, or recursive
SAME-R. Adaptive searches declare both the nominal budget and the adjusted
decision budget, including candidate-family size, repeated evaluator looks,
and the multiplicity or sealed-holdout policy. Calls that return malformed or
rejected candidates still debit the declared budget unless a predeclared
infrastructure-failure rule says otherwise.

The complete field and invalidation contract lives in
[`CAUSAL_AND_EVIDENCE_CONTRACTS.md`](CAUSAL_AND_EVIDENCE_CONTRACTS.md). The
machine-readable definitions and canonical example live under
[`contracts/`](contracts/README.md).

## Frozen Run Contract

Every run emits a human-readable contract line and a machine-readable contract
object before training begins.

```text
[run-contract] experiment_id=<id> lane=<anchor|targeted|random_control> run_name=<name> teacher=<id|none> student=<id> base_revision=<hash> adapter=<targets/rank/alpha/dropout|none> dataset=<manifest> dataset_rows=<n> order_hash=<sha256> evals=<paths> evaluator=<id/hash> decode=<policy> optimizer=<type> schedule=<id> seed=<n> dtype=<dtype> device=<device> resume_from=<path|none> sweep_mode=<live|after_train>
```

The machine-readable form records at least:

```json
{
  "schema_version": 1,
  "experiment_id": "",
  "causal_contract_sha256": "",
  "lane_id": "",
  "run_name": "",
  "teacher": {
    "model_id": null,
    "revision": null,
    "wrapper_hash": null,
    "instruction_hash": null,
    "decode_contract": null
  },
  "student": {
    "model_id": "",
    "model_revision": "",
    "base_checkpoint_id": "",
    "base_checkpoint_sha256": "",
    "tokenizer_revision": "",
    "tokenizer_sha256": "",
    "parameter_manifest_sha256": "",
    "adapter": {
      "type": null,
      "targets": [],
      "rank": null,
      "alpha": null,
      "dropout": null,
      "initialization_method": null,
      "initialization_seed": null,
      "initial_parameters_sha256": null,
      "trainable_parameter_manifest_sha256": null
    }
  },
  "data": {
    "manifest_path": "",
    "manifest_hash": "",
    "row_count": null,
    "ordered_row_ids_path": "",
    "row_order_hash": "",
    "split_hashes": {},
    "consumed_row_count": 0,
    "consumed_prefix_hash": "",
    "resume_cursor": null
  },
  "training": {
    "optimizer": {},
    "schedule": {},
    "precision": "",
    "seed": null,
    "device": "",
    "runtime_mode": "",
    "retry_policy": {
      "maximum_attempts": 1,
      "retryable_failure_codes": [],
      "attempts_share_seed": true,
      "failed_attempts_count_toward_budget": true
    },
    "checkpoint_policy": {
      "save_updates": [],
      "selection_rule": "",
      "terminal_checkpoint_has_privilege": false
    }
  },
  "evaluation": {
    "evaluator_id": "",
    "evaluator_hash": "",
    "decode_policy": {},
    "datasets": [],
    "promotion_rule": "",
    "checkpoint_denominator": {
      "expected_checkpoint_ids": [],
      "evaluated_checkpoint_ids": [],
      "failed_checkpoint_ids": [],
      "omitted_checkpoint_ids": []
    },
    "item_denominators": {}
  },
  "contract_validity": {
    "status": "valid",
    "invalidation_triggers": [],
    "supersedes_run_contract_sha256": null
  },
  "run_contract_sha256": ""
}
```

The run contract hash covers a canonical serialization with the
`run_contract_sha256` field omitted. Exact model, tokenizer, base checkpoint,
adapter initialization, initial adapter parameters, and trainable-parameter
manifest identities are required. A model name or adapter rank without those
hashes is incomplete lineage.

Every attempt is retained. A retry receipt records the attempt number, failure
code, seed, inputs, outputs, and whether the attempt remains in the task and
budget denominators. Retries may recover declared infrastructure failures; they
may not silently erase malformed output, verifier failure, timeout policy, or
an unfavorable model result.

## What Must Stay Frozen

When the independent variable is a data intervention, freeze:

- student model and exact initialization;
- tokenizer and prompt/chat template;
- adapter targets, rank, alpha, dropout, and initialization;
- optimizer, learning rate, scheduler, warmup, weight decay, and clipping;
- batch size, accumulation, row budget, update budget, and stopping policy;
- checkpoint cadence and selection rule;
- dtype, device class, runtime mode, and deterministic settings;
- evaluator version, thresholds, category mapping, and malformed-output policy;
- decoding strategy, temperature, token budget, and retries;
- split membership and item order policy;
- seed for the primary matched comparison.

If one of these must change, open a separate experiment axis. Do not compare it
as if only the data changed.

## Controlled Data Lanes

### Required matched trio

Every data-selection claim begins with:

| Lane | Data policy | Purpose |
|---|---|---|
| `anchor` | Current accepted rows under the frozen budget. | Measures the known baseline. |
| `targeted` | Anchor plus or replacing rows chosen by the named heuristic. | Tests the intervention. |
| `random_control` | Same operation and count, chosen by seeded deterministic random selection. | Tests whether the heuristic matters beyond row count or regularization. |

The lanes must match in total row count unless row count is itself the declared
independent variable. Replacement positions and ordering rules must also match.

### Optional diagnostic lanes

| Lane | Question answered |
|---|---|
| `prune` | Does removing suspect data help without replacement? |
| `replace` | Does targeted replacement add capability beyond pruning? |
| `random_prune` | Does any equal-size reduction behave similarly? |
| `random_replace` | Does any equal-size replacement behave similarly? |
| `teacher_control` | Does the teacher policy matter relative to another frozen teacher policy? |
| `construction_control` | Does the typed construction heuristic matter relative to random templates? |
| `dense_checkpoint` | Did the capability peak before the final checkpoint? |
| `seed_confirmation` | Does the selected conclusion survive another initialization/order seed? |
| `blend` | Do two independently proven capability lanes compose? |
| `polish` | Does narrow continuation improve an already selected artifact? |

Do not launch a blend until each contributor independently beats anchor and its
matched control.

## Row Manifest

Every row has stable, inspectable provenance:

```json
{
  "row_id": "",
  "source_id": "",
  "source_revision": "",
  "source_split": "train",
  "capability_buckets": [],
  "teacher_id": null,
  "teacher_qualified_buckets": [],
  "generator_id": null,
  "template_hash": null,
  "manifest_hash": null,
  "exact_duplicate_key": "",
  "loose_duplicate_key": "",
  "quality_components": {},
  "lane_action": "keep",
  "lane_reason": "",
  "target_hash": ""
}
```

Static quality components may propose rows. They never promote a lane.

## Deterministic Row Order

The default row-order key is:

```text
sha256(seed + "\0" + row_id)
```

Record:

- the seed;
- ordered row IDs;
- the SHA-256 of the ordered row-ID stream;
- duplicate-removal order;
- replacement positions;
- shard boundaries;
- resume cursor and consumed-row count.

Two runs claiming the same lane and seed must have the same order hash.

## Teacher Qualification

Teacher qualification, row generation, student diagnostics, and sealed
promotion evaluation are distinct tasks.

A teacher qualification receipt binds:

- model/provider ID and immutable revision when available;
- command and CLI/runtime version;
- wrapper and instruction hashes;
- qualification corpus and gold hashes;
- decoding, retry, and timeout policies;
- accepted output envelopes;
- malformed-output behavior;
- overall and per-category counts;
- recall, precision, and contract thresholds;
- qualified and unqualified categories.

A teacher may label only the categories and task shapes it qualifies. Overall
quality does not override a failed category threshold.

Qualification creates scoped label authority, represented by a receipt with:

- authority ID; teacher/curator/human identity and immutable revision;
- domain, capability, population, language, category, task shape, output
  envelope, and label-operation scope;
- qualification corpus, instruction, wrapper, decoding, retry, evaluator, and
  threshold hashes;
- allowed positive, negative, abstain, correction, and adjudication actions;
- explicitly denied categories and failure cells;
- valid-from event, invalidation triggers, superseded authority, and human
  owner; and
- downstream row IDs and manifests that consumed the authority.

Authority never transfers by provider family or consensus. Qualification of
Claude on one category does not qualify another Claude revision, Codex,
Gemini, another language, another population, or another output contract.
Multi-model agreement may be recorded as evidence, but each label still names
the authority that permitted it. Labels outside scope are blocked from
training manifests rather than downgraded to unverified data.

### Fail-closed outputs

Teacher output is invalid when it contains an unaccepted envelope, prose where
structured output is required, missing item rows, duplicate item IDs, malformed
spans, or a command/runtime failure.

Invalid output:

- produces zero accepted predictions;
- counts corresponding gold items as missed during qualification;
- does not become a negative training example;
- remains visible in the receipt.

## Construction-Gold Data

Construction-gold generation is preferred when exact labels can be known by
construction.

The generator should:

1. select a versioned template;
2. select a typed manifest;
3. render entities, spans, fields, or faults into the template;
4. record exact offsets, types, and normalized values during insertion;
5. add hard-negative twins and near-boundary cases;
6. validate the rendered example deterministically;
7. emit row, template, manifest, generator, and validator hashes.

Constructed rows are training inputs, not the real-world promotion holdout.
The external holdout remains untouched and representative of deployment.

## Split And Contamination Contract

At minimum, separate:

- teacher qualification;
- prompt or instruction development;
- row construction and selection;
- student training;
- public diagnostics;
- sealed promotion evaluation.

Contamination checks include:

- exact and normalized duplicate hashes;
- source-document, family, repository, matter, page, or block grouping;
- shared-template leakage;
- paraphrase or near-duplicate screening;
- teacher access to sealed documents;
- evaluator examples copied into prompts;
- checkpoint selection against the promotion holdout;
- reuse of prediction outputs as later labels without lineage.

When the domain allows corpus-specific tuning, as enwiki9 does, held-out blocks
still matter as an experimental control. Official full-corpus accounting is the
final target, but a search method that cannot transfer across disjoint blocks is
unlikely to survive counted integration.

### Comprehensive contamination audit

The audit is a machine-readable blocking artifact, not a prose assertion. It
binds the exact revisions and hashes of qualification, prompt-development,
construction, training, public-diagnostic, checkpoint-selection, and sealed
promotion populations. For every pair of populations it records:

- exact, normalized, loose, semantic, template, source-group, repository,
  matter, page, family, and block overlap checks;
- overlap counts, item IDs, checker ID/version/hash, threshold, status, and
  disposition;
- whether a teacher, proposer, critic, selector, evaluator, or human reviewer
  could access each population;
- prompts, few-shot examples, retrieval indexes, caches, generated labels, and
  prior prediction outputs that could carry evaluation information;
- checkpoint-selection looks and whether the sealed holdout was opened;
- approved exceptions with domain-owner authority and a narrowed claim; and
- an overall `pass`, `fail`, or `blocked` result with blocking issue IDs.

Unknown access, missing hashes, or an unexecuted required check is `blocked`,
not `pass`.

### Contract invalidation

A contract is invalidated when any frozen causal input changes, including:

- capability, population, split membership, item order, or denominator;
- baseline model, tokenizer, base checkpoint, adapter initialization, or
  trainable-parameter identity;
- data manifest, operation count, positions, prompt, generation policy, label
  authority, or teacher qualification;
- optimizer, schedule, precision, device class, seed, retry, checkpoint, or
  resume policy;
- evaluator, metric implementation, adjudication policy, decode contract,
  guardrail, threshold, or promotion rule;
- search method, candidate family, adjusted budget, evaluator-look budget,
  recursion depth, or selector policy; or
- contamination status or newly discovered overlap.

Invalidation produces an immutable invalidation receipt naming the old contract
hash, trigger, affected evidence, discovery time, discovering authority, and
replacement contract when one exists. Invalidated runs remain in history but
cannot support selection or promotion. A new hash opens a new comparison axis;
it does not silently amend the old run.

## Training Execution

The executor must verify before launch:

- the declared runtime and dependencies are active;
- the intended accelerator is doing real compute;
- all input manifests and split files exist and hash correctly;
- model/tokenizer/checkpoint identities match the run contract;
- resume state belongs to the same lane and stage;
- metrics are growing after launch;
- artifact and log paths are durable.

Training logs must record stage, update, examples consumed, loss components,
learning rate, overflow/skip state, checkpoint writes, evaluator launches, and
terminal status.

## Checkpoint Selection

The final checkpoint has no privileged status.

For each saved checkpoint, record:

- primary external metric;
- category or family breakdown;
- in-domain guardrails;
- output-contract failures;
- representative predictions or task outputs;
- inference/decode contract;
- model and adapter hashes;
- evaluator and dataset hashes.

The checkpoint denominator is explicit. The receipt lists every checkpoint
required by the frozen cadence, every checkpoint successfully evaluated, every
failed evaluation attempt, and every omission with a predeclared reason code.
The scoreboard reports `expected`, `attempted`, `evaluated`, `failed`, and
`omitted` counts. A missing or failed checkpoint cannot disappear because its
result would weaken the selected candidate.

Selection is lexicographic:

1. reject contract, safety, contamination, and policy failures;
2. reject required category or regression guardrail failures;
3. rank by the declared external capability metric;
4. use declared secondary metrics only for ties;
5. retain losing checkpoints and failure rows.

## Metric And Reward Contract

Keep the metric vector before reducing it:

```text
result = {
  contract_pass,
  task_score,
  category_scores,
  regression_scores,
  safety_pass,
  policy_pass,
  malformed_count,
  payload_cost,
  runtime_cost,
  human_status
}
```

Each component is typed on independent axes:

```text
metric_evidence = {
  metric_id,
  value,
  measurement_type,
  adjudication_type,
  decision_role,
  scorer_id,
  scorer_revision,
  scorer_or_policy_hash,
  prompt_hash,
  population_hash,
  item_denominator,
  missing_count,
  malformed_count,
  uncertainty,
  item_level_artifact,
  receipt_hash
}
```

`measurement_type` is one of:

- `deterministic_measurement`: exact compiler, roundtrip, arithmetic coder,
  schema, hash, or executable oracle;
- `reference_scored`: BLEU, chrF, exact match, F1, or another versioned
  comparison against declared references;
- `learned_metric`: a frozen learned scorer whose identity and calibration are
  part of the receipt;
- `ai_judged`: a frozen model judge with prompt, tools, decoding, retry, and
  failure behavior; or
- `human_judged`: a declared rubric applied by identified reviewers.

`adjudication_type` is `none`, `machine_adjudicated`, `human_adjudicated`, or
`human_and_machine_adjudicated`. This axis records who or what resolves the
metric into a decision. A deterministic compiler result is usually machine
adjudicated; an AI-judged score may later receive human adjudication; a hybrid
gate may require both. `decision_role` is `primary`, `blocking_guardrail`,
`supporting`, or `diagnostic`.

AI or human agreement does not turn a learned judgment into a deterministic
measurement. Every adjudicated result retains dissent, abstentions, overrides,
rubric version, and the pre-adjudication machine evidence.

Do not let a scalar average compensate for a blocking contract or safety
failure.

## Statistical And Seed Confirmation

Prefer item-paired comparisons because lanes share the same evaluation items.
Report:

- per-item baseline and candidate scores;
- paired deltas and confidence intervals;
- category/family deltas;
- regression counts and largest regression;
- effect versus random control;
- seed-level results and dispersion;
- whether the conclusion changes under any declared label protocol.

Run additional seeds only after a targeted lane beats the primary anchor and
random control. Seeds confirm a hypothesis; they should not be used to search
for one favorable run.

## Search Budget And Formal Saturation

Every search declares its method and budget before observing candidate
outcomes. The budget records:

- eligible approach IDs and candidate-family hash;
- proposal, critic, teacher, generation, materialization, training,
  evaluation, adjudication, and human-decision call ceilings;
- model-token ceilings by registered participant;
- candidate, lane, seed, checkpoint, item, and evaluator-look ceilings;
- maximum recursion depth, child count, and descendant calls;
- public-diagnostic access and sealed-holdout access counts;
- adaptive search policy and state hash;
- nominal candidate budget, adjusted decision budget, candidate-family size,
  and multiplicity policy; and
- accounting rules for malformed output, rejected proposals, retries,
  infrastructure failures, blocked trials, and invalidated contracts.

An adaptive method cannot enlarge its family, add evaluator looks, change its
correction, or open the sealed holdout after seeing results. Such a change
invalidates the search contract and starts a new lineage.

`is_saturated(history, declared_budget)` returns this decision object:

```json
{
  "schema_version": 1,
  "saturated": false,
  "reason_code": "eligible_candidates_remain",
  "scope": {
    "capability": "",
    "population_hash": "",
    "frozen_contract_sha256": "",
    "approach_registry_sha256": "",
    "history_sha256": ""
  },
  "budget_declared": {},
  "budget_spent": {},
  "budget_remaining": {},
  "eligible_untried_approach_ids": [],
  "pending_required_trial_ids": [],
  "blocked_trial_ids": [],
  "terminal_trial_ids": [],
  "rule_evidence": [],
  "decision_policy_sha256": "",
  "decision_receipt_sha256": ""
}
```

Permitted terminal reason codes are:

- `promotion_achieved`: the frozen promotion rule passed;
- `candidate_budget_exhausted`: the declared candidate or call budget is
  spent;
- `eligible_registry_exhausted`: every eligible approach has a terminal
  receipt for this contract;
- `predeclared_diminishing_returns_rule_met`: the frozen effect, uncertainty,
  and no-improvement window all pass; or
- `domain_owner_stop`: a named human authority stops the search and records a
  terminal no-promotion decision.

`blocked` is not `saturated`. Pending required evaluations prevent saturation.
Budget exhaustion means only that this registry, contract, and budget are
saturated; it does not prove that the capability cannot improve. Adding an
approach, changing the population, or enlarging the budget opens a new lineage
with a new saturation scope.

The selector algorithm, recursive accounting rules, and selector
meta-evaluation contract are detailed in
[`SELECTOR_AND_SATURATION.md`](SELECTOR_AND_SATURATION.md).

## Promotion Receipt

A promotion receipt contains:

```json
{
  "schema_version": 1,
  "experiment_id": "",
  "candidate_artifact": {"path": "", "sha256": ""},
  "evidence_state": "promotion_ready",
  "claim": "",
  "claim_boundary": "",
  "causal_contract_hash": "",
  "run_contract_hash": "",
  "approach_registry_hash": "",
  "selection_receipt_hash": "",
  "saturation_decision_hash": "",
  "model_revision": "",
  "base_checkpoint_hash": "",
  "adapter_initial_parameters_hash": null,
  "adapter_final_parameters_hash": null,
  "lane_manifest_hashes": {},
  "row_order_hashes": {},
  "ordered_row_id_artifacts": {},
  "teacher_qualification_receipts": [],
  "label_authority_receipts": [],
  "checkpoint_scoreboard_hash": "",
  "checkpoint_denominator": {},
  "selected_checkpoint": "",
  "selected_checkpoint_hash": "",
  "primary_metric": {},
  "metric_evidence_receipts": [],
  "guardrails": {},
  "random_control": {},
  "seed_confirmation": {},
  "contamination_audit": {},
  "retry_receipts": [],
  "contract_invalidation_receipts": [],
  "runtime_receipts": [],
  "deployment_constraints": {},
  "review_status": ""
}
```

Missing evidence is represented explicitly. It is not inferred from prose.

## Failure Taxonomy

| Failure | Evidence pattern | Correct conclusion |
|---|---|---|
| No learning | Loss and external metric remain flat. | Recipe or signal did not move the student. |
| Fit without transfer | Loss improves; external metric does not. | Student learned rows but not the target capability. |
| Random-control equivalence | Targeted and random lanes move together. | Row count or generic regularization explains the change. |
| Format collapse | Task score may rise but malformed outputs increase. | Contract failure blocks promotion. |
| Category tradeoff | Aggregate rises while required category falls. | Candidate fails the category guardrail. |
| Seed instability | Primary run wins; confirmation seeds do not. | Single-seed observation only. |
| Evaluator overfit | Public diagnostic rises; sealed evaluation does not. | Selection adapted to the diagnostic set. |
| Contamination | Split, source, or template leakage is found. | Affected evidence is invalid. |
| Checkpoint overtraining | Earlier checkpoint wins; later checkpoints regress. | Promote earlier checkpoint if all other gates pass. |
| Serving-only win | Outputs match; latency or memory improves. | Deployment efficiency improved, not capability. |
| Teacher imitation only | Student agrees with teacher but external metric is flat. | Imitation improved without proven capability. |

## Serving-Side State Reuse

Serving optimizations are evaluated in two stages:

1. prove output parity under the same model, prompts, decoding, and inputs;
2. measure latency, throughput, memory, and cache behavior.

Prefix and KV reuse receipts should identify:

- shared prefix hash and token count;
- branch/tail inputs;
- reset sequence lengths;
- cache ownership and invalidation;
- output hashes before and after reuse;
- prefill, decode, memory, and batch metrics.

If outputs change, the work is a capability experiment and needs controlled
lanes. If outputs match, it is a serving experiment and should not be credited
as training improvement.

## Relationship To SRSTC

`SRSTC` is the registered enwiki9 name for the Streaming Self-Referential
Semantic Table Coder. `SRSTM` is not currently a registered Gamma mechanism;
when it appears without a separate definition, treat it as a likely reference
to SRSTC rather than silently creating a second algorithm.

SAME-R and SRSTC occupy different layers:

| Layer | SAME-R | SRSTC |
|---|---|---|
| Purpose | Establish whether an intervention transfers capability. | Predict future bits from decoder-rebuilt semantic and structural recurrence. |
| Runtime role | None required; it is an experiment and promotion method. | Active compressor expert, retrieval table, probability mixer, and router. |
| State | Run contracts, lane manifests, checkpoints, metrics, receipts. | Decoded prefix, bounded span tables, sketches, candidates, probabilities, online weights. |
| Primary metric | Domain external behavior plus guardrails. | Exact held-out and constructive codelength after counted costs. |
| Teacher use | Qualify, compare, and distill teachers under controlled lanes. | May consume only a final prefix-rebuildable distilled mechanism. |
| Final artifact | Selected model, adapter, rule, table, router, or no-promotion result. | Deterministic decoder component and arithmetic-coded archive. |

SRSTC can be a SAME-R target. SAME-R can test interventions to improve:

- span segmentation;
- sketch or key construction;
- candidate retrieval;
- candidate usefulness scoring;
- expert selection and abstention;
- fixed-point posterior updates;
- table capacity and eviction;
- integration with FX2 residual probabilities.

SAME-R does not replace SRSTC, and SRSTC does not by itself establish a SAME-R
causal claim. A positive SRSTC shadow receipt proves measured codelength for one
mechanism. It does not prove why a teacher-selected data or feature intervention
worked unless the matched lanes and controls isolate that intervention.

### SAME-R experiment for Qwen-guided SRSTC

The strongest proposed bridge is:

```text
FX2 base probabilities
+ true bits
+ WRT/Wiki causal state
+ SRSTC decoder-rebuilt candidate spans
        |
Qwen3 embedding retrieves or characterizes candidates offline
        |
Qwen3 reranker scores continuation usefulness offline
        |
exact counterfactual coder computes the gold codelength delta
        |
small causal student/router is trained under matched SAME-R lanes
        |
student is replayed against untouched FX2 blocks
        |
only the smallest paying deterministic component enters native replay
```

The exact counterfactual label is:

```text
gain_bits(candidate, state) =
    fx2_codelength_bits - candidate_mixed_codelength_bits
```

Qwen does not define truth. The exact coder does. Qwen proposes candidates,
representations, or rankings that may help the small student learn the useful
regions.

Use these matched lanes:

| Lane | Policy |
|---|---|
| `srstc_anchor` | Existing deterministic SRSTC features and exact counterfactual labels. |
| `srstc_qwen_curated` | Same budget plus rows/features selected by the frozen Qwen hybrid teacher. |
| `srstc_random_control` | Same count and placement selected by deterministic random policy. |

Freeze:

- FX2 trace and exact coder;
- candidate generation and candidate count;
- student architecture and payload budget;
- training recipe, updates, checkpoints, and seed;
- train/validation/test block membership;
- code/table-cost accounting;
- promotion threshold and regression cap.

Select the checkpoint by:

```text
heldout_saved_bytes
- compressed_student_or_rule_bytes
- static_table_bytes
- integration_code_bytes
```

Blocking failures include:

- future text, block IDs, or future-derived page labels in student inputs;
- hidden Qwen vectors, weights, or indexes at decode;
- floating-point nondeterminism in the final coder path;
- curated lane failing to beat random control;
- positive teacher similarity without positive codelength;
- gains that disappear against the FX2 substrate;
- payload cost larger than held-out savings;
- unbounded block regression or online state.

### Evidence ladder for the bridge

| Level | Evidence | Claim |
|---:|---|---|
| 1 | Qwen teacher ranking or representation result. | Chooses a candidate intervention. |
| 2 | Matched SAME-R shadow lanes on exact FX2 residual rows. | Tests whether Qwen selection transfers to codelength. |
| 3 | Tiny student or rule with counted payload on held-out blocks. | Establishes positive net shadow capability. |
| 4 | Multiple disjoint block and seed confirmations. | Establishes transfer stability. |
| 5 | Native archive, roundtrip, determinism, resource, and official accounting receipts. | Establishes a constructive compression result. |

The current SRSTC raw-shadow win and negative unchanged FX2 transfer make level
2 the immediate scientific question. Repeating a generic embedding adjacency
or page-order proxy does not answer it.

## Domain Profiles

### Translation

- Primary metric: external BLEU/chrF or declared domain metric.
- Guardrails: language, protected tokens, numbers, entities, placeholders, and
  in-domain retention.
- Controls: anchor, targeted replacement, random replacement.
- Selection: external metric first; final checkpoint has no privilege.

### WGSL and code

- Primary metric: family-disjoint pass@1 under execution.
- Guardrails: response contract, compile, dispatch, CPU oracle, numerical and
  historical regressions.
- Controls: accepted anchor, targeted verifier-qualified rows, equal-count
  random in-domain rows.
- Selection: sealed execution behavior, not token loss or textual similarity.

### Legal and grounded extraction

- Primary metric: sealed real-document exact grounded-span precision, recall,
  and F1 by category.
- Guardrails: schema validity, exact source anchoring, citations, policy, and
  human-authority boundaries.
- Controls: accepted anchor, targeted construction-gold rows, deterministic
  random construction rows.
- Selection: external category metrics with zero malformed outputs.

### Embedding and reranking

- Primary metric: task-specific retrieval/ranking behavior, not teacher cosine
  alone.
- Guardrails: instruction contract, finite outputs, normalization, category or
  language retention, and payload/runtime limits.
- Controls: baseline pairs, teacher-selected hard examples, matched random hard
  examples.
- Selection: untouched retrieval/ranking tasks and downstream task impact.

### enwiki9 compression and SRSTC

- Primary metric: exact held-out and native arithmetic-coded bytes.
- Guardrails: causality, decoder rebuildability, roundtrip, determinism, block
  regression, memory, runtime, and counted artifact bytes.
- Controls: current SRSTC mechanism, Qwen-curated compact student, matched random
  student/data selection.
- Selection: net bytes after compressed payload and integration cost.

### Simulatte visual construction

- Primary metric: hash-bound gold prompt obligation pass rate in final pixels.
- Guardrails: exact counts, relations, poses, no generic-only geometry, Phase 7
  pixel proof, Scene Proof, and human screenshot adjudication.
- Controls: category-level anchor, prompt-obligation construction, and seeded
  choice from the same candidate set.
- Selection: sealed screenshot behavior, not grammar IDs or self-reported
  intermediate receipts.
- Profile: [Simulatte construction](./domains/simulatte/README.md).

## Evidence For The Outer Contract

The results below are evidence for SAME-R's evaluation, control, selection, and
promotion rules. They are not evidence that SAME-R automatically chose the
interventions. Every approach selection represented here was made explicitly by
an operator or a domain-specific script. The machine-readable subset is pinned
by repository revision and SHA-256 in the [cross-repository experiment
register](../distillation/shared/experiments/experiment-register.jsonl).

| Program | Artifact-backed observation | SAME-R rule supported | Claim boundary |
|---|---|---|---|
| TranslateGemma partial replacement | Targeted `replace05` reached external WMT13 BLEU `33.7353`, above the `32.9055` prior leader. Extending the same data to 6k steps fell to `33.2481`; low-learning-rate polish reached `33.6283` without making a new leader. See the [translation results](../distillation/translation/README.md) and [normalized bundle](../distillation/translation/runs/results_bundle/summary.md). | Select checkpoints by the frozen external metric; neither lower loss, more updates, continuation, nor final-step status has promotion privilege. | This supports external checkpoint selection for this EN/ES experiment. It does not by itself complete random-control or seed-confirmed attribution for `replace05`. |
| WGSL SFT capability transfer | The verified Qwen 3.5 9B seed-11 SFT path moved family-disjoint public compiler-repair pass@1 from `8.36%` to `88.29%` over `299` tasks. See the [WGSL project receipt](../distillation/wgsl/README.md) and immutable [Doppler V10 receipt](https://github.com/clocksmith/doppler/blob/b141d4394adabd4840524d0260ce25d8edbcf7ec/docs/status/wgsl-repair-v10-2026-07-12.md). | Measure capability on an external execution-based evaluator rather than inferring it from training loss. | This establishes one-seed compiler repair, not semantic kernel correctness, seed stability, or promotion readiness. |
| WGSL optimizer comparison | From the selected SFT checkpoint, one clipped GRPO-with-KL update reached `94.98%` public pass@1 with 20 paired wins and zero losses, while the retained DPO lane regressed to `36.79%`. See the [WGSL project receipt](../distillation/wgsl/README.md) and immutable [Doppler V11 receipt](https://github.com/clocksmith/doppler/blob/7625aa7e44ae359d1ec0c4f4a486281274256697/docs/status/wgsl-repair-v11-2026-07-12.md). | Inner methods are swappable under a fixed sampler and verifier, and losing methods remain in history rather than being hidden. | This is a one-seed public compiler-repair optimizer result. It is not a general GRPO-over-DPO claim or semantic-kernel proof. |
| WGSL V12 lane correction | The earlier 800-step schedule exposed byte-identical prefixes in nominal `anchor`, `external20`, and `random20` lanes, so the comparison did not expose the declared intervention. V12 seed/hash-orders 1,200 rows per lane, records the order hash, and consumes every lane once. See the immutable [Doppler V12 design receipt](https://github.com/clocksmith/doppler/blob/c55d932a1676a212241847b5e3c5d9cb0b8491cd/docs/status/wgsl-repair-v12-design-2026-07-12.md). | Manifest names are insufficient: row-order hashes, consumed-row counts, full-lane exposure, and resume cursors belong in the run contract. | This validates a harness correction and invalidates the earlier attribution. V12 capability results must come from the corrected nine-run matrix. |
| Columbo teacher qualification | On a disjoint 6-document, 52-span, 17-category qualification corpus, Claude qualified `14/17` categories and Codex `15/17`, with zero format failures. Both failed `employer` recall (`0.5`) and `person_name` precision (`0.5556`); Claude also missed the `witness_identity` precision threshold. See the immutable [Columbo qualification log](https://github.com/clocksmith/columbo/blob/ab4a87c4ddc5ec0ef72fc71895a1055235ce55e4/docs/hybrid-distillation-plan.md) and the [Claude](https://github.com/clocksmith/columbo/blob/f95167ab207bbdc27b20916650220de637466e57/corpus/training/columbo/teacher-distillation/qualification/claude-p-sonnet.qualification.2026-07-13T00-45-29-853Z.qualification.json) and [Codex](https://github.com/clocksmith/columbo/blob/f95167ab207bbdc27b20916650220de637466e57/corpus/training/columbo/teacher-distillation/qualification/codex-exec.qualification.2026-07-13T00-46-58-234Z.qualification.json) receipts. | Teacher authority is category-scoped and fail-closed; an overall score cannot authorize labels for a failed category. | These receipts qualify teacher/category cells only. They do not prove student transfer or authorize the failed cells. |
| Doppler serving and state reuse | Doppler compare receipts keep output or semantic correctness beside, but separate from, efficiency accounting: the generation receipt records an exact `128/128` token match and a resolved KV-cache plan, while the reranker receipt records semantic correctness and separately times the shared 73-token prefix phase. See the immutable [generation parity receipt](https://github.com/clocksmith/doppler/blob/d089c9d7fd8d67d8ebaf47f869cb81cee163143d/benchmarks/vendors/results/compare_20260709T154633.json) and [reranker prefix receipt](https://github.com/clocksmith/doppler/blob/d089c9d7fd8d67d8ebaf47f869cb81cee163143d/benchmarks/vendors/results/rerank_compare_qwen-3-reranker-0-6b-q4k-ehf16-af32_20260709T192830.json). | KV/prefix reuse is serving evidence only after output parity or the declared semantic contract passes; latency and memory gains do not become capability gains. | These receipts support serving correctness and phase accounting for their exact models and workloads. Without a matched no-reuse ablation, they do not prove that reuse caused a speedup; they also do not show that model capability improved. |
| Null and rejected trials | The V8 WGSL student changed all 72 adapter tensors but scored `0/6` constructive passes, matching the base, and produced 30 policy violations; its mixed lane regressed completion loss and was rejected before replay. Other retained failures include neutral-to-worse kernel geometries, historical translation random-control rows and overtrained checkpoints, the failed DPO policy, and continuations that did not beat their selected anchor. See the immutable [V8 terminal receipt](https://github.com/clocksmith/doppler/blob/90ca8e7d88e945f29a8f0c658a8c4f36d9cc6b26/docs/status/wgsl-student-replay-v8-2026-07-11.json), Doppler's [ruled-out kernel table](https://github.com/clocksmith/doppler/blob/91e45a6bdb427b56c19f2e5c7e3862a7b374034c/docs/developer-guides/16-kernel-performance-optimization.md), Gamma's [translation comparison ledger](../distillation/translation/runs/RUN_COMPARE.md), and the V11 receipt above. | Null, equivalent, regressing, and rejected lanes remain first-class history and constrain the next intervention. | Negative evidence is scoped to the tested shape, seed, artifact, and evaluator; it is not a universal ban on the method family. Historical random controls are retained evidence, not a matched causal control for `replace05`. |

Together, these results validate SAME-R's outer evaluation discipline: matched
contracts expose invalid comparisons, external metrics select artifacts,
category and regression guardrails limit authority, parity separates serving
from capability, and receipts retain both winners and failures.

They do **not** validate automatic cross-domain approach selection, recursive
self-selection, or autonomous promotion. Gamma still lacks the shared typed
approach registry and `select_approach(history)` implementation described in
the algorithm contract. The recursive selector remains an explicit
implementation boundary until it proposes interventions, receives receipts,
and reproduces better selections under an enclosing frozen SAME-R contract.

## Worked Applications And Claim Boundaries

These examples illustrate how to apply SAME-R. A historical result remains bound
to its original receipts. A planned profile does not become evidence merely by
appearing here.

### TranslateGemma partial replacement

The TranslateGemma EN/ES program demonstrates why the targeted intervention,
random controls, and checkpoint selection must remain separate.

Starting evidence:

- prior leader `pack06/prune10`: 1,568 rows, external BLEU `32.9055`;
- full replacement `pack06/replace10`: statically plausible but below the
  leader after training;
- a seed-only rerun was weaker;
- low-learning-rate continuation of the old leader was weaker.

The next experiment reconstructed the frozen best-five data mix and narrowed
the suspected edit:

| Lane | Intervention | Rows | Best external BLEU | Interpretation |
|---|---|---:|---:|---|
| `prune10` | Previous broad prune leader. | 1,568 | 32.9055 | Anchor leader. |
| `prune05` | Remove only the highest-risk half. | 1,584 | 32.8755 | Near miss; smaller pruning alone did not explain a win. |
| `replace05` | Replace those 16 rows with top frozen candidates. | 1,600 | 33.7353 | New externally selected leader. |
| `replace05_6k` | Same data, longer schedule. | 1,600 | 33.2481 | More updates reduced external quality. |
| `replace05_polish` | Continue from the leader at lower LR. | 1,600 | 33.6283 | Close, but no new leader. |

The reusable conclusions are limited and concrete:

1. Narrow partial replacement beat the prior student under the external metric.
2. Pruning alone did not produce the same improvement.
3. Longer training and polishing did not improve the selected capability.
4. The best checkpoint, not the terminal checkpoint, defined the candidate.
5. Static row quality proposed the lane but did not establish the result.

This does not prove that partial replacement is universally superior. It proves
that one frozen partial-replacement intervention won in that experiment.

### Doppler WGSL V10 and V12

The WGSL repair program demonstrates both a strong observed capability movement
and the need to restrict the claim.

The V10 recipe used:

- Qwen 3.5 9B student;
- rank-32 LoRA across attention and MLP projections;
- completion-only replacement targets;
- hundreds of compiler-reproducing rows;
- family-disjoint evaluation;
- a frozen sampler and Radeon compiler verifier.

The seed-11 adapter moved public family-disjoint compiler-repair pass@1 from
`8.36%` to `88.29%` on `299` tasks. The external Zero-TVM subgroup moved from
`9.73%` to `71.68%`.

The exact claim boundary remains narrower than those large deltas:

- compilation repair is demonstrated;
- semantic ML-kernel correctness is not demonstrated;
- a single seed does not establish stability;
- missing anchor/curated/random data controls prevent attribution to one data
  source;
- no RLVR claim follows from SFT;
- promotion still requires sealed dispatch, CPU-oracle, numerical,
  metamorphic, and historical-regression checks.

V11 then isolated optimizer behavior from the selected SFT checkpoint. Both
optimizer lanes used only the separate `285`-task diagnostic split. Twelve
groups supplied `96` nonzero-advantage samples; `11` groups had constructive
verifier variance and one varied only on exact-reference match.

One clipped GRPO-with-KL update moved public pass@1 from `88.29%` to `94.98%`,
with `20` paired wins and zero losses. Zero-TVM pass@1 moved from `71.68%` to
`86.73%`. The matched `400`-step DPO lane overfit `11` pairs and regressed to
`36.79%`, so it is rejected.

This supports a one-seed public compiler-repair RLVR result. It does not prove
semantic kernel correctness or promotion readiness, and it does not resolve
the missing SFT data-lane controls or seed confirmations.

V12 corrects a data-ablation flaw: an earlier update budget consumed the same
prefix across nominal lanes, so the experiment did not actually expose the
replacement difference. V12 hash-orders and consumes the complete matched lane
budgets. This is a core SAME-R lesson: different manifest names do not prove that
the learner consumed different interventions.

### Gamma, Doppler, and Columbo grounded extraction profile

This is a cross-repository application profile, not a completed capability
claim. Columbo owns the domain truth and promotion policy; Gamma owns the
controlled training execution; Doppler contributes teacher qualification,
runtime evidence patterns, and serving primitives.

#### Target behavior

The external target is sealed-holdout extraction quality:

- exact grounded spans;
- per-category recall and precision;
- output-contract validity;
- real-document evaluation isolated from synthetic construction.

Training loss remains diagnostic. A checkpoint that emits no usable findings
cannot win because its loss is lower.

#### Frozen training recipe

The planned primary comparison freezes:

- student checkpoint and tokenizer;
- rank `32`, alpha `64`, dropout `0.05`;
- all seven declared attention/MLP projection targets;
- completion-masked causal-LM loss;
- optimizer, schedule, update budget, dtype, device, and seed;
- row count, deterministic row order, evaluator, and decode contract.

Only the data-lane intervention changes.

#### Matched lanes

| Lane | Columbo extraction policy |
|---|---|
| `anchor` | Current accepted training rows. |
| `curated` | Anchor plus the targeted constructed or adjudicated rows. |
| `random_control` | Anchor plus the same number of deterministically selected rows without the quality heuristic. |

If curated and random control move together, the construction heuristic has not
demonstrated value.

#### Deterministic ordering

Rows use:

```text
sha256(seed + "\0" + row_id)
```

The order hash enters lineage. Resume receipts record the consumed prefix so a
lane cannot silently skip the rows that distinguish it from its control.

#### Teacher qualification

Qualification, row labeling, and student holdout remain disjoint. The supplied
qualification snapshot contains:

- six synthetic/public documents;
- 52 exact gold spans;
- all 17 categories;
- category thresholds recall `>= 0.8` and precision `>= 0.7`.

Receipts bind teacher, CLI, command, corpus, instruction, thresholds,
per-category counts, and format failures. In the supplied snapshot, Claude
qualifies 14 categories and Codex 15; neither qualifies `employer` or
`person_name`. Those categories cannot use their outputs as qualified teacher
evidence unless a later versioned qualification receipt changes the result.

#### Fail-closed extraction output

Accepted output envelopes are explicitly enumerated. Prose, malformed
envelopes, missing document rows, and command failures produce zero accepted
predictions and count the corresponding qualification gold as missed. Invalid
teacher output is never converted into a negative student label.

#### Construction-gold lane

The targeted constructed lane does not ask a teacher to rediscover spans in
finished prose. It uses:

1. a teacher- or curator-authored document template;
2. a typed entity manifest;
3. deterministic insertion of every entity;
4. exact character offsets emitted during rendering;
5. hard-negative twins such as public names, partial identifiers, and
   citation-shaped strings;
6. generator, template, manifest, and rendered-row hashes.

These rows are training-only. They cannot enter the real-document sealed KPI
holdout.

#### Checkpoint and seed policy

Every saved checkpoint is evaluated on the same sealed per-category metrics.
Columbo selects by external span behavior with zero malformed TSV/JSON outputs
as a blocking guardrail. A selected lane must then reproduce on additional
seeds. Data sources remain isolated until each proposed edit independently
beats anchor and random control.

#### Receipt-visible promotion

Promotion rejects:

- evaluation-source contamination;
- split reuse;
- empty predictions;
- blocking F1 or category regressions;
- duplicate adapter hashes presented as different candidates;
- malformed output;
- missing comparison lanes;
- missing generator, template, manifest, or qualification hashes.

#### Serving-side prefix reuse

The JSON serving path may reuse a shared prefix containing matter, policy,
source/release context, categories, and excerpts, then branch into contextual
redaction and clause/responsiveness tails.

The scan-loop extension may use prefix KV retention, reset to a recorded
sequence length, token-to-character anchoring, and category-specific candidate
scores. It remains a serving experiment until output parity is proven. If the
changed scan loop alters findings, it becomes a separate SAME-R capability axis.

#### Explicit exclusions

This profile does not use policy gradients, advantages, grouped rollouts,
hidden teacher reasoning, synthetic KPI holdouts, teacher similarity as the
promotion metric, or customer documents in remote teacher calls. It is
qualification-gated controlled-lane SFT with deterministic verification and
external capability selection.

### Interpreting null and negative results

A SAME-R program records null and negative lanes as first-class evidence:

- targeted equals random: the heuristic is not established;
- lower loss with unchanged external score: fit without transfer;
- one seed wins and confirmations fail: unstable observation;
- final checkpoint loses to an earlier checkpoint: overtraining after the
  capability peak;
- teacher agrees with student but exact verifier is flat: imitation without
  capability;
- Qwen improves SRSTC semantic ranking but not FX2 codelength: semantic proxy
  failed substrate transfer;
- shadow compression win disappears after payload accounting: non-paying
  mechanism;
- native replay loses despite shadow evidence: integration shape failed.

These outcomes narrow the search. They are not rewritten as successes and are
not hidden from the experiment register.

## Canonical Artifact Layout

```text
runs/<experiment_id>/<lane_id>/<seed>/
  run_contract.json
  run_contract.txt
  inputs/
    rows.jsonl
    rows.manifest.jsonl
    rows.order.txt
    split_manifest.json
  qualification/
    teacher_receipt.json
    failures.jsonl
  training/
    metrics.jsonl
    checkpoint-*/
  evaluation/
    manifest.jsonl
    scoreboard.md
    scoreboard_rows.csv
    checkpoint-*/
      summary.json
      predictions.jsonl
      failures.jsonl
  receipts/
    contamination_audit.json
    runtime_receipt.json
    promotion_receipt.json
  logs/
    train.log
    evaluate.log
    rebuild.log
```

Domain-specific deterministic artifacts, such as compiler logs, span ledgers,
coder traces, or archive hashes, live beside the relevant checkpoint receipt.

## Decision Table

| Observation | Next action |
|---|---|
| Targeted equals random control | Reject heuristic attribution; inspect generic row-count effect. |
| Targeted beats anchor and random | Run seed confirmation with the frozen contract. |
| External rises then falls | Increase checkpoint density around the observed peak. |
| In-domain rises but external falls | Record specialization; do not promote for the external capability. |
| External rises but a blocking category falls | Narrow the intervention or add an independently proven anchor lane. |
| Prune beats replace | Test smaller prune and partial replacement around the suspect rows. |
| Replace beats prune | Audit paying replacement rows and build a narrower targeted pool. |
| Polish worsens | Preserve the earlier selected checkpoint and stop that continuation axis. |
| Seed confirmation fails | Reject stable-transfer claim; change the intervention rather than searching seeds. |
| Teacher fails a category | Do not use its labels as qualified evidence for that category. |
| Student matches teacher but verifier is flat | Reject capability-transfer claim. |
| Serving parity passes and latency improves | Promote as serving evidence only. |
| Compression shadow wins but native replay loses | Retire unchanged integration shape; inspect substrate transfer. |

## Anti-Patterns

- Calling every mixture of data or models `hybrid` without naming the isolated
  intervention.
- Comparing different models, recipes, and datasets in one causal claim.
- Selecting the final checkpoint because it is final.
- Promoting lower training loss without external behavior.
- Omitting random controls for data-selection claims.
- Seed roulette before a primary controlled-lane win.
- Using the same items for teacher qualification and student promotion.
- Treating invalid teacher output as negative supervision.
- Hiding malformed outputs or failed commands from denominators.
- Blending unproven lanes so one win can mask one loss.
- Treating learned similarity as a deterministic verifier.
- Calling output-changing serving work a latency-only optimization.
- Shipping hidden teacher weights, indexes, labels, or future information in a
  compression decoder.

## Minimal Operating Loop

1. Name one capability and one primary external metric.
2. Freeze the population, causal hypothesis, guardrails, failure
   interpretation, matched operation, and causal-contract hash.
3. Freeze participant roles, scoped label authority, approach-registry hash,
   search method, adjusted budget, recursion limits, and saturation rule.
4. Freeze exact model, tokenizer, base-checkpoint, adapter-initialization,
   training, retry, checkpoint, evaluation, and adjudication identities.
5. Materialize anchor, targeted, and random-control lanes.
6. Validate manifests, ordered row IDs, positions, consumed-row hashes,
   splits, label authority, and the contamination audit.
7. Train the same recipe on every lane and retain every attempt.
8. Evaluate every required checkpoint and preserve the full checkpoint and
   item denominators.
9. Compare targeted versus anchor and random control under typed metric
   evidence.
10. Inspect category, item, failure, adjudication, and contract-invalidation
    deltas.
11. Confirm the selected conclusion across required seeds.
12. Emit a selection receipt naming considered and rejected approaches.
13. Build the promotion receipt or record the terminal negative result.
14. Evaluate `is_saturated(history, declared_budget)` and retain its decision
    receipt.
15. Select the next isolated intervention, or stop for the recorded saturation
    reason.

## Adoption Checklist

- [ ] Canonical capability and metric named.
- [ ] Population, causal hypothesis, matched operation, and failure
      interpretation frozen per intervention.
- [ ] Legacy or ambiguous method name replaced by a mechanism-specific term.
- [ ] Typed approach registry and accepted/rejected/blocked/saturated histories
      hashed.
- [ ] Human, Claude, Codex, Gemini, program, and other participant roles,
      prompts, revisions, tools, and budgets frozen where used.
- [ ] Anchor, targeted, and random-control lanes materialized.
- [ ] Run contract frozen and hashed.
- [ ] Exact model, tokenizer, base checkpoint, adapter initialization, initial
      parameter, and trainable-parameter hashes recorded.
- [ ] Row provenance, ordered row IDs, operation positions, consumed prefix,
      deterministic order, and denominator recorded.
- [ ] Teacher qualification disjoint from training and promotion evaluation.
- [ ] Scoped label-authority receipts block unqualified categories, task
      shapes, populations, and label operations.
- [ ] Construction-gold rows excluded from the real-world KPI holdout.
- [ ] Comprehensive contamination audit passed with access paths and overlap
      results visible.
- [ ] Retry attempts and their budget/denominator dispositions retained.
- [ ] Every checkpoint evaluated under the same external contract.
- [ ] Expected, attempted, evaluated, failed, and omitted checkpoint counts
      reconcile.
- [ ] Malformed outputs fail closed and remain in denominators.
- [ ] Every metric declares measurement type, adjudication type, decision role,
      scorer identity, uncertainty, and item-level evidence.
- [ ] Category/family regressions inspected.
- [ ] Seed policy completed.
- [ ] Serving evidence separated from capability evidence.
- [ ] Search method, adaptive state, nominal budget, adjusted decision budget,
      evaluator looks, multiplicity policy, and recursive descendant costs
      recorded.
- [ ] Selection receipt lists every considered and rejected approach.
- [ ] Formal saturation decision records scope, budget, pending work, and reason.
- [ ] Contract invalidation triggers and superseding hashes reconciled.
- [ ] Promotion receipt binds every relevant artifact hash.
- [ ] Negative and null lanes retained.

## Naming Guidance

Use `SAME-R` only for an experiment that has a frozen contract, controlled lane or
otherwise justified causal comparison, external behavior metric, guardrails,
and a receipt-visible trial stage.

Use narrower mechanism names when appropriate:

- `teacher-assisted distillation`;
- `construction-gold SFT`;
- `verifier-filtered SFT`;
- `targeted replacement lane`;
- `compact router distillation`;
- `external-behavior checkpoint selection`;
- `state-reuse serving optimization`.

Do not rename SRSTC to SAME-R. SRSTC is an inner compression mechanism; SAME-R
is the outer method used to test and improve it.
