# SWE-bench Agent (v2)

A compact SWE-bench agent built around a single conductor and a FunctionGemma ring for tool selection.

## Quick Start

```bash
# Mock run (no real models)
python -m gamma.src.swe.agent --mock "Find QuerySet.union implementation"

# Ollama run
python -m gamma.src.swe.agent --ollama --conductor-model gptoss-20b --fng-model functiongemma:latest "Fix the auth bug"

```

## Architecture

```
Conductor (large model)
    |
    v
FunctionGemma Ring (parallel tool selection)
    |
    v
Tool Executors (grep, read_file, git_diff, run_tests, ...)
```

## Components

- **Conductor**: Plans steps, queries the ring, and writes the final patch.
- **Ring**: Runs multiple FunctionGemma nodes in parallel and scores tool results.
- **Tools**: Simple Python scripts with `execute()` in `tools/scripts/`.
- **Integrations**: Model backends (Ollama, Transformers, Anthropic).
- **Runner**: SWE-bench runner and execution helpers.
- **FunctionGemma training**: standalone utilities in `src/functiongemma_training/`.

## Directory Structure

```
src/swe/
├── agent.py             # Main agent
├── conductor/           # Conductor implementation
├── ring/                # FunctionGemma ring
├── tools/               # Tool scripts and loader
├── integrations/        # Model backends
├── runner/              # SWE-bench runner + execution helpers
└── core/                # History, trajectory, exceptions
```

## Evaluation

```bash
# Run SWE-bench with mock models
python -m gamma.src.swe.runner.bench.cli --mock --max-tasks 3

# Evaluate existing predictions
python -m gamma.src.swe.runner.bench.cli --eval-only predictions.jsonl
```
