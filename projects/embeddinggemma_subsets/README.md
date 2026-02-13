# EmbeddingGemma Subsets: Unified Pipeline

This project now uses one resumable pipeline and one workspace layout for:
- raw data collection (`Wikipedia` + `Gemini`)
- merged corpus/dataset generation
- distillation pair generation
- subset distillation (single-language and mixed, e.g. `en-es`)
- repeated benchmarking with confidence intervals and charts

## Workspace Layout

Use one workspace root (example: `gamma/projects/embeddinggemma_subsets/workspaces/main`):

- `raw/wiki/<lang>.jsonl`
- `raw/gemini/<lang>.jsonl`
- `raw/merged/<lang>.jsonl`
- `corpora/<lang>.txt`
- `datasets/<lang>/dataset.json`
- `training/distill_pairs.jsonl`
- `models/distilled/...`
- `eval/benchmark/...`

## Scripts You Should Use

- `pipeline/run_pipeline.py`: orchestrates end-to-end steps and resume/skip logic.
- `data_tools/fetch_wikipedia_jsonl.py`: fetches capped Wikipedia JSONL (API mode for strict network control).
- `data_tools/generate_gemini_seed_jsonl.py`: generates multilingual seed text from Gemini, optionally seeded by wiki JSONL.
- `data_tools/make_wiki_corpus.py`: builds corpus text + retrieval dataset from merged JSONL.
- `training/make_distill_pairs.py`: creates distillation pairs from datasets.
- `training/distill_subset.py`: trains one subset student (supports `--langs en,es` etc).
- `eval/run_benchmark.py`: repeated eval/perf runs + CIs + charts.
- `eval/run_mteb_remap.py`: runs MTEB on subset/distilled checkpoints with id remapping.

## Prerequisites

```bash
source gamma/.venv/bin/activate
```

Set `GEMINI_API_KEY` in `~/.env` (or pass `--env-file` to Gemini script).

Base model path used below:

```bash
export BASE_MODEL=/Users/xyz/.cache/huggingface/hub/models--google--embeddinggemma-300m/snapshots/57c266a740f537b4dc058e1b0cda161fd15afa75
```

## End-to-End Commands (Real, Copy/Paste)

### 1) Initialize workspace

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps init \
  --from-scratch
```

### 2) Fetch small capped Wikipedia seed set

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps fetch \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --resume \
  --wiki-max-output-mb 8 \
  --wiki-max-rows 100 \
  --wiki-max-requests 80 \
  --wiki-batch-pages 20 \
  --wiki-min-chars 80 \
  --wiki-sleep-ms 80 \
  --wiki-retry-429-base-s 2 \
  --wiki-retry-429-max-s 30 \
  --wiki-max-consecutive-errors 12 \
  --wiki-api-source hybrid \
  --wiki-topic-buckets news,science,culture,law,health,finance,informal \
  --wiki-purity-mode basic \
  --wiki-purity-threshold 0.55 \
  --wiki-max-latin-ratio-nonlatin 0.35 \
  --wiki-priority-langs hi,ar,pt \
  --wiki-priority-multiplier 2.0
```

`fetch` now automatically applies:
- near-duplicate filtering
- boilerplate/disambiguation rejection
- topic-bucket balancing
- language-script purity filtering

### 3) Generate Gemini data seeded by wiki

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps gemini \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --resume \
  --gemini-model gemini-3-flash-preview \
  --gemini-rows-per-lang 1000 \
  --gemini-batch-size 50 \
  --gemini-min-chars 300 \
  --gemini-max-chars 1200 \
  --gemini-temperature 1.0 \
  --gemini-sleep-ms 250
```

### 4) Merge + build datasets + build distill pairs

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps merge,dataset,pairs \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --resume \
  --merge-max-rows 20000 \
  --merge-min-chars 120 \
  --max-paragraphs 300000 \
  --max-docs 5000 \
  --max-queries 5000 \
  --keywords-per-query 14 \
  --distractors-per-query 30 \
  --pairs-per-lang 10000 \
  --pairs-neg-strategy lexical_hard \
  --pairs-hard-neg-pool 128
```

## Build Subset Checkpoints (Required Before Distill)

### A) Standard single-language subsets (batch from config)

```bash
gamma/.venv/bin/python gamma/tools/build_embeddinggemma_subsets.py \
  --config gamma/projects/embeddinggemma_subsets/config/subsets.json
```

### B) Mixed subset example (`en-es`)

