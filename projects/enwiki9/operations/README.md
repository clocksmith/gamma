# enwiki9 Operations

This directory owns durable operator inputs that are neither source code nor
benchmark evidence.

- `adaptive/` contains atomic pending, running, completed, failed, and cancelled
  job records plus mutation lineage.
- `queues/` contains candidate and gate queue lists.
- Runtime output belongs in `../run_logs/`.
- Candidate results belong in `../results/`.
