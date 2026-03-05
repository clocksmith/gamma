# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively

Interactive LLM exploration for prediction games, runtime comparison, and model experimentation.

- [Play in your browser](https://simulatte.world)
- [Game codebase: `src/game/README.md`](./src/game/README.md)
- [Architecture map: `docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md)

## What is GAMMA

GAMMA combines three core flows:

- Language model gameplay and confidence-based exploration.
- LLM comparison, benchmarking, and engine selection.
- Distillation / translation / FunctionGemma training workflows.

The project is oriented around quick experimentation with reliable, documented tooling paths.

## Quick start

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
python gamma.py game
```

For engine-specific setup, see [src/engines/README.md](./src/engines/README.md).

## Core CLI

```bash
python gamma.py [command]
```

Available command families are implemented in [gamma.py](./gamma.py):

| Command | Purpose |
|---|---|
| `game` | Play the main game (default command) |
| `comparison` | Compare multiple models on one prompt |
| `mind-meld` | Run collaborative multi-model inference |
| `benchmark` | Run speed/latency runs |
| `codegen` | Run research codegen workflows |
| `list` | List available local models |
| `select` | Run interactive engine/model selector |
| `help` | Show command help |

```bash
python gamma.py help
python gamma.py help codegen
python gamma.py help benchmark
python gamma.py game --help
python gamma.py benchmark --help
```

## Gameplay and core experiences

### The game

Predict next-token behavior with live probabilities and adjustable decoding controls.

```bash
python gamma.py game
```

### Comparison mode

Run side-by-side inference and compare token distributions on the same prompt.

```bash
python gamma.py game --comparison --help
```

### Mind meld

Blend control strategies across multiple models and compare behavior during generation.

```bash
python gamma.py mind-meld --help
```

## Distillation and training

### EmbeddingGemma distillation

Language-targeted subset distillation and retrieval-pipeline data preparation.

- [projects/distillation/embedding/README.md](./projects/distillation/embedding/README.md)

### TranslateGemma distillation

Translation pair mining, pair splitting, optional vocab subset stage, training, and eval.

- [projects/distillation/translation/training/run_translation_distill.sh](./projects/distillation/translation/training/run_translation_distill.sh)
- [projects/distillation/translation/pipeline/run_pipeline.py](./projects/distillation/translation/pipeline/run_pipeline.py)
- [projects/distillation/translation/training/make_translate_distill_pairs.py](./projects/distillation/translation/training/make_translate_distill_pairs.py)

### FunctionGemma training

Replay traces into FunctionGemma experiences and run compact SFT training.

- [src/functiongemma_training/README.md](./src/functiongemma_training/README.md)

## Benchmarks and evaluation

### Performance benchmarks

```bash
python gamma.py benchmark
python gamma.py benchmark --list-models
```

See [src/utils/README.md](./src/utils/README.md) and [docs/optimization-guide.md](./docs/optimization-guide.md) for profiler and memory tooling.

### Codegen benchmarking

Research-style code generation evaluation including language ladder and prompt-quality tracks.

```bash
python gamma.py help codegen
python gamma.py codegen language --help
python gamma.py codegen mind-meld --help
```

Implementation workspace: [tools/codegen-bench/README.md](./tools/codegen-bench/README.md)

## Engines and hardware

Model runtime support and compatibility is maintained in [src/engines/README.md](./src/engines/README.md).

Quick examples:

```bash
python gamma.py game --engine pytorch --model google/gemma-2-2b-it
python gamma.py game --engine mlx --model mlx-community/gemma-2-2b-it-4bit
python gamma.py game --engine llamacpp --model models/model.gguf
python gamma.py game --engine ollama --model /path/to/ollama-model.gguf
```

Logits requirement: comparison and mind-meld modes require direct full-logits engines.

## Integrations and ecosystem

- [docs/NATURAL_LANGUAGE_COMMANDS.md](./docs/NATURAL_LANGUAGE_COMMANDS.md) for command intent examples
- [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) for runtime/module boundaries
- [mcp-server/README.md](./mcp-server/README.md) for MCP integration
- [src/integrations/README.md](./src/integrations/README.md) for OpenAI/LangChain wrappers
- [src/functiongemma_training/README.md](./src/functiongemma_training/README.md) for tool calling SFT paths

## License

MIT - See [LICENSE](./LICENSE)
