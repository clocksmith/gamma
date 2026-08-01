# enwiki9 Takeover Runbook

This page is the current operator orientation. Generated state remains
authoritative; do not copy live process, queue, or candidate counts into this
document.

## Establish Current State

From the Gamma repository root:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py status
sed -n '1,240p' projects/enwiki9/docs/status_receipt.md
pgrep -af 'enwiki9_lab|candidate_triage|run_with_rss_guard|projects/enwiki9/lib/driver.py|cmix21'
```

Read `candidate_inventory.json` for lifecycle state,
`results/run_ledger.jsonl` for exact run history, and
`docs/hutter_frontier.json` for the source-bound forecast frontier. A persisted
queue or guard receipt is not live without an owning process.

## Proof Objective

The only winning receipt has all three properties:

```text
score <= 108,000,000 bytes
scope_bytes == 1,000,000,000
roundtrip_ok == true
```

Prefix results, forecasts, teachers, oracles, and shadows have zero proof
credit. Account for program, model, table, framing, finalization, archive,
memory, runtime, roundtrip, and deterministic replay before promotion.

## Continue Work

Use `tools/enwiki9_lab.py` and `ADAPTIVE_WORKFLOW.md`. Claim a unique proposal,
materialize a new candidate, queue the smallest missing exact gate, and record
the terminal conclusion in `docs/research_register.md`. Never edit a measured
or running candidate.

All 10M, 100M, and 1G work must use `/tmp/enwiki9-heavy.lock`. Inspect process
ownership before launch. After terminal work, run:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py refresh
```

Atlas-Clockwork material is not distributable unless:

```bash
python3 projects/enwiki9/tools/atlas_clockwork_seal.py verify --require-bound
```

returns `VALID_BOUND`.

## Current Decision Boundary

The verified full-1G score is unknown. The source-bound planning forecast is
`109,389,323`, which is `1,389,323` bytes above the design target and is not a
proof. Route D timestamp-envelope Q0 is terminal negative. Route C is blocked
until an independently reproducible under-target full-corpus teacher exists
with complete eligibility evidence. The generated status receipt supersedes
these statements whenever newer exact artifacts land.
