# CATSCAN: Gamma Repository

Component: `gamma`

Parent: none

## Target

Provide an empirical workbench for model evaluation, translation distillation (`TranslateGemma-4B -> Gemma-3-1B`), SAME-R capability transfer, and multi-backend inference comparison under verifiable run contracts.

## Authority

- Owns model evaluation harnesses, distillation pipelines, training checkpoint evaluators, benchmark scoreboards, and simulation prototypes (`games/2038/`).
- Does not own production inference runtimes (Doppler), formal hardware attestation (Doe), or multi-agent rooms (Reploid).

## Scope

- Evaluation runners (`src/engines/`, `src/benchmarks/`, `src/comparison/`, `src/mind_meld/`).
- Distillation pipelines (`projects/distillation/translation/`, `projects/distillation/wgsl/`).
- Capability transfer (`projects/samer/`).
- Simulation lab (`games/2038/`, `src/game/`).

## Contracts

- Input: Hugging Face / GGUF / local model weights, training pairs, and evaluation datasets.
- Output: Standardized run contracts, `manifest.jsonl`, `scoreboard.md`, and normalized translation results bundles.

## Invariants

- Proven compute probe on ROCm/CUDA before launching training or eval sweeps.
- Every run logs an explicit `[run-contract]` line with dataset, schedule, and device spec.
- Reporting rebuilds are strictly decoupled from raw training/eval execution and safe against in-flight jobs.

## Acceptance

- Run index and results bundle rebuilds execute cleanly:
  - `python3 projects/distillation/translation/pipeline/build_run_index.py`
  - `python3 projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py`

## Non-goals

- Production JavaScript runtime packaging, cloud model hosting, or unverified marketing claims.

## Freedom

Any internal algorithm or model training recipe is permitted if it preserves declared run contracts and produces verified scoreboards.
