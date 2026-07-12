# Hybrid Distillation Guide

Hybrid distillation is one method family inside the broader
[verifier-guided learning](./VERIFIER_GUIDED_LEARNING.md) program. Use that
guide for automatic prompt optimization, GEPA naming, preference optimization,
minimum-risk training, RLVR, domain reward contracts, and the cross-repository
experiment register. This page remains canonical for controlled data lanes,
SFT, knowledge distillation, routing, and checkpoint selection.

Hybrid distillation is an evidence-driven way to make a smaller student model
better on a named capability without blindly adding more data, more steps, or
more teacher output. The core loop is:

1. Define one external target metric that matters.
2. Build several small, controlled data lanes around a known-good baseline.
3. Train the same student recipe on each lane.
4. Sweep checkpoints and pick by the external metric, not training loss.
5. Use the winning and losing lanes to design the next data hybrid.

This is the technique behind the TranslateGemma-4B to Gemma-3-1B EN/ES work,
where the strongest student came from a small partial-replacement lane around a
known-good pack, while adjacent prune, full-replacement, dense-schedule,
polish, random, and seed lanes were used to confirm what did and did not move
external BLEU.

## What Makes It Hybrid

The hybrid part is not just mixing datasets. It is mixing evidence sources:

- Teacher outputs: strong examples, corrections, rationales, or traces.
- Human or curated gold rows: high-trust anchors.
- Candidate row edits: pruned, replaced, repaired, or generated rows.
- Random controls: prove the edit mechanism matters, not only row count.
- External evals: held-out tasks that define the actual win.
- In-domain evals: detect whether the student forgot the local workflow.
- Dense checkpoint sweeps: find the capability peak before overfitting.

A hybrid lane is useful only when it has a clean contract and a comparable
scoreboard. If the evidence cannot be reproduced, it is not a candidate; it is
a note.

## The Contract

Every run should emit a contract before training:

```text
[run-contract] run_name=<name> teacher=<teacher_id> student=<student_id> data=<dataset_or_manifest> resume_from=<path|none> task=<capability> evals=<comma-separated evals> decode=<greedy|sampled|pass@k> schedule=<schedule_id> seed=<seed> dtype=<dtype> device=<device> sweep_mode=<live|after_train>
```

For coding distillation, include these fields when they matter:

```text
language=<python|js|ts|rust|mixed>
repo_scope=<single-file|multi-file|tool-use|patch>
execution_gate=<syntax|unit-tests|hidden-tests|sandbox-run>
prompt_format=<chat|fill-in-middle|diff|tool-call>
teacher_trace=<none|rationale|tests|patch-plan|tool-log>
```

The contract prevents accidental drift. A result should never depend on hidden
defaults, an unstated data file, or a different evaluator.

## Data Lanes

Start from one trusted baseline dataset, then create narrow variants:

| Lane | Purpose |
| --- | --- |
| Anchor | Known-good gold or prior best data. |
| Prune | Remove suspected bad, duplicated, leaky, or overfitting rows. |
| Replace | Replace removed rows with stronger candidates from a candidate pool. |
| Random prune | Control for row count and regularization effects. |
| Random replace | Control for replacement mechanics. |
| Dense checkpoint | Same data, more checkpoint granularity. |
| Seed rerun | Measure variance only after a lane is already strong. |
| Polish | Continue from a winning checkpoint with a smaller learning rate or targeted data. |
| Blend | Merge two complementary capability lanes when both have external evidence. |

Do not launch wide combinatorial sweeps until the small lanes show a real
signal. The most useful run is usually the one that isolates one variable.

## Row Selection

For row-level hybridization, keep a row manifest with:

- stable row id
- source dataset
- teacher or curator provenance
- capability bucket
- static quality score
- exact and loose duplicate keys
- length and formatting features
- reason for keep, prune, replace, or review

Useful row scores are additive and inspectable. Example components:

