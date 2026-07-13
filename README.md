# GAMMA

A toolkit for exploring, measuring, comparing, and improving language models
through interactive and reproducible experiments.

- Browser demo: https://simulatte.world
- Architecture map: [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
- Full docs index: [docs/README.md](./docs/README.md)

## What GAMMA Means

GAMMA is deliberately a family name rather than one rigid expansion. Each
backronym names a real project surface or goal:

| Context | Reading | What it names |
|---|---|---|
| Interactive game | **G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively | Predicting model continuations and inspecting the choices behind them. |
| Comparison and benchmarking | **G**uessing **A**lternative **M**odel **M**echanics **A**nalytically | Comparing models, engines, decoding policies, and performance under recorded contracts. |
| Learning and interpretability | **G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly | Making logits, tokenization, attention-capable backends, and generation mechanics understandable. |
| SAME-R research | **G**eneralized **A**pproach **M**atching, **M**easurement, and **A**ttribution | Testing different methods under matched evaluation and determining what caused an observed improvement. |

These are contextual readings, not separate product names. `GAMMA` remains the
stable project and command identity.

## Choose a Surface

| Surface | Purpose | Starting point |
|---|---|---|
| Game and chat | Explore next-token prediction interactively. | `python gamma.py game` |
| Comparison and benchmarking | Compare model behavior, throughput, latency, and code generation. | `python gamma.py comparison` or `python gamma.py benchmark` |
| Mind Meld | Coordinate and swap among multiple model engines. | `python gamma.py mind-meld` |
| SAME-R | Compare prompts, data, teachers, training methods, routers, kernels, or other approaches under matched rims. | [projects/samer/README.md](./projects/samer/README.md) |
| Domain research | Run translation, embedding, WGSL, compression, and other owned experiments. | [projects/](./projects/) |
| Integrations | Connect Gamma through APIs, MCP, and supported model engines. | [docs/integration-guide.md](./docs/integration-guide.md) |

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gamma.py game
```

Engine-specific setup is in [src/engines/README.md](./src/engines/README.md).

## SAME-R Research Method

**SAME-R** is Gamma's implementation-neutral outer method: **Swappable
Approaches under Matched Evaluation and Replication**. Its recursive expansion
is **SAMER Applies Methods, Evaluates, Repeats**.

> Different inners. Same rims.

The inner approach can be human or agent labeling, data construction, prompt
search, SFT, distillation, preference or policy optimization, routing, kernel
search, or a future method. SAME-R keeps the objective, evaluator, controls,
replication policy, receipts, and promotion boundary matched. A SAME-R instance
may itself run as an inner approach.

Gamma currently executes SAME-R through domain project scripts, manifests, and
human-selected interventions. The shared automatic approach registry and
selector remain an explicit implementation boundary.

- [SAME-R project and capability-transfer protocol](./projects/samer/README.md)
- [Cross-repository experiment register](./projects/samer/experiments/README.md)
- [Verifier-guided optimizer and reward taxonomy](./docs/VERIFIER_GUIDED_LEARNING.md)

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
- [projects/samer/README.md](./projects/samer/README.md): SAME-R algorithm, controlled capability-transfer trials, and promotion contract
- [docs/VERIFIER_GUIDED_LEARNING.md](./docs/VERIFIER_GUIDED_LEARNING.md): prompt optimization, verifier-filtered data, RLVR, domain reward boundaries, and experiment states
- [projects/samer/experiments/README.md](./projects/samer/experiments/README.md): cross-repository experiment register contract
- [docs/integration-guide.md](./docs/integration-guide.md): OpenAI/LangChain/API/MCP integrations
- [src/mind_meld/README.md](./src/mind_meld/README.md): Mind Meld usage, configs, and operational guardrails
- [flux/README.md](./flux/README.md): Flux install, CLI, and reference
- [tools/README.md](./tools/README.md): project tooling and feedback loop commands
- [requirements/README.md](./requirements/README.md): dependency profiles by engine and hardware
- [projects/distillation/embedding/README.md](./projects/distillation/embedding/README.md): EmbeddingGemma distillation
- [projects/distillation/translation/README.md](./projects/distillation/translation/README.md): TranslateGemma distillation
- [projects/distillation/wgsl/README.md](./projects/distillation/wgsl/README.md): Doppler WGSL SFT, DPO, rollout, and GRPO optimizer backend
- [src/functiongemma_training/README.md](./src/functiongemma_training/README.md): FunctionGemma training path

## Integrations and Ecosystem

- [docs/NATURAL_LANGUAGE_COMMANDS.md](./docs/NATURAL_LANGUAGE_COMMANDS.md)
- [mcp-server/README.md](./mcp-server/README.md)
- [docs/integration-guide.md](./docs/integration-guide.md)

## License

MIT. See [LICENSE](./LICENSE).
