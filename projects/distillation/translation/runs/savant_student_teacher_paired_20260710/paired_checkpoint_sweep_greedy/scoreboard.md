# Stage A Checkpoint Evaluation Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/savant_student_teacher_paired_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | 2 | 2 | 44.0926 | 65.9790 | 33.7353 | 59.6065 | 54.4500 | 72.3516 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-004000 | 4000 | external_wmt13_en_es_translation_benchmark_128 | 33.7353 | 59.6065 | 128 |  |  |  |  |  |
| checkpoint-004000 | 4000 | indomain_clean_merged_en_es_translation_benchmark_128 | 54.4500 | 72.3516 | 128 |  |  |  |  |  |

## Files

- Manifest: `projects/distillation/translation/runs/savant_student_teacher_paired_20260710/paired_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/savant_student_teacher_paired_20260710/paired_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/savant_student_teacher_paired_20260710/paired_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
