# Distillation Path Migration Map

## Code moved to new namespace

- `projects/embeddinggemma_subsets/pipeline/run_pipeline.py`
  -> `projects/distillation/embedding/pipeline/run_pipeline.py`
- `projects/embeddinggemma_subsets/training/run_distill_batch.py`
  -> `projects/distillation/embedding/training/run_distill_batch.py`
- `projects/embeddinggemma_subsets/training/distill_subset.py`
  -> `projects/distillation/embedding/training/distill_subset.py`
- `projects/embeddinggemma_subsets/training/make_distill_pairs.py`
  -> `projects/distillation/embedding/training/make_distill_pairs.py`
- `projects/embeddinggemma_subsets/training/make_translate_distill_pairs.py`
  -> `projects/distillation/translation/training/make_translate_distill_pairs.py`
- `projects/embeddinggemma_subsets/training/split_translate_distill_pairs.py`
  -> `projects/distillation/translation/training/split_translate_distill_pairs.py`
- `projects/embeddinggemma_subsets/training/train_translate_distill.py`
  -> `projects/distillation/translation/training/train_translate_distill.py`
- `projects/embeddinggemma_subsets/training/run_translate_distill_eval.py`
  -> `projects/distillation/translation/eval/run_translate_distill_eval.py`
- `projects/embeddinggemma_subsets/eval/run_benchmark.py`
  -> `projects/distillation/embedding/eval/run_benchmark.py`
- `projects/embeddinggemma_subsets/eval/run_eval.py`
  -> `projects/distillation/embedding/eval/run_eval.py`
- `projects/embeddinggemma_subsets/eval/run_mteb_remap.py`
  -> `projects/distillation/embedding/eval/run_mteb_remap.py`

## Shared tooling moved to new namespace

- `projects/embeddinggemma_subsets/data_tools/fetch_wikipedia_jsonl.py`
  -> `projects/distillation/shared/data_tools/fetch_wikipedia_jsonl.py`
- `projects/embeddinggemma_subsets/data_tools/generate_gemini_seed_jsonl.py`
  -> `projects/distillation/shared/data_tools/generate_gemini_seed_jsonl.py`
- `projects/embeddinggemma_subsets/data_tools/make_synthetic_hard_datasets.py`
  -> `projects/distillation/shared/data_tools/make_synthetic_hard_datasets.py`
- `projects/embeddinggemma_subsets/data_tools/make_wiki_corpus.py`
  -> `projects/distillation/shared/data_tools/make_wiki_corpus.py`
- `projects/embeddinggemma_subsets/data_tools/tokenizer_coverage_report.py`
  -> `projects/distillation/shared/data_tools/tokenizer_coverage_report.py`
- `projects/embeddinggemma_subsets/data_tools/writing_profiles.json`
  -> `projects/distillation/shared/data_tools/writing_profiles.json`
- `projects/embeddinggemma_subsets/config/subsets.json`
  -> `projects/distillation/shared/config/subsets.json`

## Compatibility layer kept in legacy path

- Updated legacy entrypoints remain in `projects/embeddinggemma_subsets/*` and
  delegate to new paths with deprecation warnings.
- `projects/embeddinggemma_subsets/README.md` now points users to
  `projects/distillation/embedding/README.md` and notes compatibility behavior.
