# Translation Results Bundle

Generated: 2026-03-07 22:48:57 UTC

## Counts

- runs: 13
- eval rows: 33
- compare rows: 22
- manifests scanned: 3
- artifact dirs backfilled: 2

## Best External BLEU Rows by Run

| run | dataset | category | top_row | best_external_bleu | indomain_bleu | checkpoint | pair_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | Gold Legacy 1280 | Teacher Baseline | Teacher Baseline \| greedy | 27.5437 | 39.2681 |  | 1280 |
| translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | Merged Full 17532 | Student Stage B | Student Stage B \| checkpoint-002000 \| greedy | 7.9159 | 87.3266 | checkpoint-002000 | 17532 |
| translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | Merged Subset 1280 | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 6.7827 |  | checkpoint-004000 | 1280 |
| translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z | Merged Subset 2560 | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 6.1746 |  | checkpoint-004000 | 2560 |

## Backfilled Artifact Dirs

| kind | artifact_dir | rows |
| --- | --- | --- |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z/stage_a_live_eval | 8 |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z/stage_a_live_eval | 3 |
