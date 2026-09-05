# enwiki9 Operations

This directory owns durable operator inputs that are neither source code nor
benchmark evidence.

Browse jobs and their linked results in the [ledger](../ledger/README.md).
Use the [workbench](../workbench/README.md) and
[adaptive workflow](../ADAPTIVE_WORKFLOW.md) to change state. The project
[AGENTS.md](../AGENTS.md) supplies the operating rules.

- `adaptive/` contains atomic pending, running, completed, failed, and cancelled
  job records plus mutation lineage.
- `queues/` contains candidate and gate queue lists.
- Runtime output belongs in `../run_logs/`.
- Candidate results belong in `../results/`.
