# enwiki9

Compression research toward exact reconstruction of canonical enwik9's
1,000,000,000 bytes with a fully counted score at or below 99,000,000 bytes.
The [active objective](contracts/research/v2/objective-contract.json) defines the
proof. This is a provisional engineering target; the unchanged 105M objective
remains historical. [Competitive provenance](operations/provenance/competitive_frontier_v1.json)
separates published submissions, the official record, and contingent thresholds.

From `gamma/projects/enwiki9/`, begin with:

```bash
python3 tools/enwiki9_lab.py start
```

| Start here | Purpose |
| --- | --- |
| [Agent rules](AGENTS.md) | Permissions, evidence invariants, and ownership |
| [Command manual](ADAPTIVE_WORKFLOW.md) | Find records, research, create, benchmark, simulate, review, and publish |
| [Ledger](ledger/README.md) · [browser](ledger/index.html) | Algorithms, mixes, lineage, jobs, results, and source links |
| [Workbench](workbench/README.md) · [task prompts](workbench/PROMPTS.md) | Choose a concrete task or begin with “go” |
| [Tool catalogue](docs/tooling_inventory.md) | Discover existing implementations and utilities |

```text
programs/     candidate implementations and metadata
operations/   proposals, frozen experiments, revisions, queue, and reflections
results/      measured artifacts and canonical run ledger
docs/         research decisions, portfolios, generated reports, and references
contracts/    objective, experiment, measurement, and evidence definitions
lib/          reusable predictor and measurement interfaces
tools/        execution, research, and reporting utilities
ledger/       generated browser and JSON projection of canonical records
workbench/    reusable task prompts and workflow pointers
```

Read the [algorithm guide](ALGORITHMS.md), [research register](docs/research_register.md),
or [historical technical reference](docs/reference/project_manual.md) as needed.
Current status and results belong in linked records and generated views. The
[component charter](CATSCAN.md) defines the project's authority and proof boundary.
