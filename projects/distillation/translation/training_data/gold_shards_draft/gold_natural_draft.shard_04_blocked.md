# Shard 04 Blocked

The current `shard_04` replacement is blocked for training use as a full 640-row shard.

Reasons:

- current high-quality human + mined pools do not contain enough unique rows to make a full fourth shard
- the remaining review queue is dominated by synthetic number-swap families
- forcing `640` rows would reintroduce the exact templated patterns we are trying to remove

Best available partial shard:

- `projects/distillation/translation/training_data/gold_shards_draft/gold_natural_draft.shard_04_seed_plus_manual.jsonl`
- rows: `112`

Recommended action:

- train on the recommended `1920` set for now
- extend shard 04 with newly authored or rewritten rows before promoting a `2560` set
