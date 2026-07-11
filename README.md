# GAMMA

**G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively

Interactive LLM exploration for gameplay, model comparison, and reproducible benchmarking.

- Browser demo: https://simulatte.world
- Architecture map: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- Full docs index: [docs/README.md](./docs/README.md)

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gamma.py game
```

Engine-specific setup is in [src/engines/README.md](./src/engines/README.md).

## Repository Layout

The root is limited to stable entrypoints, project metadata, and tool configuration.

| Path | Ownership |
|---|---|
| `src/` | Gamma runtime, engines, game, benchmarks, and integrations |
| `projects/` | Self-contained research and distillation work |
| `tools/` | Operator-facing utilities and model analysis |
| `requirements/` | Engine and hardware-specific dependency manifests |
| `docs/` | Canonical architecture and usage documentation |
| `tests/` | Automated test suites |

Keep generated reports under `reports/`, run output under its owning project, and
new project-specific utilities beside that project rather than at repository root.

## CLI Surface

```bash
python gamma.py [command]
```

| Command | Purpose |
|---|---|
| `game` | Interactive gameplay and chat-style runs |
| `comparison` | Side-by-side model comparison |
| `mind-meld` | Multi-model collaboration and swapping |
| `benchmark` | Throughput/latency benchmarking |
| `codegen` | Code-generation benchmark workflows |
| `list` | List available models |
| `select` | Interactive model/engine selector |
| `help` | Command help |

```bash
python gamma.py help
python gamma.py help benchmark
python gamma.py help codegen
python gamma.py game --comparison --help
python gamma.py mind-meld --help
```

## Canonical Documentation

- [docs/README.md](./docs/README.md): documentation map and ownership
- [docs/BENCHMARKING.md](./docs/BENCHMARKING.md): speed, quality, codegen, and mind-meld benchmarking
- [docs/HYBRID_DISTILLATION.md](./docs/HYBRID_DISTILLATION.md): reusable hybrid distillation method for coding, translation, and capability students
- [docs/integration-guide.md](./docs/integration-guide.md): OpenAI/LangChain/API/MCP integrations
- [src/mind_meld/README.md](./src/mind_meld/README.md): Mind Meld usage, configs, and operational guardrails
- [flux/README.md](./flux/README.md): Flux install, CLI, and reference
- [tools/README.md](./tools/README.md): project tooling and feedback loop commands
- [requirements/README.md](./requirements/README.md): dependency profiles by engine and hardware
- [projects/distillation/embedding/README.md](./projects/distillation/embedding/README.md): EmbeddingGemma distillation
- [projects/distillation/translation/README.md](./projects/distillation/translation/README.md): TranslateGemma distillation
- [src/functiongemma_training/README.md](./src/functiongemma_training/README.md): FunctionGemma training path

## Integrations and Ecosystem

- [docs/NATURAL_LANGUAGE_COMMANDS.md](./docs/NATURAL_LANGUAGE_COMMANDS.md)
- [mcp-server/README.md](./mcp-server/README.md)
- [docs/integration-guide.md](./docs/integration-guide.md)

## License

MIT. See [LICENSE](./LICENSE).
