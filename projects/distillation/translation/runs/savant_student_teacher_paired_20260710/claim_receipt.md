# Savant Student Beats TranslateGemma

Status: **PASS**

Scope: in-domain clean merged EN<->ES translation holdout, 128 rows.

## Claim

The Gemma 3 1B Savant student beats `google/translategemma-4b-it` on both BLEU
and chrF in one paired greedy evaluation. It also wins both metrics separately
for EN->ES and ES->EN.

## Models

- Student:
  `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/stage_a/checkpoint-004000`
- Teacher: `google/translategemma-4b-it`
- Student size class: 1B
- Teacher size class: 4B

## Result

| scope | student BLEU | teacher BLEU | delta BLEU | student chrF | teacher chrF | delta chrF |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| overall | 54.4500 | 45.4563 | +8.9937 | 72.3516 | 70.8387 | +1.5129 |
| EN->ES | 57.7884 | 51.3369 | +6.4515 | 73.0159 | 72.9659 | +0.0499 |
| ES->EN | 50.3034 | 37.7406 | +12.5628 | 71.5408 | 68.2184 | +3.3224 |

## Contract

- Pair file:
  `projects/distillation/translation/training_data/translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl`
- Pair-file SHA-256:
  `0bef72ecdc09eb0d65564312f76c0333d756d5a4978608b4f69a6b5ad4857e39`
- Student training input:
  `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/inputs/train_pairs.rows1600.normalized.jsonl`
- Student training-input SHA-256:
  `2cfea3f81a44cb469d9229862a98763c7e31a78d1ae78a3b90fc54fd8c543e92`
- Decode: greedy, `num_beams=1`, `temperature=0.0`
- Runtime: `.venv_rocm`, `torch=2.12.1+rocm7.2`, `transformers=4.57.6`
- Device: Radeon 8060S Graphics through `device=cuda`, bfloat16
- Student tokenizer: student checkpoint tokenizer
- Teacher tokenizer: TranslateGemma tokenizer

Validation found 128 student rows, 128 teacher rows, identical row order, no
empty predictions, and no prompt fragments in either prediction file.
Normalized comparison against the student's 1,600-row training input found
zero exact source matches and zero exact source-target pair matches.

## Artifacts

- Verifier:
  `.venv_rocm/bin/python projects/distillation/translation/runs/savant_student_teacher_paired_20260710/verify_claim.py`
- Sweep scoreboard:
  `projects/distillation/translation/runs/savant_student_teacher_paired_20260710/paired_checkpoint_sweep_greedy/scoreboard.md`
- Paired summary:
  `projects/distillation/translation/runs/savant_student_teacher_paired_20260710/indomain_clean_128/compare_eval_summary.json`
- Paired-summary SHA-256:
  `c7dbdfb6b780a4a35bde28a048ca49abbcd8d90d8a4be81e6d356ecd82b4676a`
- Student predictions SHA-256:
  `5ccff143480f3a23e5ad6ad5036c914b5de57c070a1a65039d079ea8da859cf9`
- Teacher predictions SHA-256:
  `dc0e61a09cb41564aa0ff05b0daafa531e95025707d5ae109ee0c7c50ce405b7`

## Boundary

This is an in-domain holdout claim, not an external WMT13 claim. The paired
external receipt in the same run scores the student at `33.7353 BLEU / 59.6065
chrF` and the teacher at `33.6973 BLEU / 60.8011 chrF`; the student wins BLEU
but not chrF there.
