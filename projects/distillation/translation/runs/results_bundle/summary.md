# Translation Results Bundle

Generated: 2026-03-10 14:10:01 UTC

## Counts

- runs: 40
- eval rows: 98
- compare rows: 55
- manifests scanned: 21
- artifact dirs backfilled: 20

## Best External BLEU Rows by Run

| run | dataset | category | top_row | best_external_bleu | indomain_bleu | checkpoint | pair_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z |  | External Baseline | External Baseline \| greedy | 38.4519 | 59.4292 |  |  |
| baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z |  | External Baseline | External Baseline \| greedy | 37.9870 | 58.8747 |  |  |
| baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z |  | External Baseline | External Baseline \| greedy | 37.2022 | 58.5298 |  |  |
| baseline__facebook__m2m100_1.2b__2026-03-10T025214Z |  | External Baseline | External Baseline \| greedy | 36.8589 | 60.3346 |  |  |
| baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z |  | External Baseline | External Baseline \| greedy | 35.6963 | 61.2861 |  |  |
| baseline__google__translategemma-4b-it__2026-03-10T134941Z |  | External Baseline | External Baseline \| greedy | 34.0474 | 45.5415 |  |  |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | train_pairs.rows2560.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 27.9709 | 48.7948 | checkpoint-004000 | 2560 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-002000 \| greedy | 27.6770 | 47.8638 | checkpoint-002000 | 1920 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z | train_pairs.rows1920.merged.jsonl | Student Stage A | Student Stage A \| checkpoint-004001 \| greedy | 27.6477 | 45.8440 | checkpoint-004001 | 1920 |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | Gold Legacy 1280 | Teacher Baseline | Teacher Baseline \| greedy | 27.5437 | 39.2681 |  | 1280 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | Gold Legacy 1280 | Student Stage A | Student Stage A \| checkpoint-006000 \| greedy | 27.4061 | 47.3852 | checkpoint-006000 | 1280 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | Gold Legacy 1280 | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 27.1978 | 48.7992 | checkpoint-004000 | 1280 |

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
| 7 | 27.9709 | 57.9468 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 8 | 27.7776 | 57.8237 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |
| 9 | 27.6770 | 57.5271 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 10 | 27.6477 | 57.7483 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 11 | 27.5437 | 59.3547 | teacher_baseline | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__teacher4b__greedy |
| 12 | 27.4061 | 57.1701 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |
| 13 | 27.2349 | 57.1826 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 14 | 27.2071 | 56.9757 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 15 | 27.1978 | 57.2337 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |

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
| 10 | 48.7992 | 69.9488 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 11 | 48.7948 | 71.7605 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 12 | 48.5998 | 71.4817 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-006000__greedy |
| 13 | 48.2256 | 69.7793 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-006000__greedy |
| 14 | 47.9813 | 69.8823 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 15 | 47.9571 | 69.8997 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-008000__greedy |

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
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z/stage_a_checkpoint_sweep_greedy | 19 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z/stage_a_checkpoint_sweep_greedy | 26 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z/stage_a_checkpoint_sweep_greedy | 6 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy | 8 |
