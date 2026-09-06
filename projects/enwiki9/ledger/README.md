# Research ledger

[Open browser](index.html) · [JSON export](ledger.json) ·
[Command manual](../ADAPTIVE_WORKFLOW.md#start-and-find-records) ·
[Tool catalogue](../docs/tooling_inventory.md)

The ledger projects canonical research records into a searchable local view.
From `gamma/projects/enwiki9/`, rebuild it with:

```bash
python3 tools/enwiki9_ledger.py
```

Open `ledger/index.html` directly; no server, installation, or network is needed.
The HTML and JSON are ignored local snapshots, so rebuild on each device.
`--summary` reports coverage without writing them. Agents can query records
directly through the command manual's `enwiki9_lab.py records` interface.

| Browser view | Contents |
| --- | --- |
| Algorithms | Candidates, proposals, ideas, lineage, and linked evidence |
| Running & queued | Jobs, holds, and host/timestamp-specific process observations |
| Results | Exact receipts and retained summaries with scope, units, and verdicts |
| Mixes | Composition graphs and explicitly described combinations |
| Research notes | Register decisions, archives, and historical candidate notes |
| Tools | Generated catalogue of existing implementations and utilities |

Current algorithm/result views keep active work visible. Enable history or
search explicitly to find retired work; candidate detail retains complete indexed
lineage and runs. Lists are paginated. Follow source links before using a claim.
Search includes reflection lessons, causes, retired dimensions, uncertainties,
and next actions. Candidate history keeps their source reflection links and
recorded validity; finding a lesson does not validate its evidence.
Use the [terminal recorder](../ADAPTIVE_WORKFLOW.md#record-a-closed-comparison)
to publish a reviewed arm set to the existing run ledger. Routine refresh already
rebuilds this browser; a separate browser-generation command is only needed when
you want to refresh this view alone.

## Record map

| Record | Canonical source |
| --- | --- |
| Candidate identities and source | [Programs](../programs/), [curated registry](../index.json), [filesystem audit](../candidate_inventory.json) |
| Lineage | [Mutation records](../operations/adaptive/mutations.jsonl), [candidate revisions](../operations/adaptive/candidate-revisions/) |
| Ideas and proposals | [Research register](../docs/research_register.md), named portfolio JSONs in `docs/`, [proposals](../operations/adaptive/proposals/) |
| Jobs and decisions | [Adaptive state](../operations/adaptive/), [reflections](../operations/adaptive/reflections/) |
| Frozen comparison | [Experiments](../operations/adaptive/experiments/) |
| Scoped negative findings | [OMEGA exclusions](../operations/adaptive/exclusions/) |
| Measurements | [Run ledger](../results/run_ledger.jsonl), [retained results](../results/) |
| Composition | [Explicit graphs](../operations/adaptive/composition/) and named composition portfolios in `docs/` |
| Worker logs | [Adaptive logs](../run_logs/adaptive/) |
| Counted proof frontier | [Frontier](../docs/hutter_frontier.json) and [proof run ledger](../docs/hutter_run_ledger.json) |
| Generated operator report | [Status receipt](../docs/status_receipt.md) and its JSON companion; verify timestamp and process evidence |
| Atlas-Clockwork problem binding and activation | `docs/atlas_clockwork_seal_*.md` and [seal operations](../operations/atlas_clockwork_seal_v2/) |

## Evidence boundaries

Edit canonical records through the [workflow](../ADAPTIVE_WORKFLOW.md), then
regenerate snapshots. This view creates no registry, queue, verdict, or launch
authority. Completed jobs and reported passes alone do not establish scientific
success; missing metrics stay missing. Lineage uses explicit recorded references.

A driver's `program_size` and `hutter_score` can count only its local candidate
directory. Imported codec sources, runtimes, models and options may add required
bytes. Read the linked terminal accounting and validated reflection before
comparing package costs or choosing a descendant; a driver score is not a
complete submission certificate. The [package workflow](../ADAPTIVE_WORKFLOW.md#compose-prize-facing-evidence)
defines the separate package evidence.

Unreadable or oversized summaries remain visible as source issues. The generator
reads process metadata and may reuse HORIZON's existing operational receipt; it
does not read raw traces or active scientific outputs, take observer ownership,
or launch workers. See [AGENTS.md](../AGENTS.md) for operating rules.
