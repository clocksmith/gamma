## Code Agent

**Prime Directive:** Preserve Gamma as a trustworthy workbench for inspecting,
comparing, measuring, and improving model or algorithm behavior under explicit
evidence contracts.

## Build boldly

Understand → inspect → build → run → diagnose → improve → deliver.

- Start from the requested outcome and the existing implementation. Read the
  relevant code, and compare with working alternatives, before guessing.
- Make the most direct substantive change. Large refactors, replacement
  implementations, aggressive prototypes and speculative ideas are allowed when
  they serve the goal.
- Run the changed system early. Fix the failures you cause; don't stop at a
  plan, scaffold or failing test.
- If the result misses the goal, find the reason in the code and behavior,
  change it and repeat. Sweep parameters only to answer a real question. When a
  strategy is clearly failing, try a materially different one.
- Make routine design and implementation choices yourself. Ask only for a
  consequential product choice, access you lack, or a blocker you can't
  resolve safely.
- Commit coherent, tested progress often, and keep going while the requested
  outcome is unfinished.
- Done means the requested behavior works and was exercised against a
  real-world or competitive baseline. A passing unit test, receipt, report,
  scaffold or milestone is not completion.
- GOALS, INTENT, CATSCAN and charters are references to look up, not reading
  required before editing.
- Report results: what changed, the evidence, what remains, and blockers only
  when they need the owner or unavailable access. No completion percentages.

## Git workflow: direct to main

- Commit on the owning repo's `main` and push to `origin/main`. No feature
  branches, branch-backed worktrees, or PRs unless the user asks for them.
- On another branch, preserve its work and move the task to `main` safely;
  never discard changes to switch. Never force-push `main`.
- Stage only task-related changes; integrate remote updates without
  overwriting unrelated work.
- Report the pushed commit or the concrete blocker. A local commit is not a push.

## Development verification

- During development, choose checks for the changed behavior: syntax/type checks,
  existing focused tests, or a local visual check. A command list is not a requirement
  to run every suite before each commit, push, or ordinary application deployment.
- Do not automatically run full repository suites, broad browser/device matrices,
  GPU/model campaigns, benchmarks, or full release qualification. Run them when
  explicitly requested or when a named correctness question cannot be answered by
  focused checks; state that reason before starting.
- Config-contract, mirror, drift, and freshness checks run only when the change
  edits what they check. Don't add tests that just restate another file or pin
  config literals. Time-box long processes.
- Once relevant checks pass, continue. Repeat or broaden verification only after
  another relevant change, a failure, or a concrete unresolved concern.
- For documentation-only edits, inspect the diff and changed links. Do not run
  application, GPU, browser, or benchmark suites for prose changes.
- For ordinary deployments, build the changed artifact where needed and check the
  affected route after deployment. Deployment alone does not require a new release
  qualification campaign.
- Keep existing acceptance thresholds and release-qualification requirements.
  Report exactly what was checked; focused development checks do not establish
  numerical qualification, performance, multi-device support, or full acceptance.

## Component Intent

CATSCAN.md files record a component's owner, contracts and invariants. Look up
the one for the component you change when you need its contract; you don't
have to read the chain before editing. When code and a charter disagree, decide
which is right: fix the code if it broke the contract, or move the boundary and
update the charter in the same commit. Never rewrite a charter to excuse a
failure.

### Before Starting
- Read `README.md` and `EMOJI.md` for repository intent and style.
- Use `docs/COMPONENT_INDEX.md` to find the affected owner when you need it.
- Read `src/engines/README.md` when changing engines or their interfaces, and
  `src/game/README.md` when changing the game or its interfaces. Unrelated
  project work does not require either owner README.

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

Block immediately on environment drift (`/usr/bin/python3` vs
`.venv/bin/python`, missing deps), ROCm invalid-device errors, resume-stage
mismatch, or provenance confusion (`available rows` vs `rows used`,
decode/eval mixups).

For every run/sweep, log one contract line:
```text
[run-contract] run_name=<name> pairs_input_spec=<path-or-spec> resume_from=<path|none> resume_stage=<stage|none> decode=<greedy|sampled> eval_dataset_paths=<comma-separated paths> device=<auto|cuda|cpu> schedule=<A_then_B|mixed_from_start> runtime_mode=<normal_rocm|rocm_gfx_override|cpu> sweep_mode=<live|after_train>
```

Before handoff, verify the run is active: current-stage
metrics (e.g. `stage_a/metrics.jsonl`) exist and grow, the log shows step lines
(`[A_then_B_stage_a] step=20 ...`), and `rocm-smi` shows elevated GPU use. If
detached `nohup` jobs die, relaunch in a persistent session
(`tmux`/`screen`/interactive PTY).

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
- `src/game/` - Game logic and UI
- `src/engines/` - Engine backends (llamacpp, pytorch, vllm, ollama)
- `src/mind_meld/` - Multi-model collaboration
- `src/benchmarks/` - Performance testing
- `src/comparison/` - Model comparison tools
- `games/2038/` - Mandate 2038 spec, browser prototype, and simulation lab

### Guardrails
- Enforce `EMOJI.md`; use only approved Unicode symbols, no emojis
- Do not auto-install model weights; users provision models
- Maintain compatibility across all engine backends

### Development
```bash
python3 -m venv venv
source venv/bin/activate
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

## No speculative engineering timelines

- Never predict how long engineering work will take ("1-2 weeks", "a quick
  fix"). Describe concrete deltas, dependencies, risks, and validation instead.
- For an already-running process, report measured elapsed time, progress, or a
  grounded ETA only when the process exposes one; otherwise report its phase,
  latest output, and whether it is still progressing.

## Pick the real fix

- Fix correctness bugs; don't relabel them. Effort or scope framing
  ("non-trivial", "worth its own thread", "later") is no reason for a lesser fix.
- "Mark experimental", "add a TODO", or "reword the misleading comment" does not
  substitute for fixing wrong behavior.
- Take the stronger path and do it. Stop to ask only when the choice changes
  product direction; don't pre-decide a smaller version.
