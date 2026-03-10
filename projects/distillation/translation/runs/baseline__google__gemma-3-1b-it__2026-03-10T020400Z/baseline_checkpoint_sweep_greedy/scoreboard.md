# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-03-10 14:10:01 UTC
Run root: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T020400Z`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| final | 0 | 2 | 2 | 0.6573 | 18.3622 | 0.0285 | 15.4027 | 1.2862 | 21.3217 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | duration_s |
| --- | --- | --- | --- | --- | --- | --- |
| final | 0 | external_wmt13_en_es_translation_benchmark_128 | 0.0285 | 15.4027 | 128 | 189.5799 |
| final | 0 | indomain_clean_merged_en_es_translation_benchmark_128 | 1.2862 | 21.3217 | 128 | 118.8743 |

## Files

- Manifest: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T020400Z/baseline_checkpoint_sweep_greedy/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T020400Z/baseline_checkpoint_sweep_greedy/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T020400Z/baseline_checkpoint_sweep_greedy/scoreboard_checkpoints.csv`
