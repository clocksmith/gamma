# Translation Distillation Merged Comparison

Generated: 2026-03-07 00:43:52 UTC
Runs root: `/home/x/deco/gamma/projects/distillation/translation/runs`

One row = one comparable eval group (run + variant/checkpoint + decode), with strict run-parameter columns.

| run | group | decode | train_rows | stage_a_steps | stage_b_steps | teacher_model_cfg | student_model_cfg | evaluated_model | source_langs | target_langs | lambda_kd | mu_triplet | external_wmt13_en_es_translation_benchmark_128_bleu | external_wmt13_en_es_translation_benchmark_128_chrf | indomain_clean_merged_en_es_translation_benchmark_128_bleu | indomain_clean_merged_en_es_translation_benchmark_128_chrf |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | stage_b__checkpoint-002000 | greedy |  |  |  |  |  | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210/stage_b/checkpoint-002000 |  |  |  |  | 7.9159 | 35.6396 | 87.3266 | 97.2802 |
| translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | stage_a__checkpoint-032000 | greedy |  |  |  |  |  | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210/stage_a/checkpoint-032000 |  |  |  |  | 6.4642 | 33.9828 | 87.4218 | 97.4243 |
| translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | stage_a__checkpoint-022000 | greedy |  |  |  |  |  | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210/stage_a/checkpoint-022000 |  |  |  |  | 5.6350 | 33.7260 | 87.1698 | 97.2928 |
| translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | stage_a__checkpoint-012000 | greedy |  |  |  |  |  | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210/stage_a/checkpoint-012000 |  |  |  |  | 7.0652 | 34.9801 | 86.5173 | 96.6936 |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | teacher4b | greedy | 1280 | 32000 | 32000 | google/translategemma-4b-it | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_b/checkpoint-000005 | /home/x/.cache/huggingface/hub/models--google--translategemma-4b-it/snapshots/10042cb0e6e7fdce748996a71dc3dc432a4e0c89 | en,es | en,es | 0.5000 | 0.1000 | 27.5437 | 59.3547 | 39.2681 | 69.0260 |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | stage_a__checkpoint-032000 | sampled | 1280 | 32000 | 32000 | google/translategemma-4b-it | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_b/checkpoint-000005 | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_a/checkpoint-032000 | en,es | en,es | 0.5000 | 0.1000 | 26.8719 | 57.0090 | 46.2854 | 69.7740 |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | stage_a__checkpoint-032000 | greedy | 1280 | 32000 | 32000 | google/translategemma-4b-it | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_b/checkpoint-000005 | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_a/checkpoint-032000 | en,es | en,es | 0.5000 | 0.1000 | 26.3488 | 56.7732 | 46.9378 | 70.0786 |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | final | sampled | 1280 | 32000 | 32000 | google/translategemma-4b-it | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_b/checkpoint-000005 | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/final | en,es | en,es | 0.5000 | 0.1000 | 7.9262 | 33.4874 | 19.3169 | 42.6927 |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | final | greedy | 1280 | 32000 | 32000 | google/translategemma-4b-it | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/stage_b/checkpoint-000005 | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_full_20260303_114100/final | en,es | en,es | 0.5000 | 0.1000 | 6.5945 | 31.4518 | 18.7825 | 41.3420 |

## Dataset Labels

- `external_wmt13_en_es_translation_benchmark_128`: External WMT13 EN-ES translation benchmark (128 rows)
- `indomain_clean_merged_en_es_translation_benchmark_128`: In-domain clean merged EN-ES translation benchmark (128 rows)
