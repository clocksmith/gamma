# Gold Expansion Dataset Build

Gold core: `projects/distillation/translation/training_data/gold/translate_distill_pairs.gold_legacy1280_20260303_b8f685a.jsonl`
Universe: `projects/distillation/translation/training_data/translate_distill_pairs_en_es_2way.train.merged.jsonl`

## Buckets

| bucket | rows | score_avg | naturalness_avg | counts_by_pair |
| --- | --- | --- | --- | --- |
| exact_mined | 512 | 99.6195 | 99.6195 | {"en-es": 256, "es-en": 256} |
| hard_natural | 4 | 109.25 | 97.25 | {"en-es": 1, "es-en": 3} |
| rewrite_queue | 1024 | 70.6105 | 69.8168 | {"en-es": 512, "es-en": 512} |
| candidate_exact_hard | 1796 | 99.9121 | 97.6386 | {"en-es": 897, "es-en": 899} |

## Recommendation

- Train Stage A first on `candidate_exact_hard` before mixing any rewritten rows.
- Use shorter checkpoint horizons around `2k-16k`; the gold control peaked externally at `8k`.
- Treat `rewrite_queue` as a separate synthetic lane with explicit provenance.
