# Verifier-Guided Learning

Verifier-guided learning is the cross-domain research frame for improving a
model with machine-generated experience while keeping every promotion claim
attached to executable or adjudicated evidence. It includes prompt search,
data curation, supervised fine-tuning, preference optimization, minimum-risk
training, reinforcement learning with verifiable rewards (RLVR), and
on-policy distillation. These methods are related, but they are not
interchangeable.

The repository ownership split is:

- Gamma owns the method taxonomy, experiment design, and cross-repository
  experiment register.
- Doppler owns browser/WebGPU training execution, verifier receipts, adapter
  deltas, and promotion gates.
- Valera/Columbo owns legal-document labels, adjudication, product policy, and
  the boundary between machine scores and human authority.

The checked-in register is
[`projects/distillation/shared/experiments/experiment-register.jsonl`](../projects/distillation/shared/experiments/experiment-register.jsonl).
It stores pointers and claim boundaries, not copied result bundles.

## Industry Names

There is no single standard name for the entire prompt-search, simulation,
curation, and training loop. Use the name that identifies the mechanism:

| Mechanism | Preferred name |
| --- | --- |
| Search over instructions written in language | automatic prompt optimization |
| Iterative reflective prompt evolution with instance-level Pareto selection | GEPA |
| Generate tasks and responses, execute them, retain passing rows, then tune | execution-grounded synthetic data or verifier-filtered self-training |
| Train on completions produced under two different prompts | prompt-conditioned sequence-level distillation |
| Optimize a policy with programmatic pass/fail or numeric rewards | reinforcement learning with verifiable rewards (RLVR) |
| The complete repeated loop | verifier-guided self-improvement or an execution-grounded data flywheel |

“Hybrid distillation” remains Gamma's name for the data-centric combination of
teacher outputs, curated anchors, controlled data lanes, checkpoint selection,
logit distillation, and routing. RLVR is a neighboring method, not a synonym
for hybrid distillation.

## Scientific Chain

The central causal hypothesis is:

> A machine-selected prompt changes a frozen teacher's outputs, and those
> changed outputs produce a better student under a fixed training recipe.

That statement contains separate tests:

1. Automatic prompt optimization changes a policy written in language.
2. A frozen teacher produces different outputs under that policy.
3. Data selection or training transfers the difference into student weights.
4. A sealed domain evaluation shows that the student capability improved.
5. Experiment infrastructure preserves lineage and blocks unsupported
   promotion claims.

A result at one step does not establish the full chain. A better prompt does
not prove a better student. Nonzero gradients do not prove a better task
policy. Lower completion loss does not prove a held-out capability gain.

For reference protocol `j` and training seed `s`, record two paired effects:

```text
teacher_effect[j] = score(teacher_optimized, labels[j])
                  - score(teacher_expert, labels[j])

student_effect[j, s] = score(student_optimized[s], labels[j])
                     - score(student_expert[s], labels[j])
```

Interpret them separately:

- Positive teacher and student effects support transfer into the weights.
- A positive teacher effect with equivalent students means training erased the
  prompt advantage.
- A near-zero teacher effect means there is no generalizing prompt advantage
  to transfer.
- Different signs across reference protocols leave the conclusion
  protocol-dependent.

## Evidence States

Every registered experiment uses one of these states:

| State | Meaning |
| --- | --- |
| `proposed` | The hypothesis and contracts are written; execution evidence is absent. |
| `harness_ready` | Dataset, evaluator, and receipt paths execute; no learning claim is made. |
| `mechanics_proven` | Expected steps, nonzero gradients, parameter changes, and declared loss checks pass. |
| `capability_proven` | A frozen held-out task metric improves under the declared comparison. |
| `promoted` | Capability evidence and every product/release gate pass. |
| `rejected` | The declared lane ran and missed its gate. |
| `blocked` | A named prerequisite or policy gate prevents promotion. |

Promotion must move through these states. It must never infer
`capability_proven` from `mechanics_proven`.

## Method Taxonomy

