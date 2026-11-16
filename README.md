# Gamma

Gamma is a Python toolkit for interactive model exploration, model comparison,
benchmarking, and controlled capability-transfer experiments. Its CLI can run a
token-prediction game, compare model outputs, benchmark engines, and coordinate
multiple active model engines.

- [Browser demo](https://gamma-web-game.web.app/)
- [Architecture](docs/ARCHITECTURE.md)
- [Documentation index](docs/README.md)
- [Durable goals](GOALS.md)
- [Component authority index](docs/COMPONENT_INDEX.md)

## Mission, goal, and value

Gamma’s mission is to make model and algorithm behavior inspectable, comparable,
and reproducible under named evaluation contracts.

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
| State-log context | `python -m gamma.core.state_context events.txt --query 'READ REG_03 =>'` | Keep the requested state's source dependencies while discarding irrelevant events. |
| SAME-R | [`projects/samer/`](projects/samer/) | Run matched capability-transfer trials. |
| Interview inventory | [`question bank`](projects/question_bank/README.md) | Browse categorized Hack2Hire entries and review LeetCode overlap. |
| Domain research | [`projects/`](projects/) | Inspect translation, embedding, WGSL, and compression experiments. |
| Integrations | [`integration guide`](docs/integration-guide.md) | Connect APIs, MCP, and external backends. |

Use the command help for workload-specific options:

```bash
python gamma.py help benchmark
python gamma.py help codegen
python gamma.py game --comparison --help
python gamma.py mind-meld --help
```

The [state-log compiler](gamma/core/state_context.py) runs on CPU without a model.
It supports explicit `SET`, `UPDATE`, `COPY` and integer `ADD` records, retaining
original lines and source hashes for the requested `READ`. Its JSON output
contains the compacted prompt and evidence references; `--prompt-only` prints
the prompt, while `--read-state` also returns an exact symbolic answer. Unknown
operations, inconsistent examples and unsupported queries fall back to the
original prompt; exact-answer mode rejects them. This is structured context
preprocessing, not a learned transformation or general-language interpreter.

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

Gamma is intended to become a shared workbench for model and algorithm behavior
research: interactive experiments for inspection, repeatable benchmarks for
comparison, and controlled training, routing, or algorithm trials for capability
changes. Results should remain tied to the exact model or algorithm, prompt or
dataset, runtime, metric, and replay needed to inspect them.

## Limits and current status

Gamma does not turn a benchmark result into a general model claim. Distillation,
RLVR, routing, custom kernels, and prompt changes remain separate experiment
variables unless a study explicitly combines them. Engine-specific setup may
require local GPU, API, or backend configuration; see
[`gamma/engines/README.md`](gamma/engines/README.md). Model weights are not
installed automatically.

## Repository map

See [code, apps, project and evidence boundaries](docs/REPOSITORY_LAYOUT.md) for
installation and the relocation/restore contracts.

- [`gamma/`](gamma/) — runtime, engines, game logic, comparison, and benchmarks
- [`apps/`](apps/) — independently run game, web, MCP and Flux applications
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
