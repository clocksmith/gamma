# Gold Expansion Dataset Build

Gold core: `projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl`
Universe: `projects/distillation/translation/training_data/translate_distill_pairs_en_es_2way.train.merged.jsonl`

## Buckets

| bucket | rows | score_avg | naturalness_avg | counts_by_pair |
| --- | --- | --- | --- | --- |
| exact_mined | 640 | 97.6265 | 97.6265 | {"en-es": 320, "es-en": 320} |
| hard_natural | 0 | 0.0 | 0.0 | {} |
| rewrite_queue | 0 | 0.0 | 0.0 | {} |
| candidate_exact_hard | 1920 | 99.2088 | 97.1071 | {"en-es": 960, "es-en": 960} |

## Recommendation

- Train Stage A first on `candidate_exact_hard` before mixing any rewritten rows.
- Use shorter checkpoint horizons around `2k-16k`; the gold control peaked externally at `8k`.
- Treat `rewrite_queue` as a separate synthetic lane with explicit provenance.
