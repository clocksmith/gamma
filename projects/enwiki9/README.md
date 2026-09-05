# enwiki9

Compression research toward exact reconstruction of canonical enwik9's
1,000,000,000 bytes with a fully counted score at or below 99,000,000 bytes.
This is a provisional engineering target; 105M remains a historical milestone.
[Competitive provenance](operations/provenance/competitive_frontier_v1.json) separates
published submissions from the official record and committee-dependent threshold.
The [objective contract](contracts/research/v2/objective-contract.json) defines
the proof and accounting requirements.

Start with two places:

| Area | Use it for |
| --- | --- |
| [Ledger](ledger/README.md) · [open browser view](ledger/index.html) | Find algorithms, mixes, recorded lineage, current jobs, and the results and decisions behind them. |
| [Workbench](workbench/README.md) · [plain-language prompts](workbench/PROMPTS.md) | Inspect, explore, create, mutate, combine, run, and review research through the existing workflow. |

For an agent entering `gamma/projects/enwiki9/`, start with:

```bash
python3 tools/enwiki9_lab.py start
python3 tools/enwiki9_lab.py records --search 'YOUR_MECHANISM'
```

`start` reports current record coverage, observed jobs, held work, review gaps,
and available tools. `records` searches canonical records or opens a candidate's
lineage and history. Both read current local records without launching a job.
When the user says "go", follow the [operating manual](workbench/README.md)
for research, benchmarks, simulations, and result recording.

For browser navigation, run `python3 tools/enwiki9_ledger.py` and open
`ledger/index.html`. It works offline without a server or installation.
The browser is a snapshot on the named host; rebuild it for current records.

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
