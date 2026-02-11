# Checklist

## Pipeline

- [ ] Confirm base model is available locally (HF cache or local directory).
- [ ] Choose corpora per language (plain text, UTF-8).
- [ ] Generate hard-mode eval datasets with metadata (`meta.difficulty=hard`).
- [ ] Run tokenizer coverage report against base model tokenizer.
- [ ] Run keep-list generation (token frequency scan).
- [ ] Decide `top_k` per language (start at 50k; adjust after size/quality checks).
- [ ] Prune checkpoint weights and save to `safetensors`.
- [ ] Record outputs:
  - [ ] `kept_token_ids.json`
  - [ ] `id_remap.json`
  - [ ] `stats.json`
  - [ ] `prune_info.json` (if checkpoint written)
- [ ] Validate that the pruned checkpoint loads and the embedding layer shape matches the new vocab size.

## Quality / Safety

- [ ] Implement a runtime remap wrapper for evaluation (old ids -> new ids, fallback to `unk`).
- [ ] Smoke test with a small set of in-language queries.
- [ ] Measure retrieval quality delta on a small labeled set (if available).
- [ ] Check OOV rate for the target language (fraction of token ids mapped to fallback).
- [ ] Track quality retention vs base (`recall@1_subset / recall@1_base`, `mrr@10_subset / mrr@10_base`).
- [ ] Track speedup vs base (`subset_qps / base_qps`) and size-vs-quality frontier.

## Release

- [ ] Standardize naming scheme: `embeddinggemma-300m-<tag>-vocab<k>` (or similar).
- [ ] Generate per-subset model card (source model, corpus, top_k, remap note).
- [ ] Convert to RDRR later if needed (Doppler).
