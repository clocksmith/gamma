---
name: gamma-codegen-ladder
description: Run a controlled Gamma code-generation matrix when its tasks, languages, prompt levels, providers, temperatures, and run counts are explicitly supplied.
---

# GAMMA Codegen Ladder

Use for `src/benchmarks/codegen/` experiments where dimensions must stay comparable.

## Prerequisites

Supply the task or category, language set, prompt levels, provider/model, temperature,
run count, comparison metric, and authorization for any paid or remote provider.

## Procedure

1. Enumerate supported axes and dry-run the exact supplied matrix.
2. Run the fixed baseline, then vary only the declared independent axis.
3. Validate raw artifacts and regenerate the report without changing the benchmark
   question, prompts, or provider selection.

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

## Validation

Every compared row has identical axis values except the declared independent
variable, includes its raw artifact, and appears in the regenerated report.

## Stop Conditions

Stop before running paid or remote providers without authorization. Stop comparison
when prompts, providers, temperatures, run counts, or output parsing are not aligned.

## Outputs

Raw matrix artifacts and a report of the declared axis deltas, pass rate, latency, and
variance.

## Side Effects

Runs provider/model workloads and writes benchmark artifacts. It does not choose the
benchmark question, alter prompts, update leaderboards, or make product recommendations.
