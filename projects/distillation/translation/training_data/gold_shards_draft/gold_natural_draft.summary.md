# Gold Natural Draft Shards

Gold core: `projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl`
Universe: `projects/distillation/translation/training_data/translate_distill_pairs_en_es_2way.train.merged.jsonl`

## Pools

- Human pool: `585` rows {"en-es": 315, "es-en": 270}
- Strict mined pool: `371` rows {"en-es": 173, "es-en": 198}
- Review queue: `203` rows {"en-es": 72, "es-en": 131}

## Draft Shards

- `shard_03_draft_full`: `640` rows {"en-es": 320, "es-en": 320}
- `shard_04_seed`: `316` rows {"en-es": 168, "es-en": 148}
- Missing rows to finish `shard_04`: `324`

## Note

This draft intentionally refuses to auto-fill the second shard with lower-confidence repetitive mined rows.
The review queue is the next source for manual promotion or rewrite.
