# Eval Leaderboards

Generated: 2026-03-10 22:04:28 UTC

## external_wmt13_en_es_translation_benchmark_128

| rank | student_bleu | student_chrf | teacher_bleu | teacher_chrf | delta_bleu | delta_chrf | role | run | eval_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 38.4519 | 63.2696 |  |  |  |  | baseline | baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z | eval2_external__greedy |
| 2 | 37.9870 | 62.9284 |  |  |  |  | baseline | baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 3 | 37.2022 | 65.1621 |  |  |  |  | baseline | baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 4 | 36.8589 | 61.7235 |  |  |  |  | baseline | baseline__facebook__m2m100_1.2b__2026-03-10T025214Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 5 | 35.6963 | 61.7223 |  |  |  |  | baseline | baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 6 | 34.0474 | 61.0088 |  |  |  |  | baseline | baseline__google__translategemma-4b-it__2026-03-10T134941Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 7 | 31.9598 | 59.3118 | 34.0474 | 61.0088 | -2.0876 | -1.6970 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 8 | 31.2176 | 58.6350 | 34.0474 | 61.0088 | -2.8297 | -2.3737 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 9 | 31.1363 | 57.6913 | 34.0474 | 61.0088 | -2.9111 | -3.3174 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 10 | 31.0910 | 58.4055 | 34.0474 | 61.0088 | -2.9564 | -2.6033 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 11 | 31.0039 | 58.1323 | 34.0474 | 61.0088 | -3.0435 | -2.8764 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 12 | 30.2975 | 58.3705 | 34.0474 | 61.0088 | -3.7499 | -2.6382 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 13 | 28.4786 | 56.7284 | 34.0474 | 61.0088 | -5.5687 | -4.2803 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 14 | 27.9709 | 57.9468 | 27.5437 | 59.3547 | 0.4273 | -1.4078 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 15 | 27.7776 | 57.8237 | 27.5437 | 59.3547 | 0.2340 | -1.5309 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |
| 16 | 27.6770 | 57.5271 | 27.5437 | 59.3547 | 0.1333 | -1.8276 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 17 | 27.6477 | 57.7483 | 27.5437 | 59.3547 | 0.1041 | -1.6064 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 18 | 27.5437 | 59.3547 |  |  |  |  | teacher_baseline | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__teacher4b__greedy |
| 19 | 27.4061 | 57.1701 | 27.5437 | 59.3547 | -0.1375 | -2.1845 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |
| 20 | 27.2349 | 57.1826 | 27.5437 | 59.3547 | -0.3088 | -2.1721 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 21 | 27.2071 | 56.9757 | 27.5437 | 59.3547 | -0.3366 | -2.3790 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 22 | 27.1978 | 57.2337 | 27.5437 | 59.3547 | -0.3459 | -2.1209 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 23 | 27.1562 | 57.0173 | 27.5437 | 59.3547 | -0.3875 | -2.3374 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-008000__greedy |
| 24 | 27.1509 | 57.5913 | 27.5437 | 59.3547 | -0.3927 | -1.7634 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 25 | 27.1233 | 57.0740 | 27.5437 | 59.3547 | -0.4204 | -2.2806 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-001500__greedy |
| 26 | 27.0143 | 56.5292 | 27.5437 | 59.3547 | -0.5294 | -2.8255 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 27 | 26.9558 | 57.1979 | 27.5437 | 59.3547 | -0.5878 | -2.1568 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |
| 28 | 26.8830 | 57.4844 | 27.5437 | 59.3547 | -0.6607 | -1.8703 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004001__greedy |
| 29 | 26.8719 | 57.0090 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__stage_a32__sampled |
| 30 | 26.8327 | 56.7330 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__stage_a8__greedy |
| 31 | 26.4766 | 56.7615 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-008000__greedy |
| 32 | 26.4599 | 56.7285 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__stage_a24__greedy |
| 33 | 26.4151 | 56.7315 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__stage_a16__greedy |
| 34 | 26.3488 | 56.7732 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__stage_a32__greedy |
| 35 | 26.2465 | 56.1884 | 27.5437 | 59.3547 | -1.2972 | -3.1662 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 36 | 26.0284 | 56.8031 | 27.5437 | 59.3547 | -1.5152 | -2.5516 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 37 | 25.9958 | 56.8890 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-016000__greedy |
| 38 | 25.9377 | 56.4858 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-032000__greedy |
| 39 | 25.7862 | 56.5766 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-024000__greedy |
| 40 | 25.4584 | 56.8557 | 27.5437 | 59.3547 | -2.0852 | -2.4990 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-006000__greedy |
| 41 | 25.1820 | 57.0220 | 27.5437 | 59.3547 | -2.3616 | -2.3326 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-008000__greedy |
| 42 | 24.8029 | 55.7317 | 27.5437 | 59.3547 | -2.7408 | -3.6230 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-002000__greedy |
| 43 | 24.7623 | 56.4720 | 27.5437 | 59.3547 | -2.7813 | -2.8827 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval2_external__checkpoint-004000__greedy |
| 44 | 22.6563 | 56.8741 |  |  |  |  | baseline | baseline__google__translategemma-4b-it__2026-03-10T014945Z | eval2_external__greedy |
| 45 | 7.9262 | 33.4874 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__final__sampled |
| 46 | 7.9159 | 35.6396 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stageb002000_external_wmt13_greedy_20260306 |
| 47 | 7.0652 | 34.9801 | 27.6332 | 59.3886 | -20.5681 | -24.4085 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea12k_eval2_greedy_20260306_rerun_tmux |
| 48 | 6.7827 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea4k_eval2_greedy_live |
| 49 | 6.5945 | 31.4518 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval2_external__final__greedy |
| 50 | 6.5945 | 31.4518 | 27.5437 | 59.3547 | -20.9492 | -27.9029 | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | eval_bleu_vs_teacher_enes_eval2_20260304_093211_gfxoverride |
| 51 | 6.4642 | 33.9828 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea32_eval2_greedy_20260306 |
| 52 | 6.4361 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea24k_eval2_greedy_live |
| 53 | 6.1746 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z | eval_stagea4k_eval2_greedy_live |
| 54 | 5.7466 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea28k_eval2_greedy_live |
| 55 | 5.7465 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea20k_eval2_greedy_live |
| 56 | 5.6350 | 33.7260 | 27.6332 | 59.3886 | -21.9983 | -25.6626 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea22k_eval2_greedy_20260306_rerun_tmux |
| 57 | 4.9284 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea8k_eval2_greedy_live |
| 58 | 4.6705 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea12k_eval2_greedy_live |
| 59 | 4.5627 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z | eval_stagea12k_eval2_greedy_live |
| 60 | 3.9701 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z | eval_stagea8k_eval2_greedy_live |
| 61 | 3.3827 |  |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | eval_stagea16k_eval2_greedy_live |
| 62 | 0.0315 | 15.7204 |  |  |  |  | baseline | baseline__google__gemma-3-1b-it__2026-03-10T135924Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |
| 63 | 0.0285 | 15.4027 |  |  |  |  | baseline | baseline__google__gemma-3-1b-it__2026-03-10T020400Z | baseline_checkpoint_sweep_greedy/eval2_external__final__greedy |

