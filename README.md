# Gamma

Gamma is a Python toolkit for interactive model exploration, model comparison,
benchmarking, and controlled capability-transfer experiments. Its CLI can run a
token-prediction game, compare model outputs, benchmark engines, and coordinate
multiple active model engines.

- [Browser demo](https://gamma-web-game.web.app/)
- [Architecture](docs/ARCHITECTURE.md)
- [Documentation index](docs/README.md)

## Mission, goal, and value

Gamma’s mission is to make model behavior comparable under a fixed evaluation
setup.

The current goal is to give researchers and engineers one place to inspect
token choices, compare models and runtimes, run benchmark workloads, and record
whether a change improved the named task. The repository also carries domain
experiments for translation, embeddings, WGSL, compression, and the SAME-R
method.

Gamma serves:

- Researchers testing prompts, datasets, training methods, or routing policies.
- Engineers comparing engines, kernels, latency, and output quality.
- Reviewers checking whether an improvement survives a fixed benchmark and
  replication contract.
- People learning how tokenization, logits, attention, and decoding affect an
  output.

## How to use Gamma

Create the environment and run the interactive game:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python gamma.py game
```

The main command is:

```bash
python gamma.py [command] [options]
```

| Surface | Command or link | Use |
| --- | --- | --- |
| Game and chat | `python gamma.py game` | Explore next-token prediction and model choices. |
| Comparison | `python gamma.py comparison` | Compare model outputs and decoding behavior. |
| Benchmarking | `python gamma.py benchmark` | Measure throughput, latency, output quality, or code generation. |
| Mind Meld | `python gamma.py mind-meld` | Coordinate and route across active model engines. |
| SAME-R | [`projects/samer/`](projects/samer/) | Run matched capability-transfer trials. |
| Domain research | [`projects/`](projects/) | Inspect translation, embedding, WGSL, and compression experiments. |
| Integrations | [`integration guide`](docs/integration-guide.md) | Connect APIs, MCP, and external backends. |

Use the command help for workload-specific options:

```bash
python gamma.py help benchmark
python gamma.py help codegen
python gamma.py game --comparison --help
python gamma.py mind-meld --help
```

## Evidence and method

SAME-R means **Swappable Approaches under Matched Evaluation and Replication**.
It changes the approach while holding the evaluation benchmark, success metric,
objective, control environment, and replication contract fixed. The method
helps attribute a measured change to the approach; it does not make a weak
benchmark or an incomplete replication valid.

For each experiment, record the named baseline, changed inputs, evaluation set,
metric, runtime, and replication result. The [SAME-R protocol](projects/samer/README.md)
defines the experiment contracts. The [benchmarking guide](docs/BENCHMARKING.md)
defines the comparison and performance workflow.

## Long-term vision

Gamma is intended to become a shared workbench for model behavior research:
interactive experiments for inspection, repeatable benchmarks for comparison,
and controlled training or routing trials for capability changes. Results should
remain tied to the exact model, prompt or dataset, runtime, metric, and replay
needed to inspect them.

## Limits and current status

Gamma does not turn a benchmark result into a general model claim. Distillation,
RLVR, routing, custom kernels, and prompt changes remain separate experiment
variables unless a study explicitly combines them. Engine-specific setup may
require local GPU, API, or backend configuration; see
[`src/engines/README.md`](src/engines/README.md). Model weights are not
installed automatically.

## Repository map

- [`src/`](src/) — runtime, engines, game logic, comparison, and benchmarks
- [`projects/`](projects/) — distillation, SAME-R, embedding, translation, WGSL, and compression work
- [`tools/`](tools/) — developer and model-analysis utilities
- [`requirements/`](requirements/) — dependency manifests by hardware and engine
- [`docs/`](docs/) — architecture, benchmark, integration, and method guides
- [`tests/`](tests/) — automated test suites
- [`gamma.py`](gamma.py) — CLI entrypoint

## Read next

- [Documentation index](docs/README.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Benchmarking guide](docs/BENCHMARKING.md)
- [SAME-R protocol](projects/samer/README.md)
- [Verifier-guided learning](docs/VERIFIER_GUIDED_LEARNING.md)
- [Integration guide](docs/integration-guide.md)

## License

[MIT License](LICENSE)
