# SAME-R Causal And Evidence Contracts

This document is normative for per-intervention causality, run lineage,
evaluation evidence, contamination, invalidation, and promotion under SAME-R.
The [canonical SAME-R README](README.md) owns the outer algorithm. The
[selector contract](SELECTOR_AND_SATURATION.md) owns automatic, multi-model,
cross-domain, and recursive selection. Machine-readable definitions live in
[`contracts/`](contracts/README.md).

`MUST`, `MUST NOT`, `SHOULD`, and `MAY` have their usual normative meanings.

## Artifact Chain

One trial produces or references these immutable objects:

1. approach-registry revision;
2. participant registrations;
3. scoped label-authority receipts;
4. per-intervention causal contract;
5. lane manifests and ordered row-ID artifacts;
6. run contract for each lane and seed;
7. attempt receipts, logs, checkpoints, and parameter manifests;
8. contamination audit;
9. checkpoint evaluation receipts and typed metric evidence;
10. trial receipt and disposition;
11. selection receipt;
12. saturation decision; and
13. promotion, terminal-negative, blocked, or invalidation receipt.

Objects MAY live in different repositories. Every cross-repository pointer
MUST bind repository, revision, repository-relative path, and SHA-256. A mutable
branch name is discovery metadata, not evidence identity.

## Per-Intervention Causal Contract

Each intervention MUST have one causal contract before any result-bearing call.
The contract answers: what capability, for which population, changed by what
single intervention, compared through which matched operation, judged by which
metric and guardrails, under what budget, and interpreted how on failure.

### Identity and ownership

Required identity fields:

- `experimentId` and `interventionId`;
- domain owner, method owner, evaluator owner, artifact owner, and human
  authority;
- approach-registry revision and `approachId`;
- parent selection receipt when the intervention was selected automatically;
- parent SAME-R contract and recursion path when nested; and
- canonical contract SHA-256.

The contract hash is computed from canonical JSON with the hash field omitted.
Changing any required field creates a new contract; it never edits the meaning
of an existing receipt.

### Capability and population

The contract MUST record:

- named capability and externally observable behavior;
- target population definition;
- inclusion and exclusion rules;
- unit of analysis and grouping unit;
- languages, categories, families, repositories, matters, pages, blocks, or
  other declared strata;
- source and split manifest pointers and hashes;
- expected item denominator by split and stratum;
- legal, policy, and data-access constraints; and
- populations explicitly outside the claim.

Population descriptions such as `public tasks`, `translation data`, or `legal
documents` are insufficient without a manifest or deterministic construction
rule.

### Baseline and artifact lineage

The baseline MUST identify:

- provider and model ID;
- immutable model revision;
- exact base checkpoint ID and SHA-256;
- tokenizer ID, revision, configuration, chat template, and hashes;
- model configuration and parameter-manifest hashes;
- conversion, quantization, or packaging identity when execution depends on
  it; and
- previously accepted adapter, router, rule, table, or serving configuration
  when one is part of the baseline.

A model family name or local directory is not an artifact identity.

### Intervention and causal hypothesis

The intervention MUST name one independent variable and state:

- exact proposed change;
- causal mechanism expected to move the capability;
- expected direction and minimum meaningful effect;
- primary external metric;
- blocking guardrails;
- plausible confounders controlled by the matched lanes; and
- failure interpretations for anchor equivalence, random-control equivalence,
  guardrail failure, seed instability, contamination, and budget exhaustion.

If model, data, prompt, optimizer, schedule, evaluator, and serving behavior all
change, those are separate axes unless the declared intervention is the full
bundle and the claim is restricted to that bundle.

## Matched Operation Contract

The causal contract MUST describe the operation applied to anchor, targeted,
and random-control lanes.

### Data operations

For keep, add, remove, replace, reorder, filter, weight, or relabel operations,
record:

- operation kind;
- input and output row counts;
- exact row IDs affected;
- exact positions, or position-policy ID and SHA-256;
- replacement, removal, or insertion count;
- candidate-pool ID and hash;
- selection policy, seed, and policy hash;
- duplicate-removal policy and order;
- final ordered row-ID artifact and hash;
- shard boundaries;
- consumed-row count, consumed-prefix hash, and resume cursor; and
- any row weights or sampling probabilities.

If targeted replaces 16 rows, random control MUST replace 16 rows at matched
positions from a declared random pool. If positions differ, position is an
additional independent variable.

### Prompt and generation operations

For teacher, proposer, critic, model judge, or synthetic-generation calls,
record:

- participant registration and allowed role;
- model/provider ID and revision;
- system instruction, prompt template, few-shot set, tool list, response
  schema, and hashes;
- decoding, temperature, top-p, top-k, token ceiling, stop rules, seed, retry,
  timeout, and failure policy;
- maximum calls, actual calls, tokens, invalid outputs, retries, and accepted
  outputs;
- per-call input/output receipt pointers and hashes;
- label-authority receipt authorizing each accepted label operation; and
- whether a call can access qualification, training, public-diagnostic,
  checkpoint-selection, or sealed-promotion data.

