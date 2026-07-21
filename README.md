# GAMMA

> A toolkit for exploring, measuring, comparing, and improving language models through interactive and reproducible experiments.

* **Browser Demo:** [gamma-web-game.web.app](https://gamma-web-game.web.app/)
* **Architecture Map:** [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md)
* **Full Documentation Index:** [docs/README.md](./docs/README.md)

---

## What GAMMA Means

`GAMMA` is the stable project name and CLI command, but the acronym adapts to match your current workflow:

| Context | Reading | Focus Area |
| :--- | :--- | :--- |
| **Interactive Game** | **G**ame **A**nalyzing **M**odel **M**ethods **A**ttentively | Predict model continuations and inspect token-level probability choices. |
| **Benchmarking** | **G**uessing **A**lternative **M**odel **M**echanics **A**nalytically | Compare models, engines, decoding policies, and runtime performance. |
| **Interpretability** | **G**rasping **A**ttention **M**echanism **M**ysteries **A**ccessibly | Demystify logits, tokenization, attention heads, and generation mechanics. |
| **SAME-R Research** | **G**eneralized **A**pproach **M**atching, **M**easurement, and **A**ttribution | Test new methods under identical evaluation setups to isolate causes of improvement. |

---

## Tool Surfaces

| Surface | CLI Command / Link | Purpose |
| :--- | :--- | :--- |
| **Game & Chat** | `python gamma.py game` | Interactively explore next-token prediction and model choices. |
| **Benchmarking** | `python gamma.py comparison`<br>`python gamma.py benchmark` | Measure speed, latency, output quality, and code generation. |
| **Mind Meld** | `python gamma.py mind-meld` | Coordinate, route, and swap among multiple active model engines. |
| **SAME-R Method** | [projects/samer/README.md](./projects/samer/README.md) | Controlled capability-transfer trials under matched baselines. |
| **Domain Research** | [projects/](./projects/) | Domain experiments (translation, embeddings, WGSL, compression). |
| **Integrations** | [docs/integration-guide.md](./docs/integration-guide.md) | Connect via APIs, Model Context Protocol (MCP), and external backends. |

---

## Quick Start

```bash
# Set up environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run the interactive game
python gamma.py game
```

*> For engine-specific setups (e.g., local GPUs, APIs), refer to [src/engines/README.md](./src/engines/README.md).*

---

## The SAME-R Research Method

**SAME-R** (**S**wappable **A**pproaches under **M**atched **E**valuation and **R**eplication) is Gamma's methodology for controlled AI experiments.

> **Core Philosophy:** *"Different inners. Same rims."*

* **Inners (What you change):** Prompts, dataset variations, human/agent labeling, SFT, distillation, RLVR, routing policies, custom kernels, etc.
* **Rims (What stays fixed):** Evaluation benchmarks, success metrics, objective functions, control environments, and replication contracts.

By keeping the "rim" strictly identical, SAME-R ensures that any measured improvement comes from the technique itself, not a shifting baseline.

---

## Repository Layout

To keep the root clean, top-level files are limited to entry points, metadata, and tool configs.

| Directory | Description / Contents |
| --- | --- |
| `src/` | Core Gamma runtime, engine wrappers, game logic, benchmarks, and integrations. |
| `projects/` | Self-contained research, distillation experiments, and custom workflows. |
| `tools/` | Developer/operator utility scripts and model analysis scripts. |
| `requirements/` | Dependency manifests grouped by hardware profile and engine requirements. |
| `docs/` | Canonical architecture diagrams, user guides, and reference material. |
| `tests/` | Automated test suites. |

*> Note: Keep generated reports inside `reports/` and project-specific outputs within their respective sub-directories in `projects/`.*

---

## CLI Usage

```bash
python gamma.py [command] [options]
```

### Main Commands

* `game` — Interactive next-token gameplay and chat interface.
* `comparison` — Side-by-side output and performance comparison.
* `mind-meld` — Orchestrate and swap across multiple model engines.
* `benchmark` — Measure system throughput and latency.
* `codegen` — Benchmark code generation abilities.
* `list` / `select` — Interactively list or select active models.
* `help` — Print command assistance.

### Helpful Context Commands

```bash
python gamma.py help benchmark
python gamma.py help codegen
python gamma.py game --comparison --help
python gamma.py mind-meld --help
```

---

## Documentation Index

* **[Docs Index](./docs/README.md):** Complete documentation map and ownership.
* **[Benchmarking Guide](./docs/BENCHMARKING.md):** Performance, speed, quality, and Mind Meld testing.
* **[SAME-R Protocol](./projects/samer/README.md):** Experiment frameworks and promotion contracts.
* **[Verifier-Guided Learning](./docs/VERIFIER_GUIDED_LEARNING.md):** Reward taxonomies, prompt optimization, and RLVR.
* **[Integrations Guide](./docs/integration-guide.md):** APIs, LangChain, and MCP setup.

---

## License

[MIT License](./LICENSE)
