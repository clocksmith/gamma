# Translation Dataset Quality Report

Generated: 2026-03-08 20:54:55 UTC

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
| gold_natural_draft.shard_04_seed_plus_manual | 69.7475 | 100.0 | 100.0 | 75.653 | 27.4633 | 45.2306 | 33.8379 | 225 |

## Dataset Notes

### gold_natural_draft.shard_04_seed_plus_manual

- path: `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed_plus_manual.jsonl`
- counts_by_pair: `{"en-es": 126, "es-en": 99}`
- duplicate pressure: exact_unique_ratio=1.0, source_unique_ratio=1.0, target_unique_ratio=1.0
- templated-signal: digit_row_ratio=0.0533, time_marker_ratio=0.0, date_word_row_ratio=0.0
- gold overlap: exact_overlap_pct=0.0, loose_overlap_pct=0.0
