# Adaptive Job State

[tools/enwiki9_lab.py](../../tools/enwiki9_lab.py) owns this directory.

Use the [ledger](../../ledger/README.md) to browse this state and the
[adaptive workflow](../../ADAPTIVE_WORKFLOW.md) for exact commands. Follow
the project [AGENTS.md](../../AGENTS.md).

At runtime it creates:

```text
proposals/proposed/
proposals/claimed/
proposals/developed/
proposals/rejected/
pending/
running/
completed/
failed/
cancelled/
mutations.jsonl
experiments/
candidate-revisions/
reflections/
composition/
```

Job files move atomically between state directories. Do not edit a running job.
Algorithm proposals move from proposed to claimed, developed, or rejected and
retain their evidence, leverage, promotion, and kill contracts.
Experiments freeze the comparison, revisions bind candidate source, reflections
record validated terminal decisions, and composition records describe explicit
mechanism combinations. A completed job requires its scientific reflection
before it can justify promotion.
Use `enwiki9_lab.py cancel <job_id>` for pending work and `--force` for an
explicit retry of a terminal candidate-and-scope pair.

Worker output belongs in `../../run_logs/adaptive/`; exact candidate receipts
belong in `../../results/<candidate_id>/`.
