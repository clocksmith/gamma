# Gamma agent instructions

**Prime Directive:** Preserve Gamma as a trustworthy workbench for inspecting,
comparing, measuring, and improving model or algorithm behavior under explicit
evidence contracts.

When working inside Deco, follow the [workspace operating rules](../AGENTS.md).
This file adds Gamma's build commands, code map and scientific constraints.
In a standalone clone, work directly from the requested outcome and relevant
implementation; the workspace link is optional.

## Component Intent

CATSCAN.md files record a component's owner, contracts and invariants. Look up
the one for the component you change when you need its contract; you don't
have to read the chain before editing. When code and a charter disagree, decide
which is right: fix the code if it broke the contract, or move the boundary and
update the charter in the same commit. Never rewrite a charter to excuse a
failure.

### Code and documentation map

- `README.md` describes the CLI; `EMOJI.md` records the Unicode convention.
- `docs/COMPONENT_INDEX.md` locates component owners and contracts.
- `gamma/engines/README.md` documents engine interfaces; `gamma/game/README.md`
  documents the token game. Consult the owner relevant to the change.
- These documents are searchable references, not a checklist before editing.

### Distillation Process Rules (critical)
Before any distillation run or checkpoint sweep:
- Resolve `PYTHON_BIN` (prefer `.venv/bin/python`); verify `torch` + `transformers` import.
- Print `torch.cuda.is_available()`, `torch.cuda.device_count()`, and target `DEVICE`.
- On ROCm, prove real GPU compute, not just visibility: a tiny CUDA matmul probe
  must succeed in the runtime mode you will train with before launch. On
  `HIP error: invalid device function`, retry with `HSA_OVERRIDE_GFX_VERSION=11.0.0`.
- Verify all train/eval pair files exist and match the intended input spec.
- If resuming, verify `resume_from` exists and is consistent with `resume_stage`.
- Fix any vocab/tokenizer mismatch that could break checkpoint loading first.

Known-good translation runtime: EN/ES `TranslateGemma-4B -> Gemma-3-1B` on
GPU/ROCm with `device=cuda` and `runtime_mode=rocm_gfx_override`.

Repair environment drift (`/usr/bin/python3` vs `.venv/bin/python`, missing
deps), ROCm invalid-device errors, resume-stage mismatches and provenance
confusion (`available rows` vs `rows used`, decode/eval mixups) before spending
compute on a run they invalidate. Continue independent implementation or
analysis while an unavailable resource blocks execution.

For every run/sweep, log one contract line:
```text
[run-contract] run_name=<name> pairs_input_spec=<path-or-spec> resume_from=<path|none> resume_stage=<stage|none> decode=<greedy|sampled> eval_dataset_paths=<comma-separated paths> device=<auto|cuda|cpu> schedule=<A_then_B|mixed_from_start> runtime_mode=<normal_rocm|rocm_gfx_override|cpu> sweep_mode=<live|after_train>
```

Before describing a run as active, verify current-stage metrics (e.g.
`stage_a/metrics.jsonl`) grow, logs show step lines and the device is doing
work. Report finished and failed runs as such. Recover a failed requested run
in a persistent session (`tmux`/`screen`/interactive PTY) after diagnosing the
failure and checking resource ownership and checkpoint consistency.

Keep translation distillation as two decoupled workflows: (1) training and
checkpoint-eval jobs append raw artifacts under each run directory; (2)
reporting rebuilds the normalized view from whatever artifacts exist,
backfilling older manifest-backed eval outputs into the current scoreboard
shape, and must be rerunnable and safe against partial or still-running jobs.

After each sweep or major eval batch, ensure `manifest.jsonl`, `scoreboard.md`,
`scoreboard_eval_rows.csv`, and `scoreboard_checkpoints.csv` exist and are
linked, then refresh the translation results bundle, which rebuilds the run
index internally (do not run the index builder separately first):
```bash
python3 projects/distillation/translation/pipeline/rebuild_translation_results_bundle.py
```
Rerun the bundle rebuild whenever new eval rows land; it is the canonical way
to fold fresh `compare_eval_summary.json` outputs into the leaderboards under `projects/distillation/translation/runs/results_bundle/`:
`leaderboard_all_compare_rows.csv`,
`leaderboard_external_wmt13_en_es_translation_benchmark_128.csv`,
`leaderboard_indomain_clean_merged_en_es_translation_benchmark_128.csv`, and
`leaderboard.md`.

### Intent-First Operations

- Treat Gamma intent as the named proof target for the active lane (token game, benchmark, distillation, compression); keep lanes separate unless the user explicitly bridges them.
- For compression work, anchor every run to the stated score target and dataset. Legal/memory gates are scaffolding unless they plausibly move the target metric.
- Do not kill an idea from global average lift when the user asks for conditional attribution; separate current implementation weakness from the concept being tested.
- Report distillation and other live jobs from the run contract, artifacts, checkpoints, scoreboards, process owners, logs, and GPU activity, never from a launched command alone. Base ETAs on measured counters (bytes, samples, log steps); state basis and uncertainty.
- If a reporting artifact is the source of truth, encode gaps and next commands inside it, not in chat prose.

### Key Paths
- `gamma/game/` - Game logic and UI
- `gamma/engines/` - Engine backends (llamacpp, pytorch, vllm, ollama)
- `gamma/mind_meld/` - Multi-model collaboration
- `gamma/benchmarks/` - Performance testing
- `gamma/comparison/` - Model comparison tools
- `apps/games/2038/` - Mandate 2038 spec, browser prototype, and simulation lab

### Guardrails
- Enforce `EMOJI.md`; use only approved Unicode symbols, no emojis
- Do not auto-install model weights; users provision models
- Maintain compatibility across all engine backends

### Development
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gamma.py game  # Run the game
```

### Development validation

- Verify the active CLI before relying on flags: `python gamma.py help <mode>`.
- Targeted tests by changed area:
  - Engine: `tests/test_engine_interface.py` and `tests/test_engine_factory.py`.
  - Game: `tests/test_game.py` and `tests/test_ui_components.py`.
  - Mind Meld: the matching `tests/test_mind_meld*.py` files.
- Python edits: `python -m py_compile gamma.py` (or the touched files) and import the changed package.
- Model downloads, remote providers, and compute jobs require user authority.