```bash
gamma/.venv/bin/python gamma/tools/vocab_subset.py \
  --model "$BASE_MODEL" \
  --text gamma/projects/embeddinggemma_subsets/workspaces/main/corpora/en.txt \
  --text gamma/projects/embeddinggemma_subsets/workspaces/main/corpora/es.txt \
  --top-k 50000 \
  --min-count 2 \
  --fill-to-top-k \
  --fill-strategy spm_score \
  --out gamma/projects/embeddinggemma_subsets/output/google__embeddinggemma-300m-en-es-vocab50000 \
  --write-checkpoint
```

## Distill Students

### Single-language distill targets

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps distill \
  --base-model "$BASE_MODEL" \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --subset-root gamma/projects/embeddinggemma_subsets/output \
  --resume \
  --distill-device cpu \
  --distill-steps 600 \
  --distill-batch-size 32 \
  --distill-max-length 96 \
  --distill-lr 2e-5 \
  --distill-alpha-triplet 0.25 \
  --distill-triplet-margin 0.05 \
  --distill-alpha-sim-distill 0.25
```

### Mixed distill target example (`en-es`)

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps distill \
  --base-model "$BASE_MODEL" \
  --distill-targets en-es \
  --subset-root gamma/projects/embeddinggemma_subsets/output \
  --resume \
  --distill-device cpu \
  --distill-steps 600 \
  --distill-batch-size 32 \
  --distill-max-length 96 \
  --distill-lr 2e-5
```

## Benchmark + Visualize

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps benchmark \
  --base-model "$BASE_MODEL" \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --distill-out-root gamma/projects/embeddinggemma_subsets/workspaces/main/models/distilled \
  --benchmark-device cpu \
  --benchmark-repeats 5 \
  --benchmark-max-length 96 \
  --benchmark-batch-size 64 \
  --benchmark-iters 3 \
  --benchmark-warmup 1
```

Outputs:
- `workspaces/main/eval/benchmark/benchmark_summary.json`
- `workspaces/main/eval/benchmark/charts/benchmark_recall1_retention_ci.png`
- `workspaces/main/eval/benchmark/charts/benchmark_speedup_ci.png`
- `workspaces/main/eval/benchmark/charts/benchmark_prefill_ci.png`
- `workspaces/main/eval/benchmark/charts/benchmark_vram_ci.png`

## Resume and Independent Steps

- Re-run safely with `--resume`; completed outputs are skipped.
- Run only what you need via `--steps`.
- If wiki was already collected elsewhere, copy files into:
  - `workspaces/main/raw/wiki/<lang>.jsonl`
  then run from `gemini` onward.

Example (skip fetch):

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/embeddinggemma_subsets/workspaces/main \
  --steps gemini,merge,dataset,pairs \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --resume
```

## Notes

- `raw` is JSONL source data for generation/merging.
- `corpora` is line-based text used for vocab subsetting.
- `datasets` is retrieval eval/training structure (`queries/docs/relevant`).
- Distillation needs an existing subset checkpoint directory (`id_remap.json` + model files).
- Mixed models (`en-es`, `fr-pt`, etc.) are supported by creating matching mixed subset dirs and using `--distill-targets`.
- For stronger EN quality, prefer `--pairs-neg-strategy lexical_hard` and keep triplet/sim-distill weights non-zero.

## Public Benchmarks (MTEB / BEIR)

For publishable external comparisons, run MTEB (primary) and optionally BEIR.

Install benchmark deps:

```bash
source gamma/.venv/bin/activate
pip install -U mteb sentence-transformers beir
```

Minimal MTEB retrieval run (English first, then expand):

```bash
gamma/.venv/bin/python gamma/projects/embeddinggemma_subsets/eval/run_mteb_remap.py \
  --base-tokenizer /Users/xyz/.cache/huggingface/hub/models--google--embeddinggemma-300m/snapshots/57c266a740f537b4dc058e1b0cda161fd15afa75 \
  --subset-dir gamma/projects/embeddinggemma_subsets/data/models/distilled/google__embeddinggemma-300m-en-vocab50000-distilled \
  --task-types Retrieval \
  --task-langs eng \
  --output-folder gamma/projects/embeddinggemma_subsets/data/eval/mteb_en
```

Then run multilingual retrieval tasks by changing `task_langs` (for example: `eng,spa,fra,por,ara,hin,jpn,zho`) and repeating per distilled checkpoint.

Important: distilled/subset checkpoints are pruned-vocab models, so direct `SentenceTransformer(<subset_dir>)` loading is unsafe unless ids are remapped with `id_remap.json`.

References:
- MTEB: https://github.com/embeddings-benchmark/mteb
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- BEIR: https://github.com/beir-cellar/beir