| Method | Training signal | Best fit | Required control |
| --- | --- | --- | --- |
| Data-centric SFT | selected target tokens | trusted demonstrations and narrow data edits | unchanged recipe plus random prune/replace controls |
| Rejection sampling | verifier retains passing samples | code, WGSL, schemas, exact constraints | acceptance-rate and diversity receipts |
| DPO | chosen/rejected response pairs | adjudicated or reliably ranked alternatives | frozen pair construction and reference policy |
| Minimum-risk training | expected task loss over sampled candidates | translation and other reference-scored sequence tasks | fixed candidate sampler and metric |
| GRPO-style RLVR | group-relative advantages from verifiers | executable outputs with dense enough reward | hidden verifier split and SFT/rejection baselines |
| Process supervision | scores intermediate steps or tool actions | debugging and multi-stage workflows | outcome-only comparison and trace integrity |
| Rule-based AI feedback | model critique constrained by explicit rules | policy shaping where exact outcome reward is incomplete | rule versioning and human audit |
| Active learning | disagreement or uncertainty selects labels | expensive legal or domain adjudication | random-acquisition baseline |
| Adversarial self-play | generator creates counterexamples for a solver | verifier gaps and boundary failures | frozen regression suite and novelty checks |
| On-policy distillation | promoted teacher labels current policy rollouts | capability transfer after the student distribution moves | teacher-version and validation-high receipts |

Candidate methods should isolate one new mechanism against the current best
lane. Combining prompt mutation, new data, a new optimizer, and a new reward in
one comparison makes the cause uninterpretable.

## GEPA Naming Contract

GEPA means Genetic-Pareto prompt optimization. An artifact may use `gepa` as a
method identifier only when the run records:

1. candidate execution trajectories and evaluator feedback;
2. reflection-driven mutations across iterations;
3. instance-level Pareto selection that preserves complementary candidates;
4. candidate acceptance and frontier updates; and
5. any system-aware merge operation used by the run.

A single reflection call that proposes several prompts is
`reflective_prompt_mutation`. Repeating independent one-call searches remains
controlled reflective mutation unless it implements the iterative Pareto
algorithm. A data importer may preserve a GEPA frontier, but importing one does
not mean the importing repository ran GEPA.

## Reward Contract

Represent reward as a vector before reducing it to an optimizer scalar:

```text
reward = {
  contract_pass,
  execution_pass,
  task_score,
  safety_pass,
  policy_pass,
  novelty_score,
  judge_score,
  human_status
}
```

Each component declares one evidence type:

- `deterministic`: programmatic validation, exact comparison, compilation,
  tests, schema checks, or hash checks;
- `learned_metric`: a versioned model-based metric such as a translation
  quality estimator;
- `ai_judge`: a versioned model prompt and decoding contract;
- `human_adjudicated`: a recorded reviewer decision under a declared rubric.

Use lexicographic gates. Contract, safety, and policy failures block a sample
before any scalar score can compensate for them. Keep the raw reward vector,
verifier versions, stdout/stderr or browser traces, and reduction formula in
the receipt.

Protect against reward hacking:

- keep promotion verifiers hidden from generation and training;
- separate public diagnostics from sealed evaluation;
- version every rule, judge prompt, model, and toolchain;
- include counterexamples that pass superficial format checks;
- inspect score disagreement and high-reward failures;
- forbid the same model/provider family from being the only generator,
  selector, and evaluator when cross-family checks are available;
- retain losing lanes and invalidated receipts.

## Domain Programs

### WGSL and code

The strongest reward components are executable:

- structured output and allowed-diff validation;
- WGSL parse or shader-module creation;
- pipeline creation and dispatch without validation errors;
- output comparison against a CPU oracle;
- finite values, bounds, alignment, and buffer-layout invariants;
- property and metamorphic tests over shapes and workgroup sizes;
- hidden repair tasks and policy-violation checks.

The first candidate is verifier-filtered SFT: sample repairs, retain those that
pass the qualification harness, and train on the accepted pairs. Compare it
with rejection sampling at inference and with a GRPO-style RLVR lane only after
the rollout runtime can preserve policy log-probabilities, reward vectors, and
hidden-verifier receipts. SelfCodeAlign is relevant here because it generates
coding tasks and responses, validates them in a sandbox, and selects passing
examples for instruction tuning.

Doppler WGSL V10 now has a primary Qwen 3.5 9B SFT result. Its Radeon verifier
accepted 2,714 compiler-reproducing replacement tasks from 345 kernels, split
by kernel family with no overlap. Gamma trained the seed-11 rank-32 adapter and
Doppler compared 2,392 base samples with 2,392 adapted samples on 299 public
tasks under the same sampler and verifier runtime. Pass@1 rose from 8.36% to
88.29%; the external Zero-TVM subgroup rose from 9.73% to 71.68%. This is
narrow capability evidence for compiler repair, not RLVR or semantic kernel
correctness. V11 derives DPO and clipped GRPO-with-KL updates only from the
separate 285-task diagnostic split and reserves the public split for policy
comparison. Promotion still requires the remaining seeds, data controls, and
sealed dispatch, oracle, numerical, metamorphic, and regression suite.