- Alignment: source and target solve the same task.
- Executability: code compiles, tests run, patch applies.
- Diversity: avoids duplicates and templated rows.
- External similarity: resembles the target benchmark distribution.
- In-domain coverage: preserves the product or repo workflow.
- Difficulty: not too trivial, not impossible for the student.
- Failure value: covers a known student failure mode.

Static scores choose candidates. Training receipts decide truth. In the
translation lane, static QA made full `replace10` plausible and `prune10`
became the first strong artifact-backed leader. The winning move was narrower:
`replace05`, which removed only the highest-risk half of the `pack06/prune10`
removal set and filled those slots from the top replacement pool. That is the
right lesson: static scoring is a proposal generator, not the promotion gate,
and the strongest lane may be a smaller hybrid between two good ideas.

## TranslateGemma Replace05 Case Study

The EN/ES student improvement came from treating the previous leader as a
diagnostic, not as an endpoint.

Starting evidence:

- Previous leader: `pack06/prune10`, 1568 rows, external BLEU `32.9055`.
- Full replacement candidate: `pack06/replace10`, 1600 rows, static QA looked
  strong but training topped out below the leader.
- Seed-only rerun: weaker, so variance alone was not the answer.
- Low-LR polish on the old leader: weaker, so the checkpoint needed better data
  rather than more training on the same rows.

The next lane was built by reconstructing the frozen best-five mix from packs
`01,02,03,04,06`, then using the `pack06/prune10` audit ranking:

- Keep the same base packs and row order.
- Remove only the top 8 highest-risk audit rows per direction from pack 06.
- For `prune05`, leave those 16 rows out, producing 1584 balanced rows.
- For `replace05`, fill those 16 slots with the top 8 replacement candidates
  per direction from the existing `replace10` candidate pool, producing 1600
  balanced rows.
- Score the new datasets against `prune10` and `replace10` before training.
- Train the same 4k Stage A recipe with deferred student-only checkpoint
  sweeps.

Result:

| lane | best checkpoint | external BLEU | external chrF | interpretation |
| --- | --- | ---: | ---: | --- |
| `prune10` previous leader | `003000` | 32.9055 | 59.4631 | strong baseline |
| `prune05` | `003500` | 32.8755 | 58.9218 | near miss; smaller prune alone was not enough |
| `replace05` | `004000` | 33.7353 | 59.6065 | new leader |
| `replace05` 6k | `003000` | 33.2481 | 59.4567 | longer schedule weakened external |
| `replace05` low-LR polish | `000250` | 33.6283 | 59.6061 | close, but did not beat the 4k checkpoint |

The reusable pattern is:

1. Use the previous winner to identify a small suspect set.
2. Split a coarse edit into a smaller edit.
3. Test the smaller prune and the smaller replacement separately.
4. Keep schedule and evaluator fixed while testing data edits.
5. Promote only after the normalized leaderboard and status docs agree.

## Checkpoint Selection

Always sweep checkpoints. Do not assume the final checkpoint is best.

For each checkpoint, score at least:

- external target eval
- in-domain eval
- task-specific correctness artifacts
- representative prediction samples
- run metadata and model path

Pick the model by the external target first. Then check that in-domain quality
does not collapse. If the final checkpoint is worse than an earlier checkpoint,
promote the earlier checkpoint and treat later training as overfit evidence.

## Evidence Gates

A lane can be promoted only when these are true:

1. The training dataset is materialized and has a source manifest.
2. The run contract identifies teacher, student, seed, schedule, dtype, device,
   and eval set paths.
3. The eval has a machine-readable summary and raw predictions or task outputs.
4. The scoreboard compares all relevant checkpoints under the same evaluator.
5. The external metric improves against the current student target.
6. The in-domain metric stays within the accepted band for the use case.
7. The result appears in the normalized run index or results bundle.

If a lane only improves loss, it is not a win. If it only improves in-domain
quality while external quality collapses, it is a specialization lane.

## Applying This To Qwen Coding

The same method maps cleanly to Qwen coding students.

Example roles:

- Teacher: larger Qwen Coder model, stronger proprietary model, or a verified
  multi-agent patch generator.