Prompt mutation itself is an intervention. A prompt cannot change silently
inside a data-selection or optimizer comparison.

### Model, optimizer, and serving operations

For model or adapter interventions, record exact architecture, parameter,
initialization, optimizer, schedule, precision, device, and execution-plan
identities. For serving interventions, record model/output identity, prefix or
KV state hash, reset point, cache ownership, invalidation policy, and parity
contract.

## Run Contract And Exact Lineage

Every lane and seed emits a run contract before execution.

### Model and adapter identity

Required model lineage:

- model ID and immutable revision;
- base-checkpoint ID and SHA-256;
- tokenizer revision and SHA-256;
- model configuration and parameter-manifest SHA-256;
- adapter type, target modules, rank, alpha, dropout, and bias policy;
- adapter initialization method and seed;
- initial adapter-parameter SHA-256;
- ordered trainable-parameter names, shapes, dtypes, and manifest SHA-256;
- frozen-parameter manifest SHA-256 when feasible; and
- final checkpoint and adapter parameter hashes.

Two lanes that start from different random adapter tensors are not a matched
data comparison unless initialization is the declared axis.

### Runtime and training identity

Required execution fields:

- code repository revision and dirty-state policy;
- command, configuration, environment-lock, dependency, and container/runtime
  hashes;
- accelerator identity, runtime mode, precision, and deterministic settings;
- optimizer type and complete hyperparameters;
- learning-rate and scheduler state;
- batching, accumulation, clipping, update, example, and stopping budgets;
- stage and resume identities;
- checkpoint save cadence and selection rule; and
- process, log, metrics, and terminal-status receipt pointers.

Environment visibility is not execution proof. The run receipt MUST show that
the intended accelerator executed work and that metrics advanced.

### Ordered rows and consumption

The run contract records:

- dataset manifest and SHA-256;
- ordered row IDs as an artifact, not only a seed;
- order algorithm and seed;
- row-order SHA-256;
- total declared rows;
- total consumed rows;
- consumed-prefix SHA-256;
- epoch, shard, and batch boundaries;
- duplicate and invalid-row dispositions; and
- resume cursor and prior-state hash.

Two lanes with different manifests but the same consumed prefix did not expose
their declared difference. Such a comparison is invalid.

## Retry And Attempt Contract

Every invocation has an attempt receipt. The retry policy is frozen before the
first attempt and declares:

- maximum attempts;
- retryable infrastructure failure codes;
- whether retries preserve seed and inputs;
- backoff policy ID;
- which failures debit proposal, generation, training, and evaluation budgets;
- which failures remain in item, checkpoint, and run denominators; and
- authority allowed to classify an infrastructure failure.

All attempts remain visible. A retry MUST NOT erase:

- malformed or contract-invalid model output;
- verifier, compiler, roundtrip, numerical, or task failure;
- timeout when timeout is part of the frozen capability contract;
- policy or safety failure;
- non-finite metric output; or
- unfavorable but valid evaluation.

A recovered infrastructure failure MAY be excluded from the capability
denominator only when the predeclared policy permits it and the receipt retains
both attempts and the exclusion reason.

## Scoped Label Authority

Teacher quality is not global. Each label-authority receipt binds:

- authority ID and human owner;
- teacher, curator, or adjudicator identity and immutable revision;
- qualification corpus, gold, instruction, wrapper, decode, retry, evaluator,
  and threshold hashes;
- domain, capability, population, language, category, task shape, input shape,
  and output envelope;
- allowed actions: positive label, negative label, abstention, correction,
  ranking, scoring, construction, or adjudication;
- denied and unqualified cells with failure metrics;
- valid-from event, superseded receipt, and invalidation triggers; and
- every downstream row and manifest that consumed the authority.

Authority is denied when a required field is missing. It does not transfer:

- between Claude, Codex, Gemini, humans, or local models;
- between revisions of the same model;
- between categories, languages, populations, or task shapes;
- from proposal or critique authority to labeling authority; or
- from majority agreement to ground truth.

Multi-model outputs MAY be machine- or human-adjudicated. The adjudication
receipt preserves each original output, disagreement, abstention, rubric,
adjudicator identity, and final disposition.

## Comprehensive Contamination Audit

The audit MUST enumerate these populations separately:

- teacher qualification;
- participant prompt and instruction development;
- candidate and row construction;
- student training;
- public diagnostics;
- checkpoint selection;
- sealed promotion evaluation; and
- selector meta-training and selector meta-evaluation.

### Required overlap checks

For every relevant population pair, run or explicitly mark not applicable:

- exact byte and canonical-content hashes;
- normalized text or structure hashes;
- loose duplicate and near-duplicate checks;
- template, generator, prompt, and few-shot overlap;
- source document, repository, family, matter, page, block, author, and time
  grouping where applicable;
- semantic or paraphrase screening with frozen scorer identity;
- reference answer, label, span, fault, or expected-output overlap;
- retrieval-index, cache, memory, and generated-label provenance;
- prior prediction outputs reused as labels or prompts; and
- checkpoint-selection access to sealed items.

Each check records checker ID/version/hash, threshold, compared population
hashes, denominator, overlap count, item IDs, status, and disposition.

