# EmbeddingGemma Subsets

Goal: build a repeatable pipeline to create smaller, language-targeted subsets of a large-vocab embedding model (starting with `google/embeddinggemma-300m`) by:

1. Selecting a keep-list of token IDs based on a language corpus.
2. Pruning vocab-dependent weights (at minimum: input embeddings).
3. Emitting an `old_id -> new_id` remap that must be applied at runtime.

This is primarily about disk/RAM footprint. For embedding/pooling models, runtime speed typically does not scale with vocab size (gather cost depends on sequence length, not vocab size), but smaller checkpoints can still matter a lot for on-device distribution.

## Layout

- `config/subsets.json`: batch config (model, output root, language subsets).
- `data/`: put your corpora here (one or more text files per language).
- `output/`: generated keep-lists, remaps, and pruned checkpoints.

## Prereqs

Use the repo venv:

```bash
source gamma/.venv/bin/activate
```

You must have the base model + tokenizer available locally (HF cache or a local path). This environment currently cannot fetch from Hugging Face, so plan to pre-seed the cache or point `--model` at a local directory containing the model files.

If you do have network access on a machine, one workable approach is:

```bash
huggingface-cli download google/embeddinggemma-300m \
  --local-dir /path/to/embeddinggemma-300m \
  --local-dir-use-symlinks False
```

Then run this pipeline with `--model /path/to/embeddinggemma-300m`.

## Batch Run

```bash
gamma/.venv/bin/python gamma/tools/build_embeddinggemma_subsets.py \
  --config gamma/projects/embeddinggemma_subsets/config/subsets.json
```

This drives `gamma/tools/vocab_subset.py` for each subset and writes per-subset artifacts to `output/`.

## Tests (Static Docs)

These tests compare base-model retrieval behavior vs a subset model on a small static multilingual document set.

```bash
# Base-only sanity (subset tests will be skipped)
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/tests/test_subset_embeddings.py

# Compare against a specific subset model dir (single-language subsets should pass subset_langs automatically)
EMBEDDINGGEMMA_SUBSET_DIR=gamma/projects/embeddinggemma_subsets/output/google__embeddinggemma-300m-en-vocab50000 \
  gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/tests/test_subset_embeddings.py
```

## Eval (Metrics + Charts)

This generates:
- retrieval metrics: Recall@K, MRR@K, nDCG@K
- subset health metrics: OOV rate (token remap fallback-to-unk)
- base-vs-subset consistency: cosine distributions for docs/queries
- divergence: KL/JS over per-query similarity distributions (softmax over docs)
- optional PNG charts

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/eval/run_eval.py \
  --subset-dir gamma/projects/embeddinggemma_subsets/output/google__embeddinggemma-300m-en-vocab50000 \
  --bench-iters 25 --bench-warmup 5 \
  --charts
```

## Single Run (English)

```bash
gamma/.venv/bin/python gamma/tools/vocab_subset.py \
  --model google/embeddinggemma-300m \
  --text gamma/projects/embeddinggemma_subsets/data/en.txt \
  --top-k 50000 \
  --out gamma/projects/embeddinggemma_subsets/output/embeddinggemma-300m-en \
  --write-checkpoint
```

## Runtime Reminder (Critical)

A pruned checkpoint is not directly compatible with the original tokenizer IDs.

You must remap token IDs:

- If token id exists in `id_remap.json.old_to_new`: use it.
- Else: map to `unk` (or another safe fallback).

Artifacts are emitted into each output folder, including `README_SUBSET.txt` with a concrete reminder.

## Suggested Release Order

The pipeline supports single-language subsets and “regional bundles” (multiple corpora inputs; a union keep-list).

Suggested order for shaking out edge cases:

1. `en`
2. `es`
3. `ja`
4. `ar`
5. `en-es` (bundle)
