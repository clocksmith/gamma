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
score <= 109,000,000 bytes
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
| Algorithm proposals | `operations/adaptive/proposals/` |
| Candidate source and hypothesis | `programs/<id>/` |
| Mutation lineage | `operations/adaptive/mutations.jsonl` |
| Pending/running/terminal jobs | `operations/adaptive/<state>/` |
| Worker logs | `run_logs/adaptive/` |
| Exact candidate receipts | `results/<id>/` |
| Canonical run registry | `results/run_ledger.jsonl` |
| Generated lifecycle inventory | `candidate_inventory.json` |
| Current operator status | `docs/status_receipt.md` |

Do not leave decisive commands, hashes, outcomes, or next actions only in chat.

## Safety

- Do not launch competing heavy work without the heavy lock.
- Do not mutate candidate source beneath an active proof gate.
- Quarantine evidence with broken alignment, causality, replay, or provenance.
- Do not manufacture or silently drop missing receipt artifacts.
- Do not auto-install models or dependencies.
- Follow `../../EMOJI.md`; do not add emojis.
- Run tests only when the user requests them.

## Status Replies

When explicitly asked for Hutter status, include the `109,000,000` byte and
`10.9500000%` targets, the verified full-1G score or `unknown`, the best counted
forecast and signed target distance, and the active gate's receipt-backed
scope, progress, guard state, and terminal status.

Historical detailed instructions are preserved at
`docs/reference/legacy_instructions/AGENTS_20260724.md`.
