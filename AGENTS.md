## Code Agent

**Prime Directive:** Write Python code for the token-prediction game and LLM benchmarking tools.

### Before Starting
- Read `README.md` for features and usage
- Read `EMOJI.md` for approved Unicode symbols
- Check engine docs in `src/engines/README.md`
- Check game docs in `src/game/README.md`

### Distillation Process Rules (critical)
Before any distillation run or checkpoint sweep:
- Resolve `PYTHON_BIN` (prefer `.venv/bin/python`), and verify `torch` + `transformers` import.
- Print runtime visibility: `torch.cuda.is_available()`, `torch.cuda.device_count()`, target `DEVICE`.
- On ROCm, prove real GPU compute before launch (not just visibility) with a tiny CUDA matmul probe.
  - If probe fails with `HIP error: invalid device function`, retry probe with `HSA_OVERRIDE_GFX_VERSION=11.0.0`.
  - Do not launch until the compute probe succeeds in the same runtime mode you will train with.
- Verify all train/eval pair files exist and match intended input spec.
- If resuming, verify `resume_from` exists and is consistent with `resume_stage`.
- If checkpoint loading can fail from vocab/tokenizer mismatch, stop and fix before launch.

Known-good translation runtime:
- The EN/ES `TranslateGemma-4B -> Gemma-3-1B` line has been confirmed on GPU/ROCm with `device=cuda` and `runtime_mode=rocm_gfx_override`.

Block immediately on these failure classes:
- Environment drift (`/usr/bin/python3` vs `.venv/bin/python` / missing deps).
- ROCm invalid-device errors (`HIP error: invalid device function`).
- Resume-stage mismatch (wrong checkpoint/state continuation).
- Provenance confusion (`available rows` vs `rows used`, decode/eval mixups).

For every run/sweep, log one contract line:
```text
[run-contract] run_name=<name> pairs_input_spec=<path-or-spec> resume_from=<path|none> resume_stage=<stage|none> decode=<greedy|sampled> eval_dataset_paths=<comma-separated paths> device=<auto|cuda|cpu> schedule=<A_then_B|mixed_from_start> runtime_mode=<normal_rocm|rocm_gfx_override|cpu> sweep_mode=<live|after_train>
```

After launch, verify the run is truly active before handoff:
- `stage_a/metrics.jsonl` (or current stage metrics) exists and grows.
- Training log shows step lines (example: `[A_then_B_stage_a] step=20 ...`).
- `rocm-smi` shows elevated GPU use during active steps.
- If detached `nohup` jobs die in your environment, relaunch in a persistent session (`tmux`/`screen`/interactive PTY).

Treat translation distillation as two separate continuous workflows:
- Workflow 1: launch or resume training/checkpoint-eval jobs that append raw artifacts under each run directory.
- Workflow 2: rebuild the normalized reporting view from whatever artifacts currently exist, including backfill or migration of older manifest-backed eval outputs into the current scoreboard shape.
- Keep these workflows decoupled: reporting rebuilds must be rerunnable and safe against partial or still-running jobs.

After each sweep or major eval batch, ensure these artifacts exist and are linked:
- `manifest.jsonl`
- `scoreboard.md`
- `scoreboard_eval_rows.csv`
- `scoreboard_checkpoints.csv`
- refreshed run index via:
```bash
python3 projects/distillation/translation/pipeline/build_run_index.py
```
- cohesive translation results bundle via:
```bash
python3 projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py
```
- rerun the rebuild after new eval rows land; it is the canonical way to fold fresh `compare_eval_summary.json` outputs into the normalized reporting view and leaderboard files under `projects/distillation/translation/runs/results_bundle/`
- expect the rebuild to refresh:
  - `leaderboard_all_compare_rows.csv`
  - `leaderboard_external_wmt13_en_es_translation_benchmark_128.csv`
  - `leaderboard_indomain_clean_merged_en_es_translation_benchmark_128.csv`
  - `leaderboard.md`

### Intent-First Operations

- Treat Gamma intent as the named proof target for the active lane: token game, benchmark, distillation, or compression.
- For compression work, anchor every run to the stated score target and dataset. Legal/memory gates are scaffolding unless they plausibly move the target metric.
- Do not kill an idea from global average lift when the user is asking for conditional attribution. Separate current implementation weakness from the concept being tested.
- For distillation, answer from the run contract, artifacts, checkpoints, scoreboards, and GPU/process state; do not infer active progress from a launched command alone.
- Before reporting live jobs, inspect process owners, logs, output files, and GPU activity.
- If a reporting artifact is the source of truth, encode gaps and next commands inside that artifact instead of hiding them in chat prose.
- Keep compression, distillation, token-game, and benchmark contexts separate unless the user explicitly bridges them.

### Key Paths
- `src/game/` - Game logic and UI
- `src/engines/` - Engine backends (llamacpp, pytorch, vllm, ollama)
- `src/mind_meld/` - Multi-model collaboration
- `src/benchmarks/` - Performance testing
- `src/comparison/` - Model comparison tools
- `games/frontier-2038/` - M3T4 2038 game specification, browser prototype, and simulation lab


### Guardrails
- Enforce `EMOJI.md`; use only approved Unicode symbols, no emojis
- Do not auto-install model weights; users provision models
- Maintain compatibility across all engine backends
- Run tests before committing engine changes

### Development
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python gamma.py game  # Run the game
```

## No engineering-work time estimates

- Do not estimate how long coding, debugging, refactoring, documentation,
  research, cleanup, or other engineering work will take in hours, days, weeks,
  or other time units in code, comments, commit messages, status updates,
  receipts, or chat replies.
- Do not use duration phrases such as "~30 min", "~2 hr", "multi-day",
  "quick", or "long-running" as size proxies for engineering work.
- For engineering scope, describe what the work is: the file to change, the
  function to add, the schema field to extend, the named blocker to fix, or the
  concrete deltas such as files, symbols, and receipts touched.
- This restriction does not apply to already-running processes, benchmark
  jobs, training runs, compression gates, downloads, or other live operations
  with observable counters. For those, provide runtime/finish estimates when
  useful, based on measured progress such as bytes, blocks, samples, log steps,
  subprocess stage, or repeated timestamps. State the basis and uncertainty
  when progress is nonlinear or stage-dependent.

## Pick the real fix

- when you find a correctness bug, the default is to fix it, not to relabel it
- do not use effort or scope framing ("non-trivial", "real engineering effort", "worth its own thread", "we'll address later") as cover for choosing a lesser fix
- do not propose "mark experimental", "add a TODO", or "rewrite the misleading comment" as a substitute for the actual engineering work when the underlying behavior is wrong
- if scope genuinely must be split, describe the concrete deltas and ask the user which path to take, do not pre-decide a smaller version
