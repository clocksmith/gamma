# EN-ES Distillation Experiment Brief

## 1) Purpose
Record the motivation, setup, training mechanics, hypotheses, evaluation plan, and decision logic for this EN<->ES distillation run.

## 2) Anonymized Motivation (A/B)
- A: Concern that model size mostly reflects broad linguistic/world competence, so shrinking may remove important translation quality.
- B: Point that task-adapted distillation and pair-specific variants are expected, and smaller bilingual students should be feasible.
- Joint testable question:
  - Can an EN<->ES student retain strong quality while reducing deployment footprint and runtime cost?

## 3) Hypothesis
- Primary hypothesis:
  - Distilling from a strong teacher into an EN<->ES student will preserve most practical translation quality on held-out EN<->ES data.
- Secondary hypothesis:
  - Quality loss, if present, will appear first on edge cases (idioms, domain shift, long-context nuance), not average short-form examples.

## 4) Training Configuration (Current Run)
- Run root:
  - `projects/distillation/translation/runs/enes_gemma3_270m_pruned/exp_enes_gemma3_270m_live2`
- Schedule:
  - `A_then_B`
- Total steps:
  - `100000`
- Stage split:
  - Stage A (`sft_steps`): `50000`
  - Stage B (`distill_steps`): `50000`
- Train data:
  - `translate_distill_pairs_en_es_2way.train.jsonl`
  - Rows: `922` (`461 en-es`, `461 es-en`)
- Devices:
  - Current resume on CPU (`--device cpu --dtype float32`)
- Resume source:
  - Stage B from checkpoint `checkpoint-000400`

## 5) How Training Works (Conceptual)
### Stage A (SFT warmup)
- Objective:
  - Student learns from gold targets only (`query -> target_pos`).
- Loss:
  - Cross-entropy only (`loss_pos`).
- KD/triplet:
  - Off.
- Purpose:
  - Stabilize translation behavior before harder distillation objectives.

### Stage B (distillation)
- Objective:
  - Continue CE while matching teacher behavior and optional ranking signal.
- Loss:
  - `total_loss = loss_pos + lambda_kd * loss_kd + mu_triplet * loss_triplet`
- KD:
  - Teacher-vs-student distribution matching (KL-based term).
- Triplet:
  - Positive translation should score better than negative by margin.

### Per-step mechanics
- Sample a batch from train rows (with replacement).
- Build prompt/target tensors and labels.
- Student forward pass -> logits.
- Compute active loss terms.
- Backpropagate gradients.
- Optional gradient clipping.
- Optimizer step.
- Scheduler step.
- Zero gradients.
- Periodic metrics logging and checkpoint saves.

## 6) Why 922 Rows Can Still Support 100k Steps
- Steps are optimizer updates, not unique-row consumption.
- Sampling uses replacement, so the same row can be revisited many times.
- Effective epoch-equivalent for full run:
  - `100000 / 922 ~= 108.5`
- Stage-specific epoch-equivalent:
  - `50000 / 922 ~= 54.2` per stage.

## 7) Evaluation Plan (After Training Completes)
### Primary (must-run)
- Dataset:
  - `translate_distill_pairs_en_es_2way.eval.jsonl` (102 rows: 51 en-es + 51 es-en)
- Compare:
  - Final student vs teacher
- Metrics:
  - Exact match (always)
  - BLEU/chrF when available
  - Optional COMET if local model is available

### Secondary (optional stress/generalization)
- Dataset:
  - `translate_distill_pairs.eval.jsonl` (402 rows, multi-source to en/es)
- Purpose:
  - Detect quality drop outside pure EN<->ES focus.

## 8) Evaluation Commands (Template)
Use the final checkpoint once Stage B completes.

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3

RUN_ROOT=projects/distillation/translation/runs/enes_gemma3_270m_pruned/exp_enes_gemma3_270m_live2

$PY projects/distillation/translation/eval/run_translate_distill_eval.py \
  --pairs projects/distillation/translation/training_data/translate_distill_pairs_en_es_2way.eval.jsonl \
  --model "$RUN_ROOT/final" \
  --teacher-model google/translategemma-4b-it \
  --vocab-subset-dir "$RUN_ROOT/vocab_subset" \
  --tokenizer-model google/translategemma-4b-it \
  --source-langs en,es \
  --target-langs en,es \
  --device cpu \
  --dtype float32 \
  --eval-bleu \
  --eval-chrf \
  --out-dir "$RUN_ROOT/eval_enes_102"
```

Optional broader compare:

```bash
$PY projects/distillation/translation/eval/run_translate_distill_eval.py \
  --pairs projects/distillation/translation/training_data/translate_distill_pairs.eval.jsonl \
  --model "$RUN_ROOT/final" \
  --teacher-model google/translategemma-4b-it \
  --vocab-subset-dir "$RUN_ROOT/vocab_subset" \
  --tokenizer-model google/translategemma-4b-it \
  --target-langs en,es \
  --device cpu \
  --dtype float32 \
  --eval-bleu \
  --eval-chrf \
  --out-dir "$RUN_ROOT/eval_multi_to_enes_402"
```

## 9) Results Log (Fill After Completion)
### EN<->ES 102-row compare
- Student model path:
  - `TBD`
- Teacher model path:
  - `TBD`
- Exact match delta (student - teacher):
  - `TBD`
- BLEU delta:
  - `TBD`
- chrF delta:
  - `TBD`
- Runtime (student):
  - `TBD`
- Runtime (teacher):
  - `TBD`

### Optional 402-row compare
- Exact match delta:
  - `TBD`
- BLEU delta:
  - `TBD`
- chrF delta:
  - `TBD`
- Notable failure patterns:
  - `TBD`

## 10) Interpretation Playbook
### If student is close to teacher on EN<->ES
- Implication:
  - Pair-focused distillation is viable for this deployment target.
- Next action:
  - Package student for browser/local runtime tests.

### If student trails moderately
- Implication:
  - Capacity/objective mix may be insufficient for consistency.
- Next action:
  - Increase or rebalance Stage B (KD weight, triplet weight, step budget), then re-evaluate.

### If student trails heavily
- Implication:
  - Current compression or training regime is too aggressive for target quality.
- Next action:
  - Expand student capacity or data coverage, and retune curriculum.

## 11) External Messaging Drafts (Anonymized)
### Outcome A: strong retention
- "In this EN<->ES test, pair-specific distillation preserved most quality while reducing deployment cost. Generalization still needs broader validation."

### Outcome B: mixed retention
- "Distillation captured core bilingual behavior but regressed on harder edge cases. Additional capacity/curriculum tuning appears necessary."

### Outcome C: weak retention
- "For this setup, aggressive narrowing reduced quality more than expected. We likely need a larger student and/or broader training/eval coverage."

## 12) Theoretical Next Steps
- Add checkpoint sweep evaluation (every 2k to 5k Stage B steps) to identify quality plateau and avoid overtraining.
- Build an EN<->ES hard-set (idioms, long sentences, domain shift) for robust regression checks.
- Run latency/memory benchmarks on target deployment environment (browser WebGPU and/or local CPU).
- Compare multiple student sizes to map quality-efficiency frontier for deployment decisions.
