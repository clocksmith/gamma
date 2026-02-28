---
name: gamma-codegen-ladder
description: Design and run GAMMA code generation benchmarks across JavaScript and TypeScript variants, prompt-quality levels, and temperature sweeps. Use when users ask for TS vs JS comparisons, prompt-level studies, or provider benchmarking in src/benchmarks/codegen.
---

# GAMMA Codegen Ladder Skill

Use this skill for codegen benchmark experiments in `src/benchmarks/codegen/`.

## Scope

- TS vs JS comparisons
- Prompt quality ladders (`novice` through `expert`)
- Temperature sweeps and multi-run statistics
- Provider and model comparisons (Ollama and cloud APIs)

## Workflow

1. Inspect available dimensions and providers.
2. Run a dry smoke to verify task and variant selection.
3. Run a small live benchmark.
4. Expand into matrix runs (`language x prompt_level x temperature x provider`).
5. Summarize outputs from generated reports.

## Verified Command Patterns

```bash
node src/benchmarks/codegen/index.js --help
node src/benchmarks/codegen/index.js --list-presets
node src/benchmarks/codegen/index.js --list-providers
node src/benchmarks/codegen/index.js --list-categories
node src/benchmarks/codegen/index.js --list-tasks
```

Dry smoke:

```bash
node src/benchmarks/codegen/index.js \
  --task fibonacci \
  --language js,ts \
  --prompt-level novice,expert \
  --dry
```

Focused live run:

```bash
node src/benchmarks/codegen/index.js \
  --category foundations \
  --language js,ts \
  --prompt-level advanced,expert \
  --provider ollama-gpt-oss-20b \
  --temperature 0.0 \
  --runs 3
```

Temperature sweep:

```bash
node src/benchmarks/codegen/index.js \
  --task expression-evaluator \
  --language js,ts \
  --prompt-level expert \
  --temperatures 0.0,0.5,1.0 \
  --provider ollama-qwen3-coder-30b \
  --runs 2
```

Query interface:

```bash
node src/benchmarks/codegen/query_cli.js --help
node src/benchmarks/codegen/query_cli.js "Which model is fastest for TypeScript?"
```

## Interpretation Checklist

- Compare pass rate and quality deltas between JS and TS at equal prompt levels.
- Separate deterministic (`temperature=0.0`) from creativity sweeps.
- Track run-count variance before declaring winners.
- Keep provider and model versions explicit in every report.

## Guardrails

- Confirm provider availability before live runs (`--list-providers`).
- Use `--dry` on new task matrices before expensive executions.
- Keep category and task scopes small for smoke, then scale up.
