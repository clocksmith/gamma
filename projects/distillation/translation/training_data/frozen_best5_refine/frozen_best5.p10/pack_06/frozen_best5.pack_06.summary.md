# Frozen Best-5 Pack 06 Audit

- run_root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5`
- target_pack: `06`
- prune_fraction: `0.1`
- rows_in_pack: `320`
- rows_to_remove: `{'en-es': 16, 'es-en': 16}`
- audit_csv: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_06/frozen_best5.pack_06.audit.csv`

## Top Prune Candidates

| rank | pair | prune_score | source_file | row_id |
| --- | --- | --- | --- | --- |
| 1 | en-es | 67.2714 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `f90fb3b88a30e59ad08aa68686bfb142d48ebe91d97cfb6f10d535cd1bb4d940` |
| 2 | en-es | 64.0267 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `f4cb8baf2c9e7e3dc0c0545fb57f2abde7d197a73d6f7b1bc050e0be7ed0d999` |
| 3 | en-es | 63.6455 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `c86746225dbad0d42e62a374f4c3760acae7e8a636935506b5f19a24aaf020a7` |
| 4 | en-es | 63.3688 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `ba150b7c077470659a3c205722ccfb2a2ee431b5e1a3cb48425b88ca152bd3fc` |
| 5 | es-en | 63.2678 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `a1dd68bbd93992afb7423906eae8321d87c927a0774f17e5dfa4c85280d35c93` |
| 6 | es-en | 63.0 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `061da75a6ba99c5279b58009ce24cc968145dec7ffca14772b4012e6bea2d942` |
| 7 | es-en | 63.0 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `19c794484cf82f842771576ba6fd0956c2238df990d118a4443f689d0cdea478` |
| 8 | en-es | 63.0 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `1eb47c69259a11bc17002424005d26e8373bb24a3f9e369e6e04e80cc1030d33` |
| 9 | es-en | 63.0 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `256d1e745a68e85eb426dcc2fb228b6560be6a642788b133564c6584e6d7850c` |
| 10 | es-en | 63.0 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `5ded3e6283900430e002868140c53023d195b0fe744793aff1d4295c7a43e69a` |
| 11 | es-en | 63.0 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `e0f68e4648be9887751681b596579e36731553eccc353b109f4caf18037ccf36` |
| 12 | en-es | 60.8952 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `bf023613071ac367a39e967c2095f6127634094b336349f3e500e771750c5fea` |
| 13 | en-es | 59.4344 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `4cd2caded9340627fbe2682182013cedd66a5e24bb40132946e2cf1e49d078ea` |
| 14 | en-es | 59.25 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `30d948d7354677491dbad9e26fcd7b42b93954c163e3b2a577695e6986951129` |
| 15 | es-en | 58.5 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `1036c02802179be5e1faf35707e4bfd551073bbc3bd92b2f931f05949e631e0d` |