- Student: smaller Qwen Coder model, local model, adapter, or compressed model.
- Target capability: pass repo tests, fix bugs, implement functions, follow
  project style, write browser-safe code, or use tools correctly.

Build capability buckets instead of one generic code dataset:

| Bucket | Examples | Eval gate |
| --- | --- | --- |
| Function synthesis | HumanEval-style functions, library utilities | unit tests, hidden tests |
| Repo patching | bug fixes, feature requests, API migrations | patch applies, tests pass |
| Tool use | search, inspect, edit, run tests | action trace validity |
| Style adherence | project rules, lint conventions, review fixes | lints, style tests, reviewer rubric |
| Debugging | failing test to minimal fix | before/after test delta |
| Frontend | UI task, screenshot target, interaction states | Playwright, visual assertions |
| Systems | concurrency, memory, perf-sensitive code | stress tests, benchmarks |

Then create lanes:

| Lane | Coding Example |
| --- | --- |
| Anchor | verified accepted patches with passing tests |
| Prune | remove flaky tests, leaky benchmark tasks, trivial duplicates |
| Replace | add hard failures from real repos, with verified patches |
| Random control | remove or add the same count without quality ranking |
| Dense checkpoint | score every saved adapter/checkpoint on code evals |
| Polish | continue from best checkpoint on failure-mode data only |
| Blend | combine repo-patching rows with style-adherence rows after both win separately |

For coding, the external metric should be execution based whenever possible:

- pass rate
- pass@1 or pass@k
- patch apply rate
- compile rate
- unit test delta
- hidden test pass rate
- tool trace validity
- no-regression count

Text similarity is a supporting metric, not the gate for code.

## Qwen Coding Run Contract

Use a concrete contract like:

```text
[run-contract] run_name=qwen-coder-1p5b_patch_prune08_dense500_v1 teacher=qwen-coder-14b student=qwen-coder-1p5b data=training_data/qwen_patch_prune08.jsonl task=repo_patch evals=evals/mbpp.jsonl,evals/repo_patch_smoke.jsonl,evals/style_holdout.jsonl decode=greedy execution_gate=unit-tests prompt_format=diff seed=42 dtype=bfloat16 device=cuda sweep_mode=after_train
```

The scoreboard should include:

| checkpoint | external pass@1 | patch apply | compile | in-domain pass | style pass | notes |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| checkpoint-001000 |  |  |  |  |  |  |
| checkpoint-001500 |  |  |  |  |  |  |
| checkpoint-002000 |  |  |  |  |  |  |

Promotion should be based on the external capability target, not the checkpoint
with the lowest training loss.

### WGSL V10/V11 application

The Doppler WGSL program applies this design with three equal 1,200-row
lanes: a Doppler-only anchor, a 20% pinned external-kernel replacement, and a
20% random in-domain replacement. The primary student is Qwen 3.5 9B; Qwen 3.5
2B is an efficiency control and Qwen 3.6 27B is a teacher/ceiling. Compiler
repair is the prepared training substrate. Family-disjoint and sealed semantic
repair pass@1, not completion loss or the mechanics fixture, controls
promotion.

The optimizer comparisons start from the same selected SFT checkpoint:
best-of-eight rejection sampling, DPO pairs derived from the frozen groups, and
GRPO RLVR using the same tasks, sampler, token budget, and verifier bundle.
This keeps the data-lane question separate from the optimizer question.

The seed-11 anchor SFT result raised family-disjoint compiler-repair pass@1
from 8.36% to 88.29% on 299 tasks. V11 keeps optimizer construction on the
separate diagnostic partition so the public comparison cannot leak into DPO or
GRPO training. This result does not promote the adapter: only one seed and one
data lane are complete, and compilation is not a semantic ML-kernel oracle.

V12 corrects the pending data ablation before execution. The earlier 800-step
dataset order exposed the same prefix in all three lanes, so it could not test
external replacement. The registered V12 workloads seed/hash-order and consume
all 1,200 rows in each lane. They also separate 64-token short repairs from a
640-token long stratum using only the visible broken-span length, then recombine
the original denominator.

