# enwiki9 Agent Instructions

These instructions apply to `projects/enwiki9/`. Also obey
`../../AGENTS.md`.

## Main Focus

Continuously create, mutate, try, measure, track, and promote compression
algorithms through the adaptive workflow:

```text
ADAPTIVE_WORKFLOW.md
tools/enwiki9_lab.py
```

Use that workflow instead of creating ad hoc launch scripts, root-level queue
files, or chat-only experiment state.

## Start

From the Gamma repository root:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py status
sed -n '1,200p' projects/enwiki9/docs/status_receipt.md
```

Inspect live processes before source changes or heavy work:

```bash
pgrep -af 'enwiki9_lab|candidate_triage|run_with_rss_guard|projects/enwiki9/lib/driver.py|cmix21'
```

## Adaptive Loop

1. Analyze receipts and propose a target-bearing mechanism with byte leverage.
2. Claim the highest-value proposal and materialize a unique candidate.
3. Change one attributable mechanism per candidate when practical.
4. Queue the smallest missing exact gate.
5. Run independent small gates in parallel.
6. Serialize `10M`, `100M`, and `1G` work through
   `/tmp/enwiki9-heavy.lock`.
7. Let terminal batches refresh candidate inventory and reporting views.
8. Promote exact winners, explicitly retry infrastructure failures, mutate
   promising parents, and retire decisive misses.

Every mutation is a new candidate. Never edit source under a running or already
measured candidate.

## Proof Objective

The objective is a constructive official full-corpus score:

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
| Pending/running/terminal jobs | `operations/adaptive/<state>/` |
| Worker logs | `run_logs/adaptive/` |
| Exact candidate receipts | `results/<id>/` |
| Canonical run registry | `results/run_ledger.jsonl` |
| Generated lifecycle inventory | `candidate_inventory.json` |
| Source-bound proof frontier | `docs/hutter_frontier.json` and `docs/hutter_run_ledger.json` |
| Current operator status | `docs/status_receipt.md` |
| Atlas-Clockwork problem bank, binding audit, commitment, and activation | `docs/atlas_clockwork_seal_*.md` and `operations/atlas_clockwork_seal_v2/` |

Do not leave decisive commands, hashes, outcomes, or next actions only in chat.

Do not distribute `docs/atlas_clockwork_seal_problem_set.md` to candidates
unless `python3 tools/atlas_clockwork_seal.py verify --require-bound` reports
`VALID_BOUND`. Expert review of an `UNBOUND` draft is allowed.

## Algorithm And Evidence Recording Contract

- Record every meaningfully evaluated algorithm in `docs/research_register.md`,
  including ideas that are parked, merged, rejected before implementation, or
  retained only as an oracle. Give unmeasured ideas zero score credit.
- Use a dated machine-readable portfolio JSON when evaluating a batch of ideas.
  The portfolio is an index, not an operational queue or compression receipt.
- Materialize only actionable, falsifiable work with `enwiki9_lab.py propose`.
  Link the proposal's `--evidence` fields back to its research-register section,
  portfolio entry, predecessor receipt, or paper.
- Store every completed exact run under `results/<id>/`; ensure it appears in
  `results/run_ledger.jsonl`. Record decisive promotion, mutation, merge, park,
  or retirement conclusions back in `docs/research_register.md`.
- Update `docs/hutter_frontier.json` only for source-bound evidence. Oracles,
  proxies, causal shadows, and ideas receive zero score credit.
- Do not create a second algorithm registry, queue, or device-local notebook.
  Extend these canonical files and the adaptive workflow instead.

## Cross-Device Handoff

Git synchronizes durable research state; it does not synchronize live
processes, RAM, logs still being written, or `/tmp/enwiki9-heavy.lock`.

Before beginning work on another device:

```bash
cd /home/clocksmith/deco
./rdpull.sh
cd gamma
python3 projects/enwiki9/tools/enwiki9_lab.py status
```

Before launching a heavy gate, pull first, claim and queue the unique proposal
or candidate, and publish that ownership before another device can claim the
same work. Treat each host's heavy lock as local, not cluster-wide.

After a decisive run or research decision:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py refresh
cd /home/clocksmith/deco
./rdpush.sh
```

The handoff is complete only after the commit containing proposal state,
receipts, run-ledger rows, conclusions, and generated status is pushed.
Never infer that a process is active on another device from committed status;
inspect that host directly.

## Safety

- Do not launch competing heavy work without the heavy lock.
- Do not mutate candidate source beneath an active proof gate.
- Quarantine evidence with broken alignment, causality, replay, or provenance.
- Do not manufacture or silently drop missing receipt artifacts.
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
