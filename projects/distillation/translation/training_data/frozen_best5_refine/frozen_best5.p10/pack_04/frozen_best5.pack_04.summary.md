# Frozen Best-5 Pack 04 Audit

- run_root: `projects/distillation/translation/runs/translategemma4b_es_en_gemma3_1b_stagea_goldgrid_rows1600_bf16_confirm_best5`
- target_pack: `04`
- prune_fraction: `0.1`
- rows_in_pack: `320`
- rows_to_remove: `{'en-es': 16, 'es-en': 16}`
- audit_csv: `projects/distillation/translation/training_data/frozen_best5_refine/frozen_best5.p10/pack_04/frozen_best5.pack_04.audit.csv`

## Top Prune Candidates

| rank | pair | prune_score | source_file | row_id |
| --- | --- | --- | --- | --- |
| 1 | en-es | 31.711 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `70c585dca638f188e9447d5b8bc56003eaaba7cf75a70a3713ce18eb198cd298` |
| 2 | en-es | 31.711 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `7f838301925c4d7b0f3979c94b6e1c19ea082aa92cf0ef9a7629df6b4c6b1d5f` |
| 3 | en-es | 31.711 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `95879dd2c718769ba4474981d1ece428b9d07df665f3b426a08aa10b498cd97a` |
| 4 | en-es | 31.711 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `9840c0ea58062031cea5994db080f9a962b100755cc80e148b0bdb5ff989087e` |
| 5 | en-es | 31.711 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `a280da3eec02da4895e8789e15e846a8f4386078721380904757b433fa74d395` |
| 6 | en-es | 31.711 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `fd28d189d447ab31257142968f44efca991460e1c1da7ab0ba81d6be75544c59` |
| 7 | en-es | 31.6844 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `30b784626e067828f1110bae72d713c26a3ccf49b0cf4ff4be7146c5da8846ee` |
| 8 | en-es | 31.6844 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `56c1c019aabe75a459a05719d5a07d7fb0496ef29bbd3def023b8400f568465d` |
| 9 | en-es | 31.6844 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `a7320af4b0d69fe2a3ec2aa8cfd4b7fe0a7688b878b3452db2bb7675739a9cbd` |
| 10 | en-es | 31.6786 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `acdeef1dba4a89346214dddf1731f6dc2c022e91ff25cb5854f800c141c8324c` |
| 11 | en-es | 31.6786 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `d67e5cf25e55fad2e7bbe0bc0434b3cb1e91a300c0a43d159cbee5ba0606f977` |
| 12 | en-es | 31.5922 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `03e25690bbc2bbf07f1e1606483039675d5b17aa6ba28d9b3acc584cc2e223e8` |
| 13 | en-es | 31.5922 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `21a813e4614cc97b6fcf6d7ac9021a745d06614a827d97ede0dc20144cc670cc` |
| 14 | en-es | 31.5922 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_01_gold_core_a.jsonl` | `4063af75ba31ac7cea9ab917d00d6408b95bef8d5d7026bed3875d9fe611cd75` |
| 15 | en-es | 31.5893 | `projects/distillation/translation/training_data/gold_shards/gold_quality_4x640.shard_02_gold_core_b.jsonl` | `1a889e5c67a60a370eb600fc2e68305bbf5dd28ed6c8bb718530bd0cb86e6d4a` |
