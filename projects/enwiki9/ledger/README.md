# Research ledger

[Open the ledger](index.html) · [JSON export](ledger.json) ·
[Workbench](../workbench/README.md) · [Prompts](../workbench/PROMPTS.md)

One searchable view of existing research records. Rebuild it from
`gamma/projects/enwiki9/`:

```bash
python3 tools/enwiki9_ledger.py
```

The project's [AGENTS.md](../AGENTS.md) applies here. Edit canonical records
through the workbench workflow; regenerate `index.html` and `ledger.json`
instead of editing those snapshots. Both generated files are local and ignored
by Git, so rebuild them on each device.

Open `ledger/index.html` directly in a browser. No server, dependencies, or
network are required. `--summary` prints coverage without writing files.

The browser has five views:

- **Algorithms:** candidates, proposals, portfolio ideas, and retained result
  collections. Filter their recorded status or kind; open an entry for its
  parents, children, evidence links, notes, and complete indexed run history.
- **Running & queued:** running, waiting, and held job records. Process
  observations name their host and timestamp. A source process and its observer
  can have separate jobs; their count is not a compressor count.
- **Results:** driver receipts, terminal jobs, and retained report summaries,
  preserving their scope, units, and recorded verdicts.
- **Mixes:** recorded composition graphs and portfolio combinations, plus a
  separate search grouping of candidates explicitly described as mixtures.
- **Research notes:** decisions from the current register, its archives, and
  historical candidate notes, with links back to their full text.

Search within each view. Candidate details retain their full indexed history
even when a search is active. Lists are paginated. Open source links to resolve
a claim before acting on it.

| Record | Canonical source |
| --- | --- |
| Candidate identities and source | [Programs](../programs/), [curated registry](../index.json), [filesystem audit](../candidate_inventory.json) |
| Lineage | [Mutation records](../operations/adaptive/mutations.jsonl), [candidate revisions](../operations/adaptive/candidate-revisions/) |
| Ideas and proposals | [Research register](../docs/research_register.md), named portfolio JSONs in `docs/`, [proposals](../operations/adaptive/proposals/) |
| Jobs and decisions | [Adaptive state](../operations/adaptive/), [reflections](../operations/adaptive/reflections/) |
| Measurements | [Run ledger](../results/run_ledger.jsonl), [retained results](../results/) |
| Composition | [Explicit graphs](../operations/adaptive/composition/) and named composition portfolios in `docs/` |

The generated HTML and JSON are disposable local snapshots, never another
registry or queue. They do not validate evidence or authorize a transition.
Missing metrics stay missing; completed jobs and reported passes do not imply
scientific success. Lineage uses explicit references, not library dependencies
or guesses from names. An entry without a summary still links its retained
artifact directory; oversized or unreadable summary records are listed as source
issues. Raw traces and active scientific outputs are not read.

Rebuild after updating canonical records. The generator reads process metadata
once and may reuse the existing HORIZON observer's operational receipt; it does
not take monitoring ownership or start a worker. See
[the workbench](../workbench/README.md) for making and recording changes.
