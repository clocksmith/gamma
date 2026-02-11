# Checklist

## Pipeline

- [ ] Confirm base model is available locally (HF cache or local directory).
- [ ] Choose corpora per language (plain text, UTF-8).
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

## Release

- [ ] Standardize naming scheme: `embeddinggemma-300m-<tag>-vocab<k>` (or similar).
- [ ] Generate per-subset model card (source model, corpus, top_k, remap note).
- [ ] Convert to RDRR later if needed (Doppler).

