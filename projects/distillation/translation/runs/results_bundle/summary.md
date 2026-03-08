# Translation Results Bundle

Generated: 2026-03-08 15:56:35 UTC

## Counts

- runs: 16
- eval rows: 41
- compare rows: 26
- manifests scanned: 4
- artifact dirs backfilled: 3

## Best External BLEU Rows by Run

| run | dataset | category | top_row | best_external_bleu | indomain_bleu | checkpoint | pair_count |
| --- | --- | --- | --- | --- | --- | --- | --- |
| translategemma4b_es_en_gemma3_1b_full_train1280_20260303_114100 | Gold Legacy 1280 | Teacher Baseline | Teacher Baseline \| greedy | 27.5437 | 39.2681 |  | 1280 |
| translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z | Gold Legacy 1280 | Student Stage A | Student Stage A \| checkpoint-008000 \| greedy | 26.4766 | 47.6425 | checkpoint-008000 | 1280 |
| translategemma4b_es_en_gemma3_1b_full_train17532_real1b_20260305_210210 | Merged Full 17532 | Student Stage B | Student Stage B \| checkpoint-002000 \| greedy | 7.9159 | 87.3266 | checkpoint-002000 | 17532 |
| translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z | Merged Subset 1280 | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 6.7827 |  | checkpoint-004000 | 1280 |
| translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z | Merged Subset 2560 | Student Stage A | Student Stage A \| checkpoint-004000 \| greedy | 6.1746 |  | checkpoint-004000 | 2560 |

## Backfilled Artifact Dirs

| kind | artifact_dir | rows |
| --- | --- | --- |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset1280_seed42_20260307T013333Z/stage_a_live_eval | 8 |
| stage_a_live_eval | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_cpu_subset2560_seed42_20260307T013333Z/stage_a_live_eval | 3 |
| generic_manifest | projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldlegacy1280_bf16_20260307T231031Z/stage_a_checkpoint_sweep_greedy | 8 |