### Access audit

For each participant and artifact, record whether it had direct, indirect,
tool-mediated, cached, or unknown access. Unknown access is blocking. The audit
includes humans, Claude, Codex, Gemini, teachers, critics, selectors, local
models, evaluators, scripts, retrieval systems, and logging systems.

### Audit result

The overall result is:

- `pass`: every required check ran and no blocking overlap exists;
- `fail`: blocking overlap exists and affected evidence is invalid; or
- `blocked`: required inputs, access history, hashes, or checks are missing.

An approved domain exception MUST name the authority, affected items, rationale,
and narrower claim. It does not convert overlap into absence.

## Checkpoint And Denominator Completeness

The checkpoint policy freezes expected checkpoint IDs or a deterministic
cadence. The evaluation receipt reports:

- expected checkpoints;
- materialized checkpoints;
- attempted evaluations;
- successful evaluations;
- failed evaluations and all attempts;
- omitted checkpoints and reason codes;
- expected, observed, missing, malformed, and excluded items per checkpoint;
- original and per-stratum item denominators; and
- selection eligibility for every checkpoint.

The final checkpoint has no privilege. A failed or omitted checkpoint remains
in the denominator and scoreboard. A selected checkpoint MUST be the winner
under the predeclared lexicographic rule after all blocking gates.

## Typed Metric Evidence And Adjudication

Metric evidence has independent measurement and adjudication axes.

### Measurement types

- `deterministic_measurement`: exact executable, compiler, roundtrip, coder,
  schema, hash, or numerical oracle;
- `reference_scored`: versioned score against declared references;
- `learned_metric`: frozen learned scorer with calibration evidence;
- `ai_judged`: frozen model judge with prompt, tools, decoding, retry, and
  failure behavior; and
- `human_judged`: identified reviewers applying a versioned rubric.

### Adjudication types

- `none`;
- `machine_adjudicated`;
- `human_adjudicated`; and
- `human_and_machine_adjudicated`.

### Required metric fields

Every primary, guardrail, supporting, and diagnostic metric records:

- metric ID, definition, unit, direction, threshold, and decision role;
- measurement and adjudication types;
- scorer/adjudicator ID, revision, policy hash, prompt hash, and calibration
  pointer;
- population and item IDs or manifest hash;
- expected, scored, missing, malformed, excluded, and disputed denominators;
- value, uncertainty, paired deltas, and category/family strata;
- item-level evidence pointer and SHA-256;
- abstentions, disagreements, overrides, and original pre-adjudication result;
  and
- receipt hash.

A scalar aggregation MUST NOT compensate for a blocking failure. Learned or AI
judgments remain learned evidence even after consensus. Human adjudication does
not erase machine evidence or dissent.

## Failure Interpretation

The causal contract precommits conclusions for:

- targeted equals anchor;
- targeted equals matched random control;
- training fit without external transfer;
- category, safety, policy, or contract regression;
- malformed-output increase;
- seed confirmation failure;
- public diagnostic improvement without sealed improvement;
- earlier checkpoint beating later checkpoints;
- serving parity failure;
- payload or integration cost consuming the measured gain;
- contamination failure;
- evaluator or adjudication disagreement; and
- budget exhaustion without a winner.

Observed failure selects one of those conclusions. It does not trigger a new
metric, threshold, retry policy, or holdout look inside the same contract.

## Contract Invalidation

An invalidation receipt is required when a frozen field changes or new evidence
shows the old contract was false.

### Invalidation triggers

- capability, population, grouping, split, order, or denominator change;
- model, tokenizer, checkpoint, adapter initialization, parameter, or package
  identity change;
- data, count, position, prompt, call, label-authority, teacher, or candidate
  pool change;
- optimizer, schedule, precision, runtime, seed, retry, checkpoint, resume, or
  stopping change;
- evaluator, metric, reference, rubric, judge, decode, guardrail, threshold, or
  promotion change;
- search method, family, budget, adaptivity, multiplicity, recursion, selector,
  or saturation change;
- discovered contamination, leakage, access, duplicate, or provenance defect;
  or
- missing, malformed, or contradictory receipt lineage.

### Invalidation receipt

Record old contract hash, trigger code, discovering participant, discovery
event, affected trials and claims, budget disposition, replacement contract
hash, and whether artifacts remain usable for a narrower claim.

Invalidated runs remain in accepted/rejected/blocked history with
`invalidated=true`. They cannot count toward selection, seed confirmation,
saturation, or promotion. Re-running under a corrected contract creates new
trial IDs.

## Promotion Completeness

Promotion requires:

- valid causal and run contracts;
- exact model, checkpoint, adapter, data, and code lineage;
- passed contamination audit;
- complete label authority;
- matched anchor and control evidence;
- complete checkpoint and item denominators;
- primary and guardrail metric receipts;
- required seed confirmation;
- selection and saturation receipts when automatic selection was used;
- deployment/package constraints and runtime parity where applicable; and
- named human or policy review status.

Missing evidence is represented as missing and blocks promotion. It is never
inferred from a README, aggregate score, provider reputation, or consensus.
