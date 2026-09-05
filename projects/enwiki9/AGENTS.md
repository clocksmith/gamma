# enwiki9 Agent Instructions

These operating rules apply throughout `projects/enwiki9/`, including `ledger/`
and `workbench/`. Also obey [Gamma's instructions](../../AGENTS.md); a nearer
`AGENTS.md` may narrow them for its directory.

## Component Intent

Before modifying a file, read the `CATSCAN.md` chain from the repository root
to the target directory. Treat Target, Authority, Invariants, Acceptance, and
Non-goals as implementation constraints. A child may narrow its parent but may
not contradict it. Boundary changes require the affected charter to change
with the implementation; algorithms remain free inside those constraints.

## Start Here

Create, mutate, measure, track, and promote compression algorithms through
[ADAPTIVE_WORKFLOW.md](ADAPTIVE_WORKFLOW.md) and `tools/enwiki9_lab.py`.

| Document | Role |
|---|---|
| [README.md](README.md) | Project overview and directory map |
| This `AGENTS.md` | Agent operating rules and recording obligations |
| [ledger/README.md](ledger/README.md) | Browse algorithms, mixes, lineage, jobs, and evidence |
| [workbench/README.md](workbench/README.md) | Research loop and [reusable prompts](workbench/PROMPTS.md) |
| [ADAPTIVE_WORKFLOW.md](ADAPTIVE_WORKFLOW.md) | Exact commands, contracts, and lifecycle transitions |

Commands below run from `gamma/projects/enwiki9/`:

```bash
python3 tools/enwiki9_lab.py status
sed -n '1,200p' docs/status_receipt.md
```

Inspect live processes before source changes or resource-intensive work:

```bash
pgrep -af 'enwiki9_lab|candidate_triage|run_with_rss_guard|projects/enwiki9/lib/driver.py|cmix21'
```

Resolve important claims through linked source records. Rebuild the local
ledger with `python3 tools/enwiki9_ledger.py` after recording changes; it is a
disposable index with no queue, evidence, or monitoring authority. Keep current
measurements and job status in records and generated views; keep READMEs and
agent instructions focused on stable navigation and rules.

## Adaptive Loop

1. Analyze receipts and propose a target-bearing mechanism with byte leverage.
2. Claim the highest-value proposal and materialize a unique candidate.
3. Change one attributable mechanism per candidate when practical.
4. Queue the smallest missing exact gate.
5. Run independent gates in parallel when contracts and host resources permit;
   preserve existing claims, leases, and sole observer ownership.
6. Give every run a unique job ID, output path, and explicit resource guard.
7. Validate terminal evidence and record the required reflection before changing
   scientific status; refresh candidate inventory, reports, and the local ledger.
8. Promote exact winners, explicitly retry infrastructure failures, mutate
   promising parents, and retire decisive misses.

Every mutation is a new candidate. Never edit source under a running, sealed,
or already measured candidate. Use the adaptive workflow for execution and
state transitions; do not create ad hoc launchers or root-level queue files.

## Proof Objective

The canonical objective contract is
`contracts/research/v1/objective-contract.json`. The objective is a
constructive official full-corpus score:

```text
score <= 105,000,000 bytes
scope_bytes == 1,000,000,000
roundtrip_ok == true
```

Forecasts, prefixes, partial archives, oracles, teachers, and shadows guide
search but are not the objective.

Before promoting to a larger gate, account for program/source/model/table bytes,
measured archive bytes, memory, runtime, remaining target debt, and a numeric
kill condition. Compare only identical corpus populations and scopes.

## Durable State

| State | Owner |
|---|---|
| Every considered algorithm, composition, merge, park, rejection, and conclusion | `docs/research_register.md` |
| Machine-readable batch evaluations and ranked portfolios | `docs/*portfolio*.json` and their named companion registries |
| Algorithm proposals | `operations/adaptive/proposals/` |
| Candidate source and hypothesis | `programs/<id>/` |
| Mutation lineage | `operations/adaptive/mutations.jsonl` |
| Frozen experiments, source revisions, and terminal reflections | `operations/adaptive/experiments/`, `operations/adaptive/candidate-revisions/`, and `operations/adaptive/reflections/` |
| Explicit mechanism combinations | `operations/adaptive/composition/` and named composition portfolios |
| Pending/running/terminal jobs | `operations/adaptive/<state>/` |
| Worker logs | `run_logs/adaptive/` |
| Exact candidate receipts | `results/<id>/` |
| Canonical run registry | `results/run_ledger.jsonl` |
| Generated lifecycle inventory | `candidate_inventory.json` |
| Source-bound proof frontier | `docs/hutter_frontier.json` and `docs/hutter_run_ledger.json` |
| Current operator status | `docs/status_receipt.md` |
| Atlas-Clockwork problem bank, binding audit, commitment, and activation | `docs/atlas_clockwork_seal_*.md` and `operations/atlas_clockwork_seal_v2/` |

Record every meaningfully evaluated algorithm and decisive conclusion, including
merges, parked ideas, preimplementation rejections, and oracle-only work. Use a
dated machine-readable portfolio for a batch of ideas; portfolios grant no queue
or score authority. Materialize only actionable, falsifiable proposals. Link their
`--evidence` fields to immutable supporting artifacts as required by the workflow;
retain the register, portfolio, predecessor, and paper references that explain them.

Every completed exact run must have retained artifacts and a canonical run-ledger
entry. Record its promotion, mutation, retry, merge, park, or retirement conclusion
in the research register. Update the proof frontier only from source-bound evidence;
ideas, oracles, proxies, and causal shadows receive zero score credit. A composition
needs its own joint replay; never add component forecasts as an earned gain.

Keep decisive commands, hashes, outcomes, and next actions in these canonical
records. Do not create a second algorithm registry, queue, or device-local notebook.

## Cross-Device Handoff

Git synchronizes durable research state; it does not synchronize live
processes, RAM, or logs still being written.

Before beginning work on another device, pull through the workspace wrapper,
then inspect that host. Starting from this project directory:

```bash
cd ../../..
./rdpull.sh
cd gamma/projects/enwiki9
python3 tools/enwiki9_lab.py status
```

Before launching a resource-intensive gate, pull first, claim and queue the
unique proposal or candidate, and publish that ownership before another device
can claim the same work. Inspect host resources and use a unique output path.

After a decisive run or research decision:

```bash
python3 tools/enwiki9_lab.py refresh
python3 tools/enwiki9_ledger.py
cd ../../..
./rdpush.sh
```

The handoff is complete only after the commit containing proposal state,
receipts, run-ledger rows, conclusions, and generated status is pushed.
Never infer that a process is active on another device from committed status;
inspect that host directly.

## Safety

- Bound each concurrent run with explicit memory, process, and output paths.
- Do not mutate candidate source beneath an active proof gate.
- Quarantine evidence with broken alignment, causality, replay, or provenance.
- Do not manufacture or silently drop missing receipt artifacts.
- Do not distribute `docs/atlas_clockwork_seal_problem_set.md` to candidates
  unless `python3 tools/atlas_clockwork_seal.py verify --require-bound` reports
  `VALID_BOUND`. Expert review of an `UNBOUND` draft is allowed.
- Do not auto-install models or dependencies.
- Follow `../../EMOJI.md`; do not add emojis.
- Run tests only when the user requests them.

## Status Replies

When explicitly asked for Hutter status, include the `105,000,000` byte and
`10.5000000%` targets, the verified full-1G score or `unknown`, the best counted
forecast and signed target distance, and the active gate's receipt-backed
scope, progress, guard state, and terminal status.

Historical detailed instructions are preserved at
`docs/reference/legacy_instructions/AGENTS_20260724.md`.
