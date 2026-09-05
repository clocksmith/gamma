# enwiki9

Compression research toward exact reconstruction of canonical enwik9's
1,000,000,000 bytes with a fully counted score at or below 105,000,000 bytes.
The [objective contract](contracts/research/v1/objective-contract.json) defines
the proof and accounting requirements.

Start with two places:

| Area | Use it for |
| --- | --- |
| [Ledger](ledger/README.md) · [open browser view](ledger/index.html) | Find algorithms, mixes, recorded lineage, current jobs, and the results and decisions behind them. |
| [Workbench](workbench/README.md) · [plain-language prompts](workbench/PROMPTS.md) | Inspect, explore, create, mutate, combine, run, and review research through the existing workflow. |

From `gamma/projects/enwiki9/`, rebuild the local ledger:

```bash
python3 tools/enwiki9_ledger.py
```

Open `ledger/index.html` in a browser. It works offline with no server or
installation. Search by candidate, mechanism, job, or conclusion; open a
candidate for its parents, children, evidence, and run history. Job activity is
a snapshot on the named host; rebuild it when checking what is running.

The ledger reads existing records. To change research state, use
[the adaptive workflow](ADAPTIVE_WORKFLOW.md) and `tools/enwiki9_lab.py`.

```text
ledger/       generated browser view, JSON export, and source map
workbench/    working guide and reusable system/task prompts
programs/     candidate implementations and metadata
operations/   proposals, immutable revisions, lineage, queue, and reflections
results/      measured artifacts and the canonical run ledger
docs/         research decisions, portfolios, reports, and historical references
contracts/    objective, experiment, measurement, and evidence definitions
tools/        supported execution and reporting utilities
```

Existing evidence paths stay stable. Missing metadata, unreviewed outcomes, and
unresolved lineage remain visible in the ledger. Ideas and component forecasts
carry no earned full-corpus score.

For details, see the [algorithm guide](ALGORITHMS.md),
[research register](docs/research_register.md),
[tool router](tools/README.md), and
[technical reference](docs/reference/project_manual.md).

This README is the project map. [AGENTS.md](AGENTS.md) contains the operating
rules for agents throughout this project; [CATSCAN.md](CATSCAN.md) defines its
authority and proof boundaries. The ledger and workbench READMEs explain those
areas, and [PROMPTS.md](workbench/PROMPTS.md) provides reusable task wording.
Current results and running status belong in the linked records and generated
views.
