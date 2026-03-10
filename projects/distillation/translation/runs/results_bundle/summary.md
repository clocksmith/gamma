# Translation Results Bundle

Generated: 2026-03-10 22:04:28 UTC

## Counts

- runs: 46
- eval rows: 113
- compare rows: 62
- manifests scanned: 24
- artifact dirs backfilled: 23

## Best External BLEU Rows by Run

| run | dataset | category | top_row | best_external_bleu | indomain_bleu | checkpoint | pair_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z |  | External Baseline | External Baseline \| greedy | 38.4519 | 59.4292 |  |  |
| baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z |  | External Baseline | External Baseline \| greedy | 37.9870 | 58.8747 |  |  |
| baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z |  | External Baseline | External Baseline \| greedy | 37.2022 | 58.5298 |  |  |
| baseline__facebook__m2m100_1.2b__2026-03-10T025214Z |  | External Baseline | External Baseline \| greedy | 36.8589 | 60.3346 |  |  |
| baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z |  | External Baseline | External Baseline \| greedy | 35.6963 | 61.2861 |  |  |
| baseline__google__translategemma-4b-it__2026-03-10T134941Z |  | External Baseline | External Baseline \| greedy | 34.0474 | 45.5415 |  |  |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-004001 \| greedy | 31.9598 | 54.6568 | checkpoint-004001 | 1920 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-002000 \| greedy | 31.1363 | 52.9668 | checkpoint-002000 | 1920 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-004001 \| greedy | 31.0910 | 53.5193 | checkpoint-004001 | 1920 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-004001 \| greedy | 28.4786 | 51.7370 | checkpoint-004001 | 1920 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | train_pairs.rows2560.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 27.9709 | 48.7948 | checkpoint-004000 | 2560 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-002000 \| greedy | 27.6770 | 47.8638 | checkpoint-002000 | 1920 |

## Deduped Eval Leaderboards

- `leaderboard_all_compare_rows.csv`
- `leaderboard_external_wmt13_en_es_translation_benchmark_128.csv`
- `leaderboard_indomain_clean_merged_en_es_translation_benchmark_128.csv`
- `leaderboard.md`

### External WMT13 EN/ES 128

| rank | student_bleu | student_chrf | role | run | eval_dir |
| --- | --- | --- | --- | --- | --- |
| 1 | 38.4519 | 63.2696 | baseline | baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z | eval2_external__greedy |
| 2 | 37.9870 | 62.9284 | baseline | baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 3 | 37.2022 | 65.1621 | baseline | baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 4 | 36.8589 | 61.7235 | baseline | baseline__facebook__m2m100_1.2b__2026-03-10T025214Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 5 | 35.6963 | 61.7223 | baseline | baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 6 | 34.0474 | 61.0088 | baseline | baseline__google__translategemma-4b-it__2026-03-10T134941Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 7 | 31.9598 | 59.3118 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 8 | 31.2176 | 58.6350 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 9 | 31.1363 | 57.6913 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 10 | 31.0910 | 58.4055 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 11 | 31.0039 | 58.1323 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 12 | 30.2975 | 58.3705 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 13 | 28.4786 | 56.7284 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 14 | 27.9709 | 57.9468 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 15 | 27.7776 | 57.8237 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |

### In-Domain Clean EN/ES 128

| rank | student_bleu | student_chrf | role | run | eval_dir |
| --- | --- | --- | --- | --- | --- |
| 1 | 87.4218 | 97.4243 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea32_eval3_greedy_20260306 |
| 2 | 87.3266 | 97.2802 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stageb002000_indomain_clean_greedy_20260306 |
| 3 | 87.1698 | 97.2928 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea22k_eval3_greedy_20260306_rerun_tmux |
| 4 | 86.5173 | 96.6936 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea12k_eval3_greedy_20260306_rerun_tmux |
| 5 | 61.2861 | 76.7630 | baseline | baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 6 | 60.3346 | 76.8958 | baseline | baseline__facebook__m2m100_1.2b__2026-03-10T025214Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 7 | 59.4292 | 76.3280 | baseline | baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z | eval3_indomain_clean__greedy |
| 8 | 58.8747 | 76.8520 | baseline | baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 9 | 58.5298 | 76.7342 | baseline | baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 10 | 54.8412 | 72.0276 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 11 | 54.6568 | 72.0550 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 12 | 53.6107 | 72.5728 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 13 | 53.5193 | 72.7240 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 14 | 53.4297 | 72.6389 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 15 | 52.9668 | 72.3839 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |

## Backfilled Artifact Dirs

| kind | artifact_dir | rows |
| --- | --- | --- |
| generic_manifest | projects/distillation/translation/runs/baseline__facebook__m2m100_1.2b__2026-03-10T025214Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T020400Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__google__gemma-3-1b-it__2026-03-10T135924Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T014945Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__google__translategemma-4b-it__2026-03-10T134941Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z/baseline_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z/baseline_checkpoint_sweep_greedy | 2 |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z/stage_a_live_eval | 8 |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z/stage_a_live_eval | 3 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z/stage_a_checkpoint_sweep_greedy | 6 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z/stage_a_checkpoint_sweep_greedy | 22 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z/stage_a_checkpoint_sweep_greedy | 26 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z/stage_a_checkpoint_sweep_greedy | 6 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy | 8 |
