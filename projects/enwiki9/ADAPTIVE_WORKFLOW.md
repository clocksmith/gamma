# enwiki9 Adaptive Workflow

This is the primary operating workflow for enwiki9 research.

The loop is:

```text
analyze evidence
-> propose and rank a mechanism
-> claim and develop
-> create or mutate
-> queue
-> run the smallest missing exact gate
-> record result and lifecycle state
-> refresh inventories and reports
-> promote, retry explicitly, mutate, or retire
```

Use `tools/enwiki9_lab.py` for this loop. Do not build separate ad hoc launchers
or keep experiment state only in chat.

## Discover And Propose Algorithms

Algorithm discovery is separate from gate discovery. Record a proposal before
writing source:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py propose <proposal_id> \
  --title "<mechanism>" \
  --hypothesis "<falsifiable hypothesis>" \
  --mechanism-class endpoint \
  --expected-savings-bytes <bytes> \
  --max-program-bytes <bytes> \
  --promotion "<numeric promotion condition>" \
  --kill "<numeric kill condition>" \
  --evidence <receipt-or-document>
```

Mechanism classes are `substrate`, `endpoint`, `representation`, and `coder`.
Keep orthogonal proposals active rather than collapsing search into one tuning
ladder.

List and claim proposals:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py proposals
python3 projects/enwiki9/tools/enwiki9_lab.py claim <proposal_id> --owner <owner>
```

Materialize a claimed proposal as a candidate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py develop \
  <proposal_id> <candidate_id>
```

Proposal state is durable under `operations/adaptive/proposals/`. Developing a
proposal records its candidate ID and mutation lineage.

## Create

Create a blank candidate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py new <candidate_id> \
  --hypothesis "<falsifiable hypothesis>"
```

This creates:

```text
programs/<candidate_id>/program.py
programs/<candidate_id>/meta.json
```

Implement `compress(data)` and `decompress(archive)` in `program.py`.

## Mutate

Every mutation gets a new candidate ID. Never mutate an active or previously
measured candidate in place.

Clone a parent:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<one changed mechanism and expected byte effect>"
```

For a small deterministic source mutation:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<hypothesis>" \
  --replace 'OLD_TEXT=NEW_TEXT'
```

The clone removes inherited measurements and records the parent, hypothesis,
creation event, and source replacements in
`operations/adaptive/mutations.jsonl`.

## Queue

Queue an explicit gate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py enqueue <candidate_id> \
  --gate-size 1000000 \
  --purpose candidate \
  --tag <lane>
```

Create or mutate and immediately queue:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py mutate <parent_id> <new_id> \
  --hypothesis "<hypothesis>" \
  --enqueue
```

Jobs move atomically through:

```text
operations/adaptive/pending/
operations/adaptive/running/
operations/adaptive/completed/
operations/adaptive/failed/
operations/adaptive/cancelled/
```

Each candidate-and-scope pair runs once unless an operator explicitly uses
`--force`.

## Adaptive Gate Discovery

Preview the next missing exact gate for eligible candidates:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py discover-gates --dry-run
```

Queue those gates:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py discover-gates
```

The exact gate ladder is:

```text
1K -> 250K -> 1M -> 10M -> 100M -> 1G
```

A scope counts as passed only when candidate metadata records exact roundtrip
and deterministic replay. Adaptive discovery selects the next larger scope; it
does not infer success from forecasts, partial archives, or process state.

## Run

Run one available batch:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py run --max-workers 4
```

Continuously discover and run work on demand:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py run \
  --adaptive \
  --continuous \
  --max-workers 4 \
  --min-free-mib 4096
```

The runner adapts to current one-minute system load and available memory before
claiming a batch. Small independent gates may run in parallel. Gates at `10M`
or larger default to `--respect-heavy-lock` and serialize through
`/tmp/enwiki9-heavy.lock`.

After each terminal batch, the runner serially refreshes:

```text
candidate_inventory.json
CANDIDATE_INVENTORY.md
results/run_ledger.jsonl-derived views
evidence and best-result views
memory and residual reports
artifact fingerprint audit
status receipt
```

Worker output is stored in `run_logs/adaptive/<job_id>.log`.

## Observe And Control

Show current jobs, recent outcomes, load, and available memory:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py status
```

Cancel a pending job:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py cancel <job_id>
```

Refresh generated views without launching a gate:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py refresh
```

Stop a continuous runner with the normal process interrupt. Pending and
terminal job records remain durable.

## Promotion And Kill Rules

- Start with the smallest decisive gate.
- State the hypothesis, baseline, expected byte leverage, promotion condition,
  and kill condition in candidate metadata.
- Promote only exact roundtrip and deterministic evidence at the measured
  scope.
- Before a larger gate, include counted program cost and remaining target debt.
- A failed implementation retires that candidate, not the entire algorithm
  family.
- A retry requires `--force` and a recorded reason; a source change requires a
  new candidate ID.
- Never edit candidate source underneath a running job.
- Never treat a partial archive, forecast, oracle, teacher, or shadow result as
  a full official score.

## Source Of Truth

| Question | Source |
|---|---|
| What algorithms are proposed or claimed? | `operations/adaptive/proposals/` |
| What work is queued or running? | `operations/adaptive/<state>/` |
| How was a candidate derived? | `operations/adaptive/mutations.jsonl` and `programs/<id>/meta.json` |
| What did a worker emit? | `run_logs/adaptive/<job_id>.log` |
| What exact run was recorded? | `results/<id>/` and `results/run_ledger.jsonl` |
| What is each candidate's lifecycle? | `candidate_inventory.json` |
| What is the current proof boundary? | `docs/status_receipt.md` and `UPPER_BOUND_CERTIFICATE.md` |
