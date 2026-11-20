# Gamma

Gamma builds a catalogue of qualified JavaScript and Python programs and studies how compact vocabularies (BITS) encode and compose them. It also provides a Python toolkit (`gamma.py`) for inspecting token probabilities, comparing model runtimes, and running controlled experiments under locked protocols. Today, model and algorithm comparisons routinely blur benchmarks, omit setup costs, and drop failed runs, making it hard to tell whether a new method beats a plain baseline.

Gamma separates protocols, execution, and reporting—fixing datasets, budgets, and baselines beforehand, charging full costs, and preserving null results alongside wins. Explore the [catalogue roadmap](projects/algorithm_solver/catalogue/ROADMAP-v1.md), [durable goals](GOALS.md), [architecture](docs/ARCHITECTURE.md), and [documentation index](docs/README.md).

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/readme/qwen-b1-development-card-dark.svg">
  <img src="assets/readme/qwen-b1-development-card-light.svg" alt="The adapter beat warm KV. The plain classifier beat both. Qwen 3.5 0.8B development run (seed 1103, 48 tables, 768 questions): plain classifier 747/768 (97.3%, +1.0 pt vs adapter, inside 5-pt margin, 187 ms/q), readout adapter 739/768 (96.2%, +5.1 pts vs warm KV, 255 ms/q, 92-184 KB), warm KV 700/768 (91.1%, 246 ms/q, 32.4 MB median)." width="100%">
</picture>

## Try it

- **BITS (program composition):** pick a vocabulary and compose a program at [256.one/labs/two-button](https://256.one/labs/two-button/).
- **Browser token game:** [gamma-web-game.web.app](https://gamma-web-game.web.app/).
- **Python CLI:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  python gamma.py game          # Also: comparison, benchmark, mind-meld
  ```

## What is verified

- **Completed:**
  - **BITS promotion (80 qualified JavaScript programs):** reduced selections from `10,155` to `9,910` (`-2.41%`) and size from `13,002` to `12,798` bytes ([promotion receipt](projects/algorithm_solver/literals/guides-joint80-v2/README.md) · [promotion rules](projects/algorithm_solver/literals/BITS_PROMOTION.md)).
  - **Qwen 3.5 0.8B B1 development run (seed 1103, 48 tables, 768 questions; exploratory split, not a confirmation):** the plain classifier (`probe_bare`) scored `747/768` (`97.3%`, `+1.0 pt` vs adapter, `90% CI +0.1 to +2.1`, inside the 5-point margin; `187 ms/q` median; retained bytes not reported in receipt), the readout adapter (`ra_bare`) scored `739/768` (`96.2%`, `+5.1 pts` vs warm KV; `255 ms/q`, `+9 ms` slower than warm KV; `92-184 KB`), and warm KV (`kv_ctx`) scored `700/768` (`91.1%`; `246 ms/q`; `32.4 MB` median) ([results](projects/reconfiguration/query_swiglu_fastweight_v5/RESULTS.md) · [development protocol](projects/reconfiguration/query_swiglu_fastweight_v5/protocol_v5_draft.json) · [tracked receipt JSON](.work/query-swiglu-fastweight-v5/qwen35_08b_dev1103_k20_readout_adapter.json)).
- **Closed / Open:**
  - **Closed:** Track B2 (self-improving proposer) closed after tying trained constants `4-4`; `enwiki9` compression is retired and archived.
  - **Open:** locked MiniCPM4 B1 confirmation run is in progress (separate from the Qwen 3.5 0.8B development run above); original compact-library `M1` remains unmet.

## CLI surfaces and research tracks

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