## indomain_clean_merged_en_es_translation_benchmark_128

| rank | student_bleu | student_chrf | teacher_bleu | teacher_chrf | delta_bleu | delta_chrf | role | run | eval_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 87.4218 | 97.4243 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea32_eval3_greedy_20260306 |
| 2 | 87.3266 | 97.2802 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stageb002000_indomain_clean_greedy_20260306 |
| 3 | 87.1698 | 97.2928 | 39.1485 | 68.9521 | 48.0213 | 28.3407 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea22k_eval3_greedy_20260306_rerun_tmux |
| 4 | 86.5173 | 96.6936 | 39.1485 | 68.9521 | 47.3687 | 27.7415 | student | translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | eval_stagea12k_eval3_greedy_20260306_rerun_tmux |
| 5 | 61.2861 | 76.7630 |  |  |  |  | baseline | baseline__helsinki-nlp__opus-mt-en-es__2026-03-10T020411Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 6 | 60.3346 | 76.8958 |  |  |  |  | baseline | baseline__facebook__m2m100_1.2b__2026-03-10T025214Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 7 | 59.4292 | 76.3280 |  |  |  |  | baseline | baseline__facebook__nllb-200-distilled-600m__2026-03-10T014951Z | eval3_indomain_clean__greedy |
| 8 | 58.8747 | 76.8520 |  |  |  |  | baseline | baseline__facebook__nllb-200-distilled-1.3b__2026-03-10T023424Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 9 | 58.5298 | 76.7342 |  |  |  |  | baseline | baseline__helsinki-nlp__opus-mt-es-en__2026-03-10T022943Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 10 | 54.8412 | 72.0276 | 45.5415 | 70.9157 | 9.2997 | 1.1118 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 11 | 54.6568 | 72.0550 | 45.5415 | 70.9157 | 9.1153 | 1.1392 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T212318Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 12 | 53.6107 | 72.5728 | 45.5415 | 70.9157 | 8.0692 | 1.6571 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 13 | 53.5193 | 72.7240 | 45.5415 | 70.9157 | 7.9778 | 1.8082 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 14 | 53.4297 | 72.6389 | 45.5415 | 70.9157 | 7.8882 | 1.7232 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T203554Z_repair_drop_01_05 | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 15 | 52.9668 | 72.3839 | 45.5415 | 70.9157 | 7.4252 | 1.4682 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T192822Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 16 | 52.7402 | 70.5829 | 45.5415 | 70.9157 | 7.1987 | -0.3329 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 17 | 51.7370 | 70.4927 | 45.5415 | 70.9157 | 6.1955 | -0.4231 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T013436Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 18 | 48.7992 | 69.9488 | 39.2681 | 69.0260 | 9.5312 | 0.9228 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 19 | 48.7948 | 71.7605 | 39.2681 | 69.0260 | 9.5267 | 2.7345 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 20 | 48.5998 | 71.4817 | 39.2681 | 69.0260 | 9.3317 | 2.4557 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-006000__greedy |
| 21 | 48.2256 | 69.7793 | 39.2681 | 69.0260 | 8.9576 | 0.7533 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-006000__greedy |
| 22 | 47.9813 | 69.8823 | 39.2681 | 69.0260 | 8.7133 | 0.8563 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 23 | 47.9571 | 69.8997 | 39.2681 | 69.0260 | 8.6890 | 0.8738 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-008000__greedy |
| 24 | 47.8638 | 71.2799 | 39.2681 | 69.0260 | 8.5957 | 2.2539 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 25 | 47.6425 | 69.9659 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-008000__greedy |
| 26 | 47.4291 | 69.7695 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-016000__greedy |
| 27 | 47.4261 | 69.7575 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-024000__greedy |
| 28 | 47.3852 | 69.5635 | 39.2681 | 69.0260 | 8.1171 | 0.5375 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-006000__greedy |
| 29 | 47.3434 | 69.6866 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-032000__greedy |
| 30 | 47.2797 | 70.2364 | 39.2681 | 69.0260 | 8.0116 | 1.2104 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 31 | 47.1364 | 69.5194 | 39.2681 | 69.0260 | 7.8683 | 0.4935 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 32 | 46.9378 | 70.0786 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval3_indomain_clean__stage_a32__greedy |
| 33 | 46.8090 | 69.8480 | 39.2681 | 69.0260 | 7.5409 | 0.8221 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-006000__greedy |
| 34 | 46.7597 | 69.8898 | 39.2681 | 69.0260 | 7.4916 | 0.8638 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-008000__greedy |
| 35 | 46.6153 | 70.5080 | 39.2681 | 69.0260 | 7.3472 | 1.4820 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1280_bf16_20260309T185602Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 36 | 46.5905 | 69.7971 | 39.2681 | 69.0260 | 7.3225 | 0.7711 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 37 | 46.5402 | 70.9114 | 39.2681 | 69.0260 | 7.2721 | 1.8854 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T001204Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 38 | 46.3742 | 69.5169 | 39.2681 | 69.0260 | 7.1061 | 0.4910 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260308T164813Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004000__greedy |
| 39 | 46.2854 | 69.7740 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval3_indomain_clean__stage_a32__sampled |
| 40 | 45.8440 | 70.1927 | 39.2681 | 69.0260 | 6.5759 | 1.1667 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1920_bf16_20260310T005321Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-004001__greedy |
| 41 | 45.5415 | 70.9157 |  |  |  |  | baseline | baseline__google__translategemma-4b-it__2026-03-10T134941Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 42 | 44.6716 | 70.1758 | 39.2681 | 69.0260 | 5.4035 | 1.1499 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T195639Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-002000__greedy |
| 43 | 43.7387 | 69.1177 | 39.2681 | 69.0260 | 4.4707 | 0.0917 | student | translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows2560_bf16_20260309T022454Z | stage_a_checkpoint_sweep_greedy/eval3_indomain_clean__checkpoint-001500__greedy |
| 44 | 39.2681 | 69.0260 |  |  |  |  | teacher_baseline | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval3_indomain_clean__teacher4b__greedy |
| 45 | 35.6382 | 67.9067 |  |  |  |  | baseline | baseline__google__translategemma-4b-it__2026-03-10T014945Z | eval3_indomain_clean__greedy |
| 46 | 19.3169 | 42.6927 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval3_indomain_clean__final__sampled |
| 47 | 18.7825 | 41.3420 |  |  |  |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | ablation_stage_decode_20260304_094102/eval3_indomain_clean__final__greedy |
| 48 | 1.2862 | 21.3217 |  |  |  |  | baseline | baseline__google__gemma-3-1b-it__2026-03-10T020400Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |
| 49 | 0.9504 | 21.3408 |  |  |  |  | baseline | baseline__google__gemma-3-1b-it__2026-03-10T135924Z | baseline_checkpoint_sweep_greedy/eval3_indomain_clean__final__greedy |

## translate_distill_pairs.eval.jsonl

| rank | student_bleu | student_chrf | teacher_bleu | teacher_chrf | delta_bleu | delta_chrf | role | run | eval_dir |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 82.5093 |  | 52.4160 |  | 30.0933 |  | student | translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | eval_bleu_vs_teacher_enes_20260304_083646_offlinefix |
