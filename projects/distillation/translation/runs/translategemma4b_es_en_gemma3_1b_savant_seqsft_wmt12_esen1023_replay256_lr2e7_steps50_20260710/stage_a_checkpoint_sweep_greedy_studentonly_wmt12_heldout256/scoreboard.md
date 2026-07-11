# Stage B Checkpoint Sweep Scoreboard

Updated: 2026-07-11 00:13:11 UTC
Run root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqsft_wmt12_esen1023_replay256_lr2e7_steps50_20260710`
Decode: `greedy`

## Checkpoint Ranking

| checkpoint | step | evals_done | evals_expected | avg_bleu | avg_chrf | wmt12_heldout_256_bleu | wmt12_heldout_256_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000030 | 30 | 1 | 1 | 30.6340 | 57.0771 | 30.6340 | 57.0771 |
| checkpoint-000010 | 10 | 1 | 1 | 30.4784 | 56.9409 | 30.4784 | 56.9409 |
| checkpoint-000050 | 50 | 1 | 1 | 30.2732 | 56.9117 | 30.2732 | 56.9117 |

## Eval Rows

| checkpoint | step | eval | bleu | chrf | samples | beams | length_penalty | candidates | candidate_selection | duration_s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| checkpoint-000010 | 10 | wmt12_heldout_256 | 30.4784 | 56.9409 | 256 | 1 | 1.0 |  |  | 171.0196 |
| checkpoint-000030 | 30 | wmt12_heldout_256 | 30.6340 | 57.0771 | 256 | 1 | 1.0 |  |  | 171.0189 |
| checkpoint-000050 | 50 | wmt12_heldout_256 | 30.2732 | 56.9117 | 256 | 1 | 1.0 |  |  | 171.0194 |

## Files

- Manifest: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqsft_wmt12_esen1023_replay256_lr2e7_steps50_20260710/stage_a_checkpoint_sweep_greedy_studentonly_wmt12_heldout256/manifest.jsonl`
- Eval rows CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqsft_wmt12_esen1023_replay256_lr2e7_steps50_20260710/stage_a_checkpoint_sweep_greedy_studentonly_wmt12_heldout256/scoreboard_eval_rows.csv`
- Checkpoint ranking CSV: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqsft_wmt12_esen1023_replay256_lr2e7_steps50_20260710/stage_a_checkpoint_sweep_greedy_studentonly_wmt12_heldout256/scoreboard_checkpoints.csv`
