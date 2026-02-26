# EmbeddingGemma Subsets: Unified Pipeline

This project now uses one resumable pipeline and one workspace layout for:
- raw data collection (`Wikipedia` + `Gemini`)
- merged corpus/dataset generation
- distillation pair generation
- subset distillation (single-language and mixed, e.g. `en-es`)
- repeated benchmarking with confidence intervals and charts

## Workspace Layout

Use one workspace root (example: `gamma/projects/distillation/embedding/workspaces/main`):

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
- `translation/training/make_translate_distill_pairs.py`: creates translation triplets (`source`, `target_pos`, `target_neg`) for multilingual-to-few-language distillation.
- `translation/training/run_translation_distill.sh`: end-to-end translation distill wrapper (build -> split -> train -> eval).
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
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
  --steps init \
  --from-scratch
```

### 2) Fetch small capped Wikipedia seed set

```bash
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
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
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
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
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
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

### 4b) Build translation distill triplets (optional)

Use this when distilling multilingual supervision into a smaller target-language set (for example, many source languages into `en,es`):

```bash
gamma/.venv/bin/python gamma/projects/distillation/translation/training/make_translate_distill_pairs.py \
  --pair-file fr en /path/to/fr.txt /path/to/en_from_fr.txt \
  --pair-file de en /path/to/de.txt /path/to/en_from_de.txt \
  --pair-file fr es /path/to/fr.txt /path/to/es_from_fr.txt \
  --pair-file de es /path/to/de.txt /path/to/es_from_de.txt \
  --target-langs en,es \
  --pairs-per-pair 20000 \
  --neg-strategy lexical_hard \
  --out gamma/projects/distillation/embedding/workspaces/main/training/translate_distill_pairs.jsonl
```

### 5) Train translation distillation (new)

Train TranslateGemma student with optional KD + triplet:

```bash
gamma/.venv/bin/python gamma/projects/distillation/translation/training/train_translate_distill.py \
  --pairs gamma/projects/distillation/embedding/workspaces/main/training/translate_distill_pairs.jsonl \
  --teacher-model google/translategemma-4b-it \
  --student-model google/translategemma-4b-it \
  --target-langs en,es \
  --source-langs fr,de,it,pt,ar,hi,ja,zh \
  --schedule A_then_B \
  --total-steps 1000 \
  --sft-steps 500 \
  --batch-size 1 \
  --lambda-kd 0.5 \
  --mu-triplet 0.1 \
  --margin 0.2 \
  --enable-lora \
  --lora-rank 16 \
  --out-root projects/distillation/translation/runs/exp01 \
  --run-name default \
  --summary-out projects/distillation/translation/runs/exp01/default/train_summary.json
```

For one-stage distillation from step 1, use `--schedule mixed_from_start`.

### 6) End-to-end translation pipeline with train/eval

Use this wrapper to go from `bitext` -> triplets -> train/eval split -> train -> teacher benchmark:

```bash
SCHEDULE=A_then_B
SOURCE_LANGS="fr,de,it,pt,ar,hi,ja,zh"
TARGET_LANGS="en,es"
PAIRS_PER_PAIR=2000
TOTAL_STEPS=20000
SFT_STEPS=10000
BATCH_SIZE=1
LR=2e-5
LAMBDA_KD=0.5
MU_TRIPLET=0.1
MARGIN=0.2
LORA_RANK=16
LORA_ALPHA=32
DEVICE=cuda
TEACHER_MODEL=google/translategemma-4b-it
STUDENT_MODEL=google/translategemma-4b-it
OUT_ROOT=projects/distillation/translation/runs/exp01
RUN_NAME=exp01
SPLIT_PAIRS=1
EVAL_ENABLED=1
EVAL_BLEU=1
EVAL_CHRF=1
EVAL_COMET=0
ALLOW_DOWNLOAD=1
DRY_RUN=0

bash gamma/projects/distillation/translation/training/run_translation_distill.sh "$SCHEDULE"
```

The command writes:
- train split: `projects/distillation/translation/training_data/translate_distill_pairs.train.jsonl`
- eval split: `projects/distillation/translation/training_data/translate_distill_pairs.eval.jsonl`
- checkpoints and training metrics: `projects/distillation/translation/runs/exp01/exp01`
- benchmark outputs: `projects/distillation/translation/runs/exp01/exp01/eval`

## Build Subset Checkpoints (Required Before Distill)

### A) Standard single-language subsets (batch from config)

```bash
gamma/.venv/bin/python gamma/tools/build_embeddinggemma_subsets.py \
  --config gamma/projects/distillation/shared/config/subsets.json
```

### B) Mixed subset example (`en-es`)

```bash
gamma/.venv/bin/python gamma/tools/vocab_subset.py \
  --model "$BASE_MODEL" \
  --text gamma/projects/distillation/embedding/workspaces/main/corpora/en.txt \
  --text gamma/projects/distillation/embedding/workspaces/main/corpora/es.txt \
  --top-k 50000 \
  --min-count 2 \
  --fill-to-top-k \
  --fill-strategy spm_score \
  --out gamma/projects/distillation/embedding/output/google__embeddinggemma-300m-en-es-vocab50000 \
  --write-checkpoint
```

## Distill Students

### Single-language distill targets

```bash
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
  --steps distill \
  --base-model "$BASE_MODEL" \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --subset-root gamma/projects/distillation/embedding/output \
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
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
  --steps distill \
  --base-model "$BASE_MODEL" \
  --distill-targets en-es \
  --subset-root gamma/projects/distillation/embedding/output \
  --resume \
  --distill-device cpu \
  --distill-steps 600 \
  --distill-batch-size 32 \
  --distill-max-length 96 \
  --distill-lr 2e-5
```

## Benchmark + Visualize

```bash
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
  --steps benchmark \
  --base-model "$BASE_MODEL" \
  --langs en,es,zh,ja,ar,fr,pt,hi \
  --distill-out-root gamma/projects/distillation/embedding/workspaces/main/models/distilled \
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
gamma/.venv/bin/python gamma/projects/distillation/embedding/pipeline/run_pipeline.py \
  --workspace-dir gamma/projects/distillation/embedding/workspaces/main \
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
gamma/.venv/bin/python gamma/projects/distillation/embedding/eval/run_mteb_remap.py \
  --base-tokenizer /Users/xyz/.cache/huggingface/hub/models--google--embeddinggemma-300m/snapshots/57c266a740f537b4dc058e1b0cda161fd15afa75 \
  --subset-dir gamma/projects/distillation/embedding/data/models/distilled/google__embeddinggemma-300m-en-vocab50000-distilled \
  --task-types Retrieval \
  --task-langs eng \
  --output-folder gamma/projects/distillation/embedding/data/eval/mteb_en
```

Then run multilingual retrieval tasks by changing `task_langs` (for example: `eng,spa,fra,por,ara,hin,jpn,zho`) and repeating per distilled checkpoint.

Important: distilled/subset checkpoints are pruned-vocab models, so direct `SentenceTransformer(<subset_dir>)` loading is unsafe unless ids are remapped with `id_remap.json`.

References:
- MTEB: https://github.com/embeddings-benchmark/mteb
- MTEB Leaderboard: https://huggingface.co/spaces/mteb/leaderboard
- BEIR: https://github.com/beir-cellar/beir