### Translation

Translation has deterministic constraints and reference-based quality metrics,
but semantic quality is not fully verifiable. Useful signals include:

- required language, script, placeholders, markup, and terminology;
- exact preservation of numbers, entities, and protected tokens;
- BLEU and chrF against frozen references;
- a versioned learned metric as supporting evidence;
- human review for domain meaning and ambiguous references.

Data-centric SFT remains the baseline. Minimum-risk training and
minimum-Bayes-risk selection directly optimize or select against sequence-level
metrics. Preference optimization can use adjudicated translation pairs. RLVR
should optimize deterministic constraints without presenting those constraints
as a complete translation-quality reward.

### Valera/Columbo legal documents

Machine-verifiable components include schema validity, exact source-span
grounding, document/page citations, provenance, deterministic PII checks,
supported-path enforcement, and export regression gates. Legal category,
privilege, responsiveness, risk, and final redaction authority remain
human-adjudicated. The domain contract lives in Columbo's
`docs/legal-feedback-optimization.md`.

Good first comparisons are verifier-filtered SFT, disagreement-directed active
learning, and DPO from adjudicated response pairs. RLVR may optimize structural
and grounding rewards, but it must not learn around a human approval gate or
turn an AI judge into final legal authority.

### Generic finance and legal judgment

For document classification or boundary decisions, freeze paired causal lanes:

| Lane | Data policy | Role |
| --- | --- | --- |
| `E` | expert-prompt teacher outputs | control |
| `O` | optimized-prompt teacher outputs | primary treatment |
| `H` | fixed half `E`, half `O` | mixed-policy diagnostic |
| `C` | curated anchors plus `O` | data-composition candidate |

`E` and `O` must share item IDs, teacher, wrapper, schema, decoding, retries,
student initialization, optimizer, token budget, checkpoint rule, and seeds.
Remove a failed teacher item from both lanes or replace it from a frozen paired
queue. Separate prompt-development, candidate-selection, and sealed evaluation
sets. Keep each reference-label protocol separate, correct paired tests for the
declared family, and report whether the result changes across label families.

## Cross-Repository Experiment Register

The register is pointer-only. Each JSONL row records:

- experiment and domain identifiers;
- owning repository and path;
- method identifiers and evidence state;
- one primary immutable evidence artifact, plus any related artifacts needed
  to support the claim boundary, each with repository revision and SHA-256;
- reward component types and roles;
- an explicit claim boundary; and
- the next gate.

Validate it with:

```bash
python projects/distillation/shared/experiments/validate_experiment_register.py
```

When sibling repositories are present in the same workspace, the validator
checks their artifact hashes. In an isolated Gamma checkout it checks Gamma
artifacts and still validates external pointers structurally.

## Related Work

- [GEPA paper](https://arxiv.org/abs/2507.19457) and
  [reference implementation](https://github.com/gepa-ai/gepa): reflective
  prompt evolution with a Pareto frontier.
- [SelfCodeAlign](https://arxiv.org/abs/2410.24198): execution-filtered task and
  response generation followed by instruction tuning.
- [DeepSeekMath](https://arxiv.org/abs/2402.03300): introduces GRPO for
  reasoning optimization.
- [Direct Preference Optimization](https://arxiv.org/abs/2305.18290): direct
  preference learning without a separately fitted reward model.
- [Minimum Risk Training for Neural Machine Translation](https://aclanthology.org/P16-1159/):
  sequence-level expected-risk optimization.
- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050): process versus
  outcome supervision.
- [Rule Based Rewards for Language Model Safety](https://arxiv.org/abs/2411.01111)
  and [Constitutional AI](https://arxiv.org/abs/2212.08073): explicit rules and
  AI feedback with distinct evidence limits.
- [An Efficient Active Learning Pipeline for Legal Text Classification](https://aclanthology.org/2022.nllp-1.32/):
  acquisition strategies for legal labels.
- [Learning to Replicate Expert Judgment in Financial Tasks](https://thinkingmachines.ai/news/learning-to-replicate-expert-judgment-in-financial-tasks/):
  related private-task evidence for interleaved batching, clipped policy
  optimization, on-policy distillation, and teacher promotion. Its private
  tasks and aggregate metrics are related work, not direct evidence for WGSL,
  translation, or Valera/Columbo.
