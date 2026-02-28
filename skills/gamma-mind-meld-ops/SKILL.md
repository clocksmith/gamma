---
name: gamma-mind-meld-ops
description: Operate, debug, and benchmark GAMMA Mind Meld sessions using CLI presets, swap and blend controls, and diagnostics for KV cache replay or translation behavior. Use when users ask to run mind meld, tune swap strategy, or troubleshoot cross-model output quality.
---

# GAMMA Mind Meld Ops Skill

Use this skill for repeatable Mind Meld execution and troubleshooting.

## Entry Points

- Primary operator CLI: `tools/run_mind_meld_cli.py`
- Core command path: `gamma.py mind-meld`
- Diagnostics docs: `docs/mind_meld_status.md`, `src/mind_meld/README.md`

## Hard Constraints

- Mind Meld requires logits-capable engines.
- Wrapper engines (`openai`, `huggingface_inference`, `ollama`) are not compatible for Mind Meld generation because they do not expose raw logits.
- KV cache translation is experimental; replay fallback is expected and often safer.

## Workflow

1. Validate models and flags with `--help` and `--list-*`.
2. Run a short headless smoke test.
3. Run target strategy with diagnostics and optional stats file.
4. Inspect `kv_cache_*` and guardrail counters.
5. Adjust strategy, blending, and template settings, then re-run.

## Verified Command Patterns

Use venv python when present:

```bash
PY=.venv/bin/python
[ -x "$PY" ] || PY=python3
```

Discover options:

```bash
$PY tools/run_mind_meld_cli.py --help
$PY tools/run_mind_meld_cli.py --list-presets
$PY tools/run_mind_meld_cli.py --list-aliases
$PY gamma.py help mind-meld
```

Quick smoke (headless + diagnostics):

```bash
bash skills/gamma-mind-meld-ops/scripts/mind_meld_smoke.sh
```

Stable baseline run:

```bash
$PY tools/run_mind_meld_cli.py gemma-1b gemma-2b \
  --blend dynamic \
  --strategy pattern \
  --prompt "Explain why deterministic benchmarks matter." \
  --steps 64 \
  --summary-only \
  --headless \
  --no-step-delay \
  --shared-chat-template \
  --meld-diagnostics \
  --stats-file mind_meld_stats.json
```

Experimental KV translation run:

```bash
$PY tools/run_mind_meld_cli.py gemma-1b gemma-2b \
  --strategy fixed_interval \
  --interval 8 \
  --allow-kv-cache-translation \
  --translate-logits \
  --use-enhanced \
  --summary-only \
  --headless \
  --meld-diagnostics
```

## Diagnostics Interpretation

- `kv_cache_translated > 0`: translation path used.
- `kv_cache_replay > 0`: replay fallback used.
- `guardrail_replay > 0`: guardrails blocked risky translation and forced replay.
- High replay counts with good output are acceptable; prioritize correctness over theoretical speed.

## Tuning Heuristics

- Start with `--shared-chat-template` for lower order sensitivity.
- Use `--order-neutral` or `--use-weighted-average` when swap order causes drift.
- Use `--soft-swap` to keep cadence while smoothing transitions.
- Reserve `--force-kv-cache-translation` for controlled debugging only.
