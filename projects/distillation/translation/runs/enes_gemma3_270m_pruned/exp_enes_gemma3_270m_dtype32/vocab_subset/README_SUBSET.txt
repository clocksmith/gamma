This directory contains a pruned HF checkpoint with a reduced vocab-dependent embedding table.

Important:
- The original tokenizer still emits the original token IDs.
- You MUST remap input_ids using id_remap.json before calling the model, or map unknown IDs to unk.

Files:
- kept_token_ids.json: original token IDs retained, in new-vocab order
- id_remap.json: old_to_new and new_to_old mappings
- stats.json: corpus scan summary
- prune_info.json: embedding shapes and pruning details

Typical runtime flow:
1) Load the base tokenizer from the original model id
2) Tokenize English text (base tokenizer) -> input_ids (original ids)
3) Remap ids: old_id -> new_id, else fallback to unk_id
4) Feed remapped input_ids to this pruned model

