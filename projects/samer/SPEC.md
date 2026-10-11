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

This specification owns the outer method and capability-transfer profile.
Domain projects own their data, executors, evaluators, artifacts, and promotion
decisions. The documents below divide the detailed contracts by subject.

## Specification Ownership

| Subject | Authoritative document |
|---|---|
| Outer algorithm, trial stages, capability-transfer profile, and operating guidance | This specification |
| Causality, exact lineage, attempts, label authority, contamination, metric evidence, invalidation, and promotion completeness | [Causal and evidence contracts](CAUSAL_AND_EVIDENCE_CONTRACTS.md) |
| Registries, participant roles, selection policy, budgets, saturation, recursion, and selector evaluation | [Selector and saturation contract](SELECTOR_AND_SATURATION.md) |
| Serialized field names, enums, object shapes, hash rule, and schema evolution | [Machine-readable contracts](contracts/README.md) |
| Experiment-register fields and coarse statuses | [Experiment register](experiments/README.md) |
| Current implementation status and validation commands | [README](README.md#what-is-implemented) |
| Optimizer, reward, and RLVR terminology | [Verifier-guided learning](../../docs/VERIFIER_GUIDED_LEARNING.md) |

Change a rule in its authoritative document; other documents link to it rather
than maintaining another field list or schema. Conceptual pseudocode, row
examples, and domain artifact layouts are not serialized contract definitions.
Use the versioned schema and canonical synthetic fixture for wire-format examples.

A domain profile may narrow the general contract but cannot silently relax it.
Historical examples retain their original evidence boundaries and do not define
current policy or authorize execution of archived lanes. Resolve contradictions
between prose, schema, and validator before claiming conformance; do not choose
whichever version admits a candidate. Contract changes require the corresponding
schema/example/validator/test updates where applicable, following the existing
[evolution rule](contracts/README.md#evolution).

## Algorithm Contract

A SAME-R implementation maintains:

- a typed registry of eligible inner approaches;
- a frozen objective, evaluator, guardrails, and comparison budget;
- typed trial history under the [history contract](SELECTOR_AND_SATURATION.md#typed-trial-history);
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

Current implementation and qualification status lives in the
[README](README.md#what-is-implemented). The interface above specifies the
method; it does not assert that every operation is implemented or qualified.

## Automatic Cross-Domain Multi-Model Selector

The [selector contract](SELECTOR_AND_SATURATION.md) owns these requirements.
They specify the intended automatic service, not evidence that selection works.

### Typed approach registry and history

See [typed approach registry](SELECTOR_AND_SATURATION.md#typed-approach-registry)
and [typed trial history](SELECTOR_AND_SATURATION.md#typed-trial-history).

### Registered participants and roles

See [participant registry](SELECTOR_AND_SATURATION.md#participant-registry) and
[multi-model proposal modes](SELECTOR_AND_SATURATION.md#multi-model-proposal-modes).

### Selector inputs and output

See [normalization](SELECTOR_AND_SATURATION.md#cross-domain-normalization),
[selection policy](SELECTOR_AND_SATURATION.md#selection-policy), and
[selection receipts](SELECTOR_AND_SATURATION.md#selection-receipt).

### Recursive selection boundary

See [recursive SAME-R](SELECTOR_AND_SATURATION.md#recursive-same-r) and
[selector evaluation](SELECTOR_AND_SATURATION.md#recursive-selector-evaluation).

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

Write the capability, population, intervention, expected mechanism, metric,
guardrails, controls, and failure interpretations before result-bearing calls.
The [causal contract](CAUSAL_AND_EVIDENCE_CONTRACTS.md#per-intervention-causal-contract)
owns the complete requirements. This example is a claim sketch, not a wire format:

```text
capability: exact grounded legal-span extraction
intervention: construction-gold rows targeting weak categories
causal_hypothesis: exact typed manifestations improve weak-category recall
primary_external_metric: sealed real-document macro span F1
guardrails: zero malformed JSON; no category precision below threshold
control: equal-count deterministic random construction templates
```

## Per-Intervention Causal Contract

Use the [causal contract](CAUSAL_AND_EVIDENCE_CONTRACTS.md#per-intervention-causal-contract)
and [matched operation contract](CAUSAL_AND_EVIDENCE_CONTRACTS.md#matched-operation-contract).
They define the intervention's immutable identity, population, baseline,
independent variable, controls, metric, guardrails, and failure interpretation.
The [canonical schema and fixture](contracts/README.md) own serialized fields;
this specification does not define an alternative payload.

## Frozen Run Contract

Use [run contract and exact lineage](CAUSAL_AND_EVIDENCE_CONTRACTS.md#run-contract-and-exact-lineage)
and [retry and attempt contract](CAUSAL_AND_EVIDENCE_CONTRACTS.md#retry-and-attempt-contract).
Freeze identities and policies before execution; retain actual consumption,
checkpoint outcomes, and completion evidence afterward. The canonical completed
bundle is distinct from the frozen pre-execution plan.

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

Qualification, row generation, student diagnostics, and promotion evaluation
are separate tasks. [Scoped label authority](CAUSAL_AND_EVIDENCE_CONTRACTS.md#scoped-label-authority)
owns receipt identities, scope, allowed actions, denied cells, and invalidation.
Qualification reports overall and per-category counts, precision, recall,
contract thresholds, and malformed-output behavior. A failed category cannot
be authorized by a passing aggregate. Labels outside scope are blocked from
training manifests.

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

[Comprehensive contamination audit](CAUSAL_AND_EVIDENCE_CONTRACTS.md#comprehensive-contamination-audit)
owns the population separation, overlap checks, access audit, approved exceptions,
and blocking result. Domain profiles apply those requirements to their actual
sources and grouping units. Corpus-specific tuning in archived compression
profiles does not waive held-out controls or authorize new research.

### Comprehensive contamination audit

Use the [audit requirements](CAUSAL_AND_EVIDENCE_CONTRACTS.md#comprehensive-contamination-audit);
this section does not maintain a second check list.

### Contract invalidation

Use [contract invalidation](CAUSAL_AND_EVIDENCE_CONTRACTS.md#contract-invalidation)
for triggers, immutable receipts, affected claims, budget disposition, and
replacement lineage.

## Training Execution

Before launch, the executor must verify:

- the declared runtime and dependencies are active;
- the intended accelerator is doing real compute;
- all input manifests and split files exist and hash correctly;
- model/tokenizer/checkpoint identities match the run contract;
- resume state belongs to the same lane and stage;
- artifact and log paths are durable.

After launch, verify that the intended accelerator executed work and that
metrics advance. Training logs must record stage, update, examples consumed,
loss components,
learning rate, overflow/skip state, checkpoint writes, evaluator launches, and
terminal status.

## Checkpoint Selection

Use [checkpoint and denominator completeness](CAUSAL_AND_EVIDENCE_CONTRACTS.md#checkpoint-and-denominator-completeness)
for checkpoint coverage, failed attempts, missing items, selection eligibility,
and the capability-transfer ranking rule. Use [typed metric evidence](CAUSAL_AND_EVIDENCE_CONTRACTS.md#typed-metric-evidence-and-adjudication)
for each checkpoint's scores, guardrails, strata, outputs, and immutable identities.
The final checkpoint has no privileged status.

## Metric And Reward Contract

Keep the metric vector before reducing it. This is a conceptual result view,
not a serialized contract:

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

[Typed metric evidence and adjudication](CAUSAL_AND_EVIDENCE_CONTRACTS.md#typed-metric-evidence-and-adjudication)
owns measurement types, adjudication types, decision roles, scorer identities,
denominators, uncertainty, dissent, and evidence pointers. A scalar cannot
compensate for a blocking failure.

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

Use [search budget](SELECTOR_AND_SATURATION.md#search-budget),
[adaptive adjustment](SELECTOR_AND_SATURATION.md#adaptive-search-adjustment), and
[formal saturation](SELECTOR_AND_SATURATION.md#formal-saturation).
They own counters, rejected-attempt accounting, descendant costs, stopping
predicates, pending-work checks, and scope. Use the canonical schema for the
serialized `saturationDecision`; no alternative JSON shape is defined here.

## Promotion Receipt

[Promotion completeness](CAUSAL_AND_EVIDENCE_CONTRACTS.md#promotion-completeness)
owns the required evidence chain. A domain promotion receipt binds that chain,
the selected immutable artifact, the exact claim and exclusions, deployment
constraints, and the named review decision.

The canonical suite defines `trialReceipt`, `selectionReceipt`, and
`saturationDecision`. It does not define a universal `promotionReceipt` wire
format. Domain owners define that artifact without adding fields to a known
canonical schema version.

## Failure Taxonomy

| Failure | Evidence pattern | Correct conclusion |
|---|---|---|
| No learning | Loss and external metric remain flat. | Recipe or signal did not move the student. |
| Fit without transfer | Loss improves; external metric does not. | Student learned rows but not the target capability. |
| Random-control equivalence | Targeted and random lanes move together. | The targeted heuristic is not established; generic effects remain a hypothesis. |
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

The enwiki9 lane is archived by user decision. This section retains a historical
profile, not execution authority; [project status](../enwiki9/operations/runtime/project_status.json)
controls reopening.

`SRSTC` is the registered enwiki9 name for the Streaming Self-Referential
Semantic Table Coder. `SRSTM` is not currently a registered Gamma mechanism;
when it appears without a separate definition, treat it as a likely reference
to SRSTC rather than silently creating a second algorithm.

SAME-R and SRSTC occupy different layers:

| Layer | SAME-R | SRSTC |
|---|---|---|
| Purpose | Establish whether an intervention transfers capability. | Predict future bits from decoder-rebuilt semantic and structural recurrence. |
| Runtime role | None required; it is an experiment and promotion method. | Archived compressor expert, retrieval table, probability mixer, and router. |
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

The retained SRSTC raw-shadow win and negative unchanged FX2 transfer framed
level 2 as the historical question. They do not authorize a new experiment. A
generic embedding adjacency or page-order proxy would not answer that question.

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

### Tinker-trained browser adapters

- Primary metric: sealed task gain over the byte-identical base checkpoint.
- Guardrails: sealed retention, Doppler import and inference parity, exact
  adapter lineage, and explicit determinism levels.
- Controls: base checkpoint, Tinker PEFT candidate, and any declared training
  or adapter-capacity control under matched populations.
- Selection: exact Doppler browser artifact behavior, not trainer loss or an
  upstream PEFT score.
- Profile: [Tinker browser adapter evaluation](./domains/tinker_browser/README.md).

## Evidence For The Outer Contract

The results below are evidence for SAME-R's evaluation, control, selection, and
promotion rules. They are not evidence that SAME-R automatically chose the
interventions. Every approach selection represented here was made explicitly by
an operator or a domain-specific script. The machine-readable subset is pinned
by repository revision and SHA-256 in the [cross-repository experiment
register](./experiments/experiment-register.jsonl).

| Program | Artifact-backed observation | SAME-R rule supported | Claim boundary |
|---|---|---|---|
| TranslateGemma partial replacement | Targeted `replace05` reached external WMT13 BLEU `33.7353`, above the `32.9055` prior leader. Extending the same data to 6k steps fell to `33.2481`; low-learning-rate polish reached `33.6283` without making a new leader. See the [translation results](../distillation/translation/README.md) and [normalized bundle](../distillation/translation/runs/results_bundle/summary.md). | Select checkpoints by the frozen external metric; neither lower loss, more updates, continuation, nor final-step status has promotion privilege. | This supports external checkpoint selection for this EN/ES experiment. It does not by itself complete random-control or seed-confirmed attribution for `replace05`. |
| WGSL SFT capability transfer | The verified Qwen 3.5 9B seed-11 SFT path moved family-disjoint public compiler-repair pass@1 from `8.36%` to `88.29%` over `299` tasks. See the [WGSL project receipt](../distillation/wgsl/README.md) and immutable [Doppler V10 receipt](https://github.com/clocksmith/doppler/blob/b141d4394adabd4840524d0260ce25d8edbcf7ec/docs/status/wgsl-repair-v10-2026-07-12.md). | Measure capability on an external execution-based evaluator rather than inferring it from training loss. | This establishes one-seed compiler repair, not semantic kernel correctness, seed stability, or promotion readiness. |
| WGSL optimizer comparison | From the selected SFT checkpoint, one clipped GRPO-with-KL update reached `94.98%` public pass@1 with 20 paired wins and zero losses, while the retained DPO lane regressed to `36.79%`. See the [WGSL project receipt](../distillation/wgsl/README.md) and immutable [Doppler V11 receipt](https://github.com/clocksmith/doppler/blob/7625aa7e44ae359d1ec0c4f4a486281274256697/docs/status/wgsl-repair-v11-2026-07-12.md). | Inner methods are swappable under a fixed sampler and verifier, and losing methods remain in history rather than being hidden. | This is a one-seed public compiler-repair optimizer result. It is not a general GRPO-over-DPO claim or semantic-kernel proof. |
| WGSL V12 controlled data curation | After correcting an earlier byte-identical-prefix ablation, V12 consumed every 1,200-row lane once across three seeds. Targeted `external20` reached `99.443%` mean public compiler-repair pass@1 versus `98.439%` for anchor and `98.885%` for matched random replacement, and beat anchor at every seed. See the immutable [Doppler V12 result](https://github.com/clocksmith/doppler/blob/015c628aba6988428e06657a8e81ebd095815aec/docs/status/wgsl-repair-v12-2026-07-13.md). | A targeted intervention must beat both anchor and matched random control under complete lane exposure, frozen external evaluation, and seed replication; names and training loss are insufficient. | The frozen rule reproduced, but none of six per-seed comparisons was significant after Holm correction, the long stratum has nine tasks, and no semantic-kernel or promotion claim follows. |
| Columbo teacher qualification | On a disjoint 6-document, 52-span, 17-category qualification corpus, Claude qualified `14/17` categories and Codex `15/17`, with zero format failures. Both failed `employer` recall (`0.5`) and `person_name` precision (`0.5556`); Claude also missed the `witness_identity` precision threshold. See the immutable [Columbo qualification log](https://github.com/clocksmith/columbo/blob/ab4a87c4ddc5ec0ef72fc71895a1055235ce55e4/docs/hybrid-distillation-plan.md) and the [Claude](https://github.com/clocksmith/columbo/blob/f95167ab207bbdc27b20916650220de637466e57/corpus/training/columbo/teacher-distillation/qualification/claude-p-sonnet.qualification.2026-07-13T00-45-29-853Z.qualification.json) and [Codex](https://github.com/clocksmith/columbo/blob/f95167ab207bbdc27b20916650220de637466e57/corpus/training/columbo/teacher-distillation/qualification/codex-exec.qualification.2026-07-13T00-46-58-234Z.qualification.json) receipts. | Teacher authority is category-scoped and fail-closed; an overall score cannot authorize labels for a failed category. | These receipts qualify teacher/category cells only. They do not prove student transfer or authorize the failed cells. |
| Doppler serving and state reuse | Doppler compare receipts keep output or semantic correctness beside, but separate from, efficiency accounting: the generation receipt records an exact `128/128` token match and a resolved KV-cache plan, while the reranker receipt records semantic correctness and separately times the shared 73-token prefix phase. See the immutable [generation parity receipt](https://github.com/clocksmith/doppler/blob/d089c9d7fd8d67d8ebaf47f869cb81cee163143d/benchmarks/vendors/results/compare_20260709T154633.json) and [reranker prefix receipt](https://github.com/clocksmith/doppler/blob/d089c9d7fd8d67d8ebaf47f869cb81cee163143d/benchmarks/vendors/results/rerank_compare_qwen-3-reranker-0-6b-q4k-ehf16-af32_20260709T192830.json). | KV/prefix reuse is serving evidence only after output parity or the declared semantic contract passes; latency and memory gains do not become capability gains. | These receipts support serving correctness and phase accounting for their exact models and workloads. Without a matched no-reuse ablation, they do not prove that reuse caused a speedup; they also do not show that model capability improved. |
| Null and rejected trials | The V8 WGSL student changed all 72 adapter tensors but scored `0/6` constructive passes, matching the base, and produced 30 policy violations; its mixed lane regressed completion loss and was rejected before replay. Other retained failures include neutral-to-worse kernel geometries, historical translation random-control rows and overtrained checkpoints, the failed DPO policy, and continuations that did not beat their selected anchor. See the immutable [V8 terminal receipt](https://github.com/clocksmith/doppler/blob/90ca8e7d88e945f29a8f0c658a8c4f36d9cc6b26/docs/status/wgsl-student-replay-v8-2026-07-11.json), Doppler's [ruled-out kernel table](https://github.com/clocksmith/doppler/blob/91e45a6bdb427b56c19f2e5c7e3862a7b374034c/docs/developer-guides/16-kernel-performance-optimization.md), Gamma's [translation comparison ledger](../distillation/translation/runs/RUN_COMPARE.md), and the V11 receipt above. | Null, equivalent, regressing, and rejected lanes remain first-class history and constrain the next intervention. | Negative evidence is scoped to the tested shape, seed, artifact, and evaluator; it is not a universal ban on the method family. Historical random controls are retained evidence, not a matched causal control for `replace05`. |

The next EN/ES campaign is governed by the separate
[single-student promotion contract](../distillation/translation/promotion/README.md).
That contract treats all current NativeKD2 and WMT13 results as feasibility and
diagnostic evidence. It does not upgrade the historical translation register
row or reuse WMT13 for future checkpoint selection or promotion.

Together, these results validate SAME-R's outer evaluation discipline: matched
contracts expose invalid comparisons, external metrics select artifacts,
category and regression guardrails limit authority, parity separates serving
from capability, and receipts retain both winners and failures.

They do **not** validate automatic cross-domain approach selection, recursive
self-selection, or autonomous promotion. The [selector claim boundary](SELECTOR_AND_SATURATION.md#selector-claim-boundary)
owns that acceptance requirement; the [README](README.md#what-is-implemented)
owns current implementation status.

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

The corrected matrix is now complete. All nine base-initialized Qwen 3.5 9B
LoRA SFT runs consumed their 1,200 rows once, and every exported adapter matched
its recorded byte digest. The targeted `external20` lane reached `99.443%` mean
public compiler-repair pass@1, compared with `98.439%` for anchor and `98.885%`
for the count-matched random replacement. It beat anchor at all three seeds and
also passed the already-frozen diagnostic selection rule when replayed
descriptively on public outcomes. Mean long-stratum pass@1 was `92.593%` versus
`59.259%` for anchor.

This is `seed_confirmed` evidence inside the detailed SAME-R trial model, but
the cross-repository register remains at coarse `mechanics_proven`: none of the
six per-seed paired control tests is significant after Holm correction, the
long stratum contains only nine tasks, and the experiment has no sealed
semantic-kernel suite. It supports a narrow controlled-data SFT conclusion,
not teacher distillation, RLVR, semantic correctness, adapter inference parity,
runtime performance, or promotion.

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
| `anchor` | Current accepted training rows under the frozen row budget. |
| `curated` | Same row budget, with targeted constructed or adjudicated replacements. |
| `random_control` | Same replacement count and positions, selected deterministically without the quality heuristic. |

If curated and random control move together, the construction heuristic has not
demonstrated value.

#### Deterministic ordering

Rows follow the [deterministic row-order rule](#deterministic-row-order).
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

Every saved checkpoint is evaluated on the same declared checkpoint-selection
population and per-category metrics. Columbo selects by external span behavior
with zero malformed TSV/JSON outputs as a blocking guardrail. A selected lane
must reproduce on the required seeds; sealed promotion evaluation is reserved
for the predeclared final comparison and is not reused to rank checkpoints.
Data sources remain isolated until each proposed edit independently beats anchor
and random control.

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

This is a capability-transfer layout convention. File locations do not define
serialized fields or replace immutable artifact pointers.

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

These actions propose a next intervention. Changes to frozen fields open a new
contract; they do not amend the comparison that produced the observation.

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
- Changing models, recipes, and datasets without declaring a bundle intervention
  and restricting the causal claim to that bundle.
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

This loop applies to controlled-lane capability transfer. Non-training
approaches execute their declared operation under the causal contract instead
of adding a training stage.

1. Freeze the capability, population, intervention, metric, controls, guardrails,
   and failure interpretation under the [causal contract](#per-intervention-causal-contract).
2. Freeze participant authority, search budget, and stopping policy under the
   [selector contract](SELECTOR_AND_SATURATION.md). When selection is automatic,
   retain its selection receipt before executing the selected intervention.
   Operator selection is recorded as operator selection.
3. Freeze the lane/seed plans under [run lineage](#frozen-run-contract).
4. Materialize matched lanes and validate planned manifests, row order,
   positions, splits, authority, and the [contamination audit](#split-and-contamination-contract).
5. Execute each lane, retain all attempts, and record actual consumption and
   completion evidence. Check that the learner encountered the intervention.
6. Evaluate every required checkpoint, retain full denominators and
   [typed metric evidence](#metric-and-reward-contract), and select under the
   [checkpoint rule](#checkpoint-selection).
7. Compare with both controls and complete the required
   [seed confirmation](#statistical-and-seed-confirmation).
8. Emit the [promotion evidence](#promotion-receipt) or retain a terminal
   negative, blocked, or invalidated result.
9. For managed search, retain the [saturation decision](#search-budget-and-formal-saturation)
   before selecting another isolated intervention or recording the stop.

## Adoption Checklist

Use the authoritative checks rather than copying their field lists:

- [Causality and matched operations](CAUSAL_AND_EVIDENCE_CONTRACTS.md#per-intervention-causal-contract).
- [Run lineage](CAUSAL_AND_EVIDENCE_CONTRACTS.md#run-contract-and-exact-lineage)
  and [attempt retention](CAUSAL_AND_EVIDENCE_CONTRACTS.md#retry-and-attempt-contract).
- [Label authority](CAUSAL_AND_EVIDENCE_CONTRACTS.md#scoped-label-authority)
  and [contamination audit](CAUSAL_AND_EVIDENCE_CONTRACTS.md#comprehensive-contamination-audit).
- [Checkpoint completeness](CAUSAL_AND_EVIDENCE_CONTRACTS.md#checkpoint-and-denominator-completeness)
  and [typed metrics](CAUSAL_AND_EVIDENCE_CONTRACTS.md#typed-metric-evidence-and-adjudication).
- [Selection policy](SELECTOR_AND_SATURATION.md#selection-policy),
  [budget](SELECTOR_AND_SATURATION.md#search-budget),
  [saturation](SELECTOR_AND_SATURATION.md#formal-saturation), and
  [recursive accounting](SELECTOR_AND_SATURATION.md#recursive-same-r), where used.
- [Invalidation](CAUSAL_AND_EVIDENCE_CONTRACTS.md#contract-invalidation)
  and [promotion completeness](CAUSAL_AND_EVIDENCE_CONTRACTS.md#promotion-completeness).
- [Canonical contract validation](contracts/README.md#validation)
  and [experiment registration](experiments/README.md).

The [minimal operating loop](#minimal-operating-loop) applies these contracts
to capability-transfer trials. Historical examples do not replace acceptance.

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
