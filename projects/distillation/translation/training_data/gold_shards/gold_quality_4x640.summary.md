# Gold Quality Shards

Gold core: `projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl`
Mined exact: `projects/distillation/translation/training_data/gold_expansion/gold_plus_1280.exact_mined.jsonl`

## Shards

| shard | rows | counts_by_pair | path |
| --- | --- | --- | --- |
| shard_01_gold_core_a | 640 | {"en-es": 320, "es-en": 320} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl |
| shard_02_gold_core_b | 640 | {"en-es": 320, "es-en": 320} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl |
| shard_03_mined_exact | 640 | {"en-es": 320, "es-en": 320} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_03_mined_exact.jsonl |
| shard_04_hybrid_seed_tail | 330 | {"en-es": 113, "es-en": 217} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_04_hybrid_seed_tail.jsonl |
| shard_04_hybrid_full | 640 | {"en-es": 320, "es-en": 320} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_04_hybrid_full.jsonl |
| train_3x640 | 1920 | {"en-es": 960, "es-en": 960} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_3x640.jsonl |
| train_4x640 | 2560 | {"en-es": 1280, "es-en": 1280} | projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.train_4x640.jsonl |

## Authored Requirement

- Required authored rows total: `310`
- Required `en-es`: `207`
- Required `es-en`: `103`

The hybrid fourth shard is built as the 330-row mined tail plus authored rows sized to restore a balanced 640-row shard.
