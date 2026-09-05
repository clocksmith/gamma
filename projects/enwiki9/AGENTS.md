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
python3 tools/enwiki9_lab.py start
python3 tools/enwiki9_lab.py records --view runs --state running
```

When the user says "go", follow [workbench/README.md](workbench/README.md):
inspect ownership and relevant prior evidence, choose one justified benchmark,
simulation, or research question, execute authorized work, record the outcome,
and continue. A held gate can coexist with independent research. Do not turn a
nonterminal wait or the entire historical review backlog into a blanket stop.
Use `records --search QUERY`, `records --candidate ID`, and
`records --view reviews` to retrieve bounded, source-linked context. Reviews
separate bound jobs from legacy records; no automatic scientific verdict is given.

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
`contracts/research/v2/objective-contract.json`. The objective is a
constructive official full-corpus score:

```text
score <= 99,000,000 bytes
scope_bytes == 1,000,000,000
roundtrip_ok == true
```

The 99M target is provisional engineering economics. The unchanged v1 objective
and its 105M milestone retain their historical digests. Consult
[competitive provenance](operations/provenance/competitive_frontier_v1.json) for
published submissions, official versus contingent thresholds, and unresolved
committee accounting. Endpoint428's 109,389,323-byte forecast has 10,389,323
bytes of planning debt; that is not a measured full-corpus deficit.

Forecasts, prefixes, partial archives, oracles, teachers, and shadows guide
search but are not the objective.

Before promoting to a larger gate, account for program/source/model/table bytes,
measured archive bytes, memory, runtime, remaining target debt, and a numeric
kill condition. Compare only identical corpus populations and scopes.

## Discovery and Qualification

Discovery uses an explicit CPU set, memory, scratch and elapsed-time stop through
the existing queue. It may share a host under admission controls while preserving
HORIZON's sole observer. Concurrent timing is diagnostic. Unknown occupancy or a
missing controller grants no launch permission. Qualification requires isolated
timing, hardware calibration, and complete phase resource evidence; a future full
corpus certificate is not a prerequisite for implementing its candidate.

Freeze the hypothesis, parent, changed mechanism, development budget, selection
population, sealed confirmation population and stop rule before measuring.
Explicitly budgeted parameter selection is allowed on development data; freeze
before confirmation. Preserve failed configurations and explain their scope.
Economic stops are budget decisions; certified futility requires a proved bound.
Require validated reflections for selected ancestry, then review unrelated backlog
incrementally. Retired Fiber-FOSSIL exact retrieval is not a fresh candidate when
renamed. HARM edit alignment and deep-MIDAS require their own evidence.

Use synthetic checks, 250KB/1MB exact archives, opening and distant 10MB,
100MB, then 1GB. History-dependent mechanisms need state-warm populations;
a cold prefix cannot certify their mature-history behavior. Cache builds and
parent traces only with matching frontend, source, state and coordinate identities.
HORIZON's original scientific threshold stays fixed. Recovered probabilities
cannot restore missing continuous runtime or memory evidence.

## Record The Work

Use the [canonical record map](ledger/README.md#record-map) for storage locations
and the [operating manual](workbench/README.md) for research, benchmark, simulation,
and result-recording commands. Candidate source, measured artifacts, and frozen
contracts keep their evidence paths; organize discovery through the existing index.

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
- Standing permission covers source inspection, research, synthetic fixtures, targeted regression tests, the release canary, and independently bounded discovery gates on assigned resources. Large launches and dependency/model installation still require explicit user authorization.

## Status Replies

When explicitly asked for Hutter status, include the `99,000,000` byte and
`9.9000000%` targets, the verified full-1G score or `unknown`, the best counted
forecast and signed target distance, and the active gate's receipt-backed
scope, progress, guard state, and terminal status.

Historical detailed instructions are preserved at
`docs/reference/legacy_instructions/AGENTS_20260724.md`.
