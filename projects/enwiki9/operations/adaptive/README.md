# Adaptive Job State

`tools/enwiki9_lab.py` owns this directory.

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
```

Job files move atomically between state directories. Do not edit a running job.
Algorithm proposals move from proposed to claimed, developed, or rejected and
retain their evidence, leverage, promotion, and kill contracts.
Use `enwiki9_lab.py cancel <job_id>` for pending work and `--force` for an
explicit retry of a terminal candidate-and-scope pair.

Worker output belongs in `../../run_logs/adaptive/`; exact candidate receipts
belong in `../../results/<candidate_id>/`.
