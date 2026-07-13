# Evidence-Gated Capability Transfer

Evidence-Gated Capability Transfer (EGCT) is Gamma's canonical method for
moving a named capability into a model, router, rule system, or other learned
component while preserving causal attribution and reproducible promotion
evidence.

`Hybrid distillation` is retained as a legacy name for one EGCT subtype:
teacher-assisted controlled-lane training. It is not the umbrella term because
EGCT also covers construction-gold data, verifier-filtered SFT, active data
selection, compact rule distillation, checkpoint selection, and serving changes
that must be evaluated separately from capability movement.

This document is the controlled-experiment companion to
[`VERIFIER_GUIDED_LEARNING.md`](VERIFIER_GUIDED_LEARNING.md). That document
defines the broader method taxonomy. This document defines how a specific
capability-transfer claim is designed, executed, compared, recorded, and
promoted.

## One-Sentence Contract

An EGCT claim has this form:

```text
Under a frozen student, training recipe, dataset budget, evaluator, and split,
intervention X improves external capability Y over both anchor and matched
random control, satisfies guardrails G, reproduces across required seeds, and
is bound to complete receipts R.
```

If any clause is missing, the result is evidence for a narrower statement, not
a capability-transfer claim.

## The Questions EGCT Separates

EGCT exists to keep these questions from collapsing into one aggregate score:

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

EGCT applies to:

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

EGCT does not imply:

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

## Evidence States

Every registered EGCT experiment has exactly one current evidence state.

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

States are monotonic only when their evidence remains valid. A changed dataset,
evaluator, prompt, model, or package may invalidate an earlier state.

## Ownership Contract

An EGCT program assigns these roles explicitly:

| Role | Responsibility |
|---|---|
| Domain owner | Defines legal data, target behavior, category semantics, and human authority. |
| Method owner | Defines lanes, controls, evidence states, and causal claim boundary. |
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
    "revision": "",
    "initial_checkpoint_hash": "",
    "adapter_targets": [],
    "rank": null,
    "alpha": null,
    "dropout": null
  },
  "data": {
    "manifest_path": "",
    "manifest_hash": "",
    "row_count": null,
    "row_order_hash": "",
    "split_hashes": {}
  },
  "training": {
    "optimizer": {},
    "schedule": {},
    "precision": "",
    "seed": null,
    "device": "",
    "runtime_mode": ""
  },
  "evaluation": {
    "evaluator_id": "",
    "evaluator_hash": "",
    "decode_policy": {},
    "datasets": [],
    "promotion_rule": ""
  }
}
```

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

Each component declares an evidence type:

- `deterministic`;
- `reference_scored`;
- `learned_metric`;
- `ai_judge`;
- `human_adjudicated`.

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
  "run_contract_hash": "",
  "lane_manifest_hashes": {},
  "row_order_hashes": {},
  "teacher_qualification_receipts": [],
  "checkpoint_scoreboard_hash": "",
  "selected_checkpoint": "",
  "selected_checkpoint_hash": "",
  "primary_metric": {},
  "guardrails": {},
  "random_control": {},
  "seed_confirmation": {},
  "contamination_audit": {},
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

EGCT and SRSTC occupy different layers:

| Layer | EGCT | SRSTC |
|---|---|---|
| Purpose | Establish whether an intervention transfers capability. | Predict future bits from decoder-rebuilt semantic and structural recurrence. |
| Runtime role | None required; it is an experiment and promotion method. | Active compressor expert, retrieval table, probability mixer, and router. |
| State | Run contracts, lane manifests, checkpoints, metrics, receipts. | Decoded prefix, bounded span tables, sketches, candidates, probabilities, online weights. |
| Primary metric | Domain external behavior plus guardrails. | Exact held-out and constructive codelength after counted costs. |
| Teacher use | Qualify, compare, and distill teachers under controlled lanes. | May consume only a final prefix-rebuildable distilled mechanism. |
| Final artifact | Selected model, adapter, rule, table, router, or no-promotion result. | Deterministic decoder component and arithmetic-coded archive. |

SRSTC can be an EGCT target. EGCT can test interventions to improve:

- span segmentation;
- sketch or key construction;
- candidate retrieval;
- candidate usefulness scoring;
- expert selection and abstention;
- fixed-point posterior updates;
- table capacity and eviction;
- integration with FX2 residual probabilities.

EGCT does not replace SRSTC, and SRSTC does not by itself establish an EGCT
causal claim. A positive SRSTC shadow receipt proves measured codelength for one
mechanism. It does not prove why a teacher-selected data or feature intervention
worked unless the matched lanes and controls isolate that intervention.

### EGCT experiment for Qwen-guided SRSTC

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
small causal student/router is trained under matched EGCT lanes
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
| 2 | Matched EGCT shadow lanes on exact FX2 residual rows. | Tests whether Qwen selection transfers to codelength. |
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

## Worked Applications And Claim Boundaries

These examples illustrate how to apply EGCT. A historical result remains bound
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
budgets. This is a core EGCT lesson: different manifest names do not prove that
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
changed scan loop alters findings, it becomes a separate EGCT capability axis.

#### Explicit exclusions

This profile does not use policy gradients, advantages, grouped rollouts,
hidden teacher reasoning, synthetic KPI holdouts, teacher similarity as the
promotion metric, or customer documents in remote teacher calls. It is
qualification-gated controlled-lane SFT with deterministic verification and
external capability selection.

### Interpreting null and negative results

An EGCT program records null and negative lanes as first-class evidence:

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
2. Write the causal hypothesis and guardrails.
3. Freeze the run and evaluation contract.
4. Materialize anchor, targeted, and random-control lanes.
5. Validate manifests, splits, ordering, and teacher qualification.
6. Train the same recipe on every lane.
7. Evaluate every eligible checkpoint externally.
8. Compare targeted versus anchor and random control.
9. Inspect category, item, and failure deltas.
10. Confirm the selected conclusion across required seeds.
11. Build the promotion receipt or record the terminal negative result.
12. Design the next isolated intervention from the observed evidence.

## Adoption Checklist

- [ ] Canonical capability and metric named.
- [ ] Legacy or ambiguous method name replaced by a mechanism-specific term.
- [ ] Anchor, targeted, and random-control lanes materialized.
- [ ] Run contract frozen and hashed.
- [ ] Row provenance and deterministic order recorded.
- [ ] Teacher qualification disjoint from training and promotion evaluation.
- [ ] Construction-gold rows excluded from the real-world KPI holdout.
- [ ] Every checkpoint evaluated under the same external contract.
- [ ] Malformed outputs fail closed and remain in denominators.
- [ ] Category/family regressions inspected.
- [ ] Seed policy completed.
- [ ] Serving evidence separated from capability evidence.
- [ ] Promotion receipt binds every relevant artifact hash.
- [ ] Negative and null lanes retained.

## Naming Guidance

Use `EGCT` only for an experiment that has a frozen contract, controlled lane or
otherwise justified causal comparison, external behavior metric, guardrails,
and receipt-visible evidence state.

Use narrower mechanism names when appropriate:

- `teacher-assisted distillation`;
- `construction-gold SFT`;
- `verifier-filtered SFT`;
- `targeted replacement lane`;
- `compact router distillation`;
- `external-behavior checkpoint selection`;
- `state-reuse serving optimization`.

Do not rename SRSTC to EGCT. SRSTC is an algorithm. EGCT is the method used to
test and improve it.