The contrast with the rejected predecessor is methodologically useful.
TranslateGemma Stage A used a capable 1B initialization, 1,600 curated pairs,
4,000 full-weight steps, checkpoint selection, and adjacent data controls. The
old WGSL V8 lane used Gemma 3 270M, four unique repairs duplicated to eight
rows, one optimizer step, rank-4 LoRA on two projections, and prose-shaped
targets. V10 uses Qwen 3.5 9B, hundreds of compiler-verified replacement rows,
100 optimizer updates, rank-32 LoRA across attention and MLP projections, and
the same replacement-only contract at training and evaluation. Model capacity,
data coverage, update budget, and response contract all changed together
between V8 and V10, so V10 explains why the tiny fixture was not a useful
capability experiment; it does not isolate which one of those four changes is
causal.

## Designing The Next Lane

Use this decision table after every sweep:

| Observation | Next move |
| --- | --- |
| External rises then falls | Add denser checkpoints around the peak. |
| External improves but in-domain drops | Blend a small in-domain anchor set into the winning lane. |
| In-domain improves but external drops | Stop that axis or relabel as specialization. |
| Prune beats replace | Build smaller partial-replacement lanes around the pruned set. |
| Replace beats prune | Inspect added rows and build targeted replacement pools. |
| Random control matches curated lane | Your scoring heuristic is not explaining the gain. |
| Seed rerun misses | Do not seed-roulette; change data or schedule. |
| Polish worsens | The winning checkpoint is already at or past the useful peak. |

The next lane should be a hypothesis, not a hope. Example:

```text
Hypothesis: external code pass rate improves because hard bug-fix rows teach
repository-local constraints, but too many style rows reduce algorithmic pass@1.
Diagnostic: compare anchor, prune08, replace08, and random08 on the same
checkpoint sweep and inspect failed tasks by bucket.
```

## Artifact Layout

For every lane, keep:

```text
runs/<run_name>/
  run_contract.txt
  inputs/
    train_pairs.normalized.jsonl
    train_pairs.normalized.jsonl.sources.json
  stage_a/
    metrics.jsonl
    checkpoint-*/
  checkpoint_sweep/
    manifest.jsonl
    scoreboard.md
    scoreboard_eval_rows.csv
    scoreboard_checkpoints.csv
    <eval>__<checkpoint>/
      compare_eval_summary.json
      predictions.jsonl
      failures.jsonl
  logs/
    train.log
    sweep.log
    report_refresh.log
```

For coding, add:

```text
patches/
  generated.diff
  apply.log
  test.log
  lint.log
  trace.json
```

## Anti-Patterns

- Training more steps because the loss still falls.
- Promoting a checkpoint without an external eval.
- Mixing several data edits in one run before isolated lanes establish signal.
- Treating static dataset score as final evidence.
- Hiding evaluator settings in scripts.
- Comparing sampled decoding against greedy decoding without labeling it.
- Reporting wins from a run that is not in the results bundle.
- Keeping only aggregate metrics and discarding predictions or failure cases.
- Re-running seeds before testing a better data hypothesis.
- Using teacher similarity as the only metric for code.

## Minimal Operating Loop

1. Pick the target: one external metric and one in-domain guardrail.
2. Freeze the baseline: teacher, student, schedule, seed, dtype, and evaluator.
3. Build three lanes: anchor, curated edit, random control.
4. Train each lane with the same contract.
5. Sweep checkpoints.
6. Promote only claim-grade rows into the leaderboard.
7. Inspect the best and worst failure cases.
8. Design one new hybrid lane from that evidence.
9. Repeat until the axis plateaus.

The method works because it separates three questions that are often confused:

- Did the student learn the training rows?
- Did the checkpoint improve the real capability?
- Do we know which data edit caused the improvement?

Hybrid distillation is the discipline of answering all three before declaring a
model better.
