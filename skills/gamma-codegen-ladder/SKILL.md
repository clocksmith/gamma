---
name: gamma-codegen-ladder
description: Design and run GAMMA code generation benchmarks across JavaScript and TypeScript variants, prompt-quality levels, providers, and temperature sweeps. Use for TS vs JS comparisons, prompt-level studies, and src/benchmarks/codegen leaderboard work.
---

# GAMMA Codegen Ladder

Use for `src/benchmarks/codegen/` experiments where dimensions must stay comparable.

## Axes

- Language: `js`, `ts`
- Prompt level: `novice`, `intermediate`, `advanced`, `expert`
- Provider/model
- Temperature and run count
- Task or category

## Workflow

1. List available tasks, categories, providers, and presets.
2. Dry-run the intended matrix.
3. Run a focused live matrix with fixed provider/model and temperature.
4. Expand one axis at a time.
5. Summarize pass rate, quality, latency, and variance from generated reports.

## Commands

```bash
node src/benchmarks/codegen/index.js --help
node src/benchmarks/codegen/index.js --list-presets
node src/benchmarks/codegen/index.js --list-providers
node src/benchmarks/codegen/index.js --list-categories
node src/benchmarks/codegen/index.js --list-tasks
```

```bash
node src/benchmarks/codegen/index.js \
  --task fibonacci \
  --language js,ts \
  --prompt-level novice,expert \
  --dry
```

```bash
node src/benchmarks/codegen/index.js \
  --category foundations \
  --language js,ts \
  --prompt-level advanced,expert \
  --provider ollama-gpt-oss-20b \
  --temperature 0.0 \
  --runs 3
```

```bash
node src/benchmarks/codegen/index.js \
  --task expression-evaluator \
  --language js,ts \
  --prompt-level expert \
  --temperatures 0.0,0.5,1.0 \
  --provider ollama-qwen3-coder-30b \
  --runs 2
```

## Guardrails

- Compare JS and TS only at identical prompt/provider/temperature/run settings.
- Separate deterministic rows from temperature sweeps.
- Confirm provider availability before live runs.
- Use `query_cli.js` only after artifacts exist:
  `node src/benchmarks/codegen/query_cli.js "Which model is strongest for TypeScript?"`
