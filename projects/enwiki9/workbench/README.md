# enwiki9 workbench

Use the [ledger](../ledger/index.html) to find algorithms, candidates, mixes,
lineage, current jobs, and run history. Use the [prompts](PROMPTS.md) to ask an
agent to move the work forward in plain language.

This guide explains the working loop. The project's [AGENTS.md](../AGENTS.md)
provides the operating rules for this directory, and [PROMPTS.md](PROMPTS.md)
provides reusable task wording. Store resulting work in the canonical locations
below; `workbench/` holds the guide and prompts.

The ledger is a generated view of the existing research records. Change those
records through the adaptive workflow, then rebuild the view. Its build time
does not establish that a listed process is still running.

From `gamma/projects/enwiki9/`:

```bash
python3 tools/enwiki9_lab.py status
python3 tools/enwiki9_ledger.py
```

Open [ledger/index.html](../ledger/index.html), or use the
[ledger guide and source map](../ledger/README.md).

| What you need | Where it lives |
| --- | --- |
| An overview and links to evidence | [Ledger](../ledger/README.md) |
| Ideas, prior findings, and reasons for decisions | [Research register](../docs/research_register.md) |
| Hypotheses, controls, and gate conditions | [Frozen experiments](../operations/adaptive/experiments/) |
| Candidate source and parent relationships | [Programs](../programs/) and [mutation history](../operations/adaptive/mutations.jsonl) |
| Queued work, terminal jobs, and reflections | [Adaptive state](../operations/adaptive/) |
| Measured artifacts and registered runs | [Results](../results/) and [run ledger](../results/run_ledger.jsonl) |

A working loop:

1. Find the relevant family, parent, running work, and previous conclusions.
2. Choose a falsifiable mechanism and the smallest comparison that can resolve it.
3. Freeze the contract, claim the proposal, and create a unique candidate through
   `tools/enwiki9_lab.py`. Preserve running and sealed source.
4. Queue and run the justified gate with its own outputs and resource guards.
   Independent gates can run together when their contracts and host resources permit.
5. Validate the terminal evidence, record a reflection and conclusion, and rebuild
   the ledger. Keep infrastructure failures distinct from scientific misses.

The [objective contract](../contracts/research/v1/objective-contract.json) defines
the target: exact reconstruction of canonical enwik9's 1,000,000,000 bytes with
a fully counted score at or below 105,000,000 bytes. Prefixes, forecasts, shadows,
and infrastructure checks retain their own evidence units and scope. A mix needs
a new joint replay to establish its combined result.

For command details and recording rules, follow the
[adaptive workflow](../ADAPTIVE_WORKFLOW.md), [project instructions](../AGENTS.md),
and [component charter](../CATSCAN.md).
