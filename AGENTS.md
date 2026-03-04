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
- Verify all train/eval pair files exist and match intended input spec.
- If resuming, verify `resume_from` exists and is consistent with `resume_stage`.
- If checkpoint loading can fail from vocab/tokenizer mismatch, stop and fix before launch.

Block immediately on these failure classes:
- Environment drift (`/usr/bin/python3` vs `.venv/bin/python` / missing deps).
- ROCm invalid-device errors (`HIP error: invalid device function`).
- Resume-stage mismatch (wrong checkpoint/state continuation).
- Provenance confusion (`available rows` vs `rows used`, decode/eval mixups).

For every run/sweep, log one contract line:
```text
[run-contract] run_name=<name> pairs_input_spec=<path-or-spec> resume_from=<path|none> resume_stage=<stage|none> decode=<greedy|sampled> eval_dataset_paths=<comma-separated paths> device=<auto|cuda|cpu> schedule=<A_then_B|mixed_from_start> runtime_mode=<normal_rocm|rocm_gfx_override|cpu>
```

After each sweep or major eval batch, ensure these artifacts exist and are linked:
- `manifest.jsonl`
- `scoreboard.md`
- `scoreboard_eval_rows.csv`
- `scoreboard_checkpoints.csv`
- refreshed run index via:
```bash
python3 projects/distillation/translation/pipeline/build_run_index.py
```

### Key Paths
- `src/game/` - Game logic and UI
- `src/engines/` - Engine backends (llamacpp, pytorch, vllm, ollama)
- `src/mind_meld/` - Multi-model collaboration
- `src/benchmarks/` - Performance testing
- `src/comparison/` - Model comparison tools

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
