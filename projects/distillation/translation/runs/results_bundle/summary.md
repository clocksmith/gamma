# Translation Results Bundle

Generated: 2026-07-11 00:13:12 UTC

## Counts

- runs: 116
- eval rows: 506
- compare rows: 223
- manifests scanned: 88
- artifact dirs backfilled: 87

## Best External BLEU Rows by Run

| run | dataset | category | top_row | best_external_bleu | indomain_bleu | checkpoint | pair_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z |  | External Baseline | External Baseline \| greedy | 38.4519 | 59.4292 |  |  |
| baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z |  | External Baseline | External Baseline \| greedy | 37.9870 | 58.8747 |  |  |
| baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z |  | External Baseline | External Baseline \| greedy | 37.2022 | 58.5298 |  |  |
| baseline__facebook__m2m100_1.2b__2026-03-10T025214Z |  | External Baseline | External Baseline \| greedy | 36.8589 | 60.3346 |  |  |
| baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z |  | External Baseline | External Baseline \| greedy | 35.6963 | 61.2861 |  |  |
| baseline__google__translategemma-4b-it__2026-03-10T134941Z |  | External Baseline | External Baseline \| greedy | 34.0474 | 45.5415 |  |  |
| translategemma4b_es_en_gemma3_1b_savant_selectorsft_balanced_lr1e7_steps30_20260710 | selector_wmt12_esen640_replay_enes640.local.jsonl | Student Stage A | Student Stage A \| checkpoint-000025 \| greedy | 33.8287 |  | checkpoint-000025 | 1280 |
| translategemma4b_es_en_gemma3_1b_savant_seqkd_news_esen2048_replay800_lr1e6_steps400_20260710 | translategemma_news_esen2048_replay_enes800.local.jsonl | Student Stage A | Student Stage A \| checkpoint-000050 \| greedy | 33.7695 |  | checkpoint-000050 | 2848 |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1 | train_pairs.rows1600.normalized.jsonl | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 33.7353 | 54.4500 | checkpoint-004000 | 1600 |
| savant_student_teacher_paired_20260710 | translate_distill_pairs.eval3_indomain_clean_merged_128.jsonl | Student Stage A | Student Stage A \| checkpoint-004000 | 33.7353 | 54.4500 | checkpoint-004000 |  |
| translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1 | train_pairs.rows1600.normalized.jsonl | Student Stage A | Student Stage A \| checkpoint-000250 \| greedy | 33.6283 | 54.2064 | checkpoint-000250 | 1600 |
| savant_wmt12_lora_scale_sweep_20260710 | translate_distill_pairs.eval2_wmt13_enes_128.jsonl | Student Stage A | Student Stage A \| checkpoint-000100 | 33.4047 |  | checkpoint-000100 |  |

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
| 6 | 34.8408 | 60.3080 | student | savant_nativekd2_candidate_logprob_rerank_20260710 | selector/external_wmt13_128_v2 |
| 7 | 34.8274 | 60.4653 | student | savant_nativekd2_candidate_logprob_rerank_20260710 | selector/external_wmt13_128_mlp |
| 8 | 34.7792 | 60.4264 | student | savant_nativekd2_candidate_logprob_rerank_20260710 | selector/external_wmt13_128_quadratic |
| 9 | 34.6386 | 60.2419 | student | savant_nativekd2_candidate_logprob_rerank_20260710 | selector/external_wmt13_128 |
| 10 | 34.3513 | 61.6621 | student | translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710 | mixed_checkpoint_sweep_greedy_studentonly_external_es_en/external_wmt13_es_en__checkpoint-000060__greedy |
| 11 | 34.1896 | 59.9388 | student | savant_nativekd2_weight_delta_sweep_20260710 | alpha_100 |
| 12 | 34.1896 | 59.9388 | student | translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710 | mixed_checkpoint_sweep_greedy_studentonly_external/eval2_external__checkpoint-000025__greedy |
| 13 | 34.0580 | 59.8368 | student | savant_nativekd2_weight_delta_sweep_20260710 | alpha_050 |
| 14 | 34.0474 | 61.0088 | baseline | baseline__google__translategemma-4b-it__2026-03-10T134941Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 15 | 33.9422 | 59.7282 | student | translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710 | mixed_checkpoint_sweep_greedy_studentonly_external/eval2_external__checkpoint-000100__greedy |

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
| 10 | 56.2462 | 73.1068 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002500__greedy |
| 11 | 56.2174 | 72.9556 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T224540Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 12 | 56.0758 | 73.9235 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T225020Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 13 | 56.0748 | 72.6944 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-003000__greedy |
| 14 | 55.9867 | 73.3200 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T233133Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 15 | 55.9294 | 73.0533 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |

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
| generic_manifest | projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/selector | 4 |
| generic_manifest | projects/distillation/translation/runs/savant_nativekd2_candidate_logprob_rerank_20260710/wmt12_router_train_current_512 | 1 |
| generic_manifest | projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/es_en_sample8_t0p6_p0p9_mbrchrf | 1 |
| generic_manifest | projects/distillation/translation/runs/savant_nativekd2_directional_mbr_external_20260710/specialist_wmt12_es_en_128 | 1 |
| generic_manifest | projects/distillation/translation/runs/savant_student_teacher_paired_20260710/paired_checkpoint_sweep_greedy | 2 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_256/beam2_lp0p8 | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_256/beam2_lp1p0 | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_256/greedy | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/decode_policy_search_wmt12_mbr128/sample8_t0p6_p0p9_mbrchrf | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd2_balanced_sft010_kd010_lr1e6_steps200_20260710/mixed_checkpoint_sweep_greedy_studentonly_external | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_balanced_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_nativekd_esen_lr2e6_kd005_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_kddominant_sft005_kd010_lr2e6_steps400_20260710/mixed_checkpoint_sweep_greedy_studentonly_external | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_news_nativekd_lr3e6_kd005_steps2000_20260710/mixed_checkpoint_sweep_greedy_studentonly_external | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_selectorsft_balanced_lr1e7_steps30_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external | 6 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqkd_news_esen2048_replay800_lr1e6_steps400_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqsft_wmt12_esen1023_replay256_lr2e7_steps50_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_seqsft_wmt12_esen1023_replay256_lr2e7_steps50_20260710/stage_a_checkpoint_sweep_greedy_studentonly_wmt12_heldout256 | 3 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_external_es_en | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_specialist_nativekd_sft005_kd010_lr5e7_steps60_20260710/mixed_checkpoint_sweep_greedy_studentonly_wmt12_es_en128 | 3 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_lora_r16_lr1e5_steps1000_20260710/stage_a_checkpoint_sweep_greedy_studentonly_external | 2 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_savant_wmt12_nativekd_sft005_kd010_lr5e7_steps100_20260710/mixed_checkpoint_sweep_greedy_studentonly_external | 4 |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z/stage_a_live_eval | 8 |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z/stage_a_live_eval | 3 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z/stage_a_checkpoint_sweep_greedy | 6 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_confirm_best4/stage_a_checkpoint_sweep_greedy | 14 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexdense_pack06_prune10_seed42_500ckpts_v1/stage_a_checkpoint_sweep_greedy | 16 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_prune10_studentonly_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack04_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_prune10_defer_studentonly_v2/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexlow_pack06_random10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexpolish_pack06_prune10_ckpt3000_lr5e6_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1568_bf16_codexseed7_pack06_prune10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1584_bf16_codexprune05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 16 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexextend_pack06_replace10_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 24 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack04_replace10_studentonly_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/stage_a_checkpoint_sweep_greedy | 19 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexlow_pack06_replace10c_hfcacheauth_v1/stage_a_checkpoint_sweep_greedy_studentonly | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_6k_dense500_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 24 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_ckpt4000_lr5e6_1k_dense250_v1/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_codexreplace05_pack06_defer_studentonly_v1/stage_a_checkpoint_sweep_greedy | 16 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z/stage_a_checkpoint_sweep_greedy | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z/stage_a_checkpoint_sweep_greedy | 22 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T220428Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T224540Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T232655Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T000816Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T004931Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T013050Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T021203Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T025326Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T033442Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T041600Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T045717Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T053842Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T062002Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T070121Z/stage_a_checkpoint_sweep_greedy | 15 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T180127Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T192425Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T200534Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T204640Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T212756Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T220906Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T225020Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260311T233133Z/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a_checkpoint_sweep_greedy | 1 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_codexblend_pack06r10_pack08_v1/stage_a_checkpoint_sweep_greedy_studentonly | 8 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2240_bf16_confirm_best7/stage_a_checkpoint_sweep_greedy | 4 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z/stage_a_checkpoint_sweep_greedy | 26 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z/stage_a_checkpoint_sweep_greedy | 6 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy | 8 |
