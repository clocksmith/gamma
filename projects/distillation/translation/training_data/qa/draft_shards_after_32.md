# Translation Dataset Quality Report

Generated: 2026-03-08 20:04:41 UTC

## Score Legend

- `alignment_quality`: field completeness, cross-language sanity, and length-ratio hygiene
- `duplication_hygiene`: exact/source/target uniqueness
- `diversity`: direction balance plus token and length entropy
- `gold_similarity`: overlap and distribution closeness to the restored March 3 gold set
- `external_match`: style similarity to eval2 external data
- `indomain_match`: style similarity to eval3 indomain data

## Summary

| dataset | overall | alignment | duplication | diversity | gold | external | indomain | rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| gold_natural_draft.shard_03_draft_full | 72.6894 | 100.0 | 100.0 | 84.7367 | 32.2347 | 48.7307 | 36.5888 | 640 |
| gold_natural_draft.shard_04_seed | 67.9083 | 100.0 | 100.0 | 71.7688 | 24.1669 | 41.5646 | 31.5315 | 125 |

## Dataset Notes

### gold_natural_draft.shard_03_draft_full

- path: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_03_draft_full.jsonl`
- counts_by_pair: `{"en-es": 320, "es-en": 320}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=0.9969
- templated-signal: digit_row_ratio=0.0, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0

### gold_natural_draft.shard_04_seed

- path: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed.jsonl`
- counts_by_pair: `{"en-es": 76, "es-en": 49}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.056, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
