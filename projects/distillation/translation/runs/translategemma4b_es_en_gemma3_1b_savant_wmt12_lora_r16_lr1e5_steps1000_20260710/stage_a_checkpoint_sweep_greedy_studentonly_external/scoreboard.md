# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_lora_r16_lr1e5_steps1000_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | 1 | 1 | 32.8773 | 58.8924 | 32.8773 | 58.8924 |
| checkpoint-000200 | 200 | 1 | 1 | 31.6911 | 57.4136 | 31.6911 | 57.4136 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000100 | 100 | external_wmt13_en_es_translation_benchmark_128 | 32.8773 | 58.8924 | 128 |  |  |  |  | 63.0077 |
| checkpoint-000200 | 200 | external_wmt13_en_es_translation_benchmark_128 | 31.6911 | 57.4136 | 128 |  |  |  |  | 63.0080 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_lora_r16_lr1e5_steps1000_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_lora_r16_lr1e5_steps1000_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_lora_r16_lr1e5_steps1000_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external/scoreboard_checkpoints.csv`
