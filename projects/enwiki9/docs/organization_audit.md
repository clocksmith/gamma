# enwiki9 Organization Audit

This audit defines organization invariants and cleanup ownership. It does not
duplicate live candidate, file, or status counts.

## Canonical Inventory

`candidate_inventory.json` and `CANDIDATE_INVENTORY.md` are the generated
filesystem and lifecycle inventory. Refresh both after structural or candidate
metadata changes:

```bash
python3 tools/candidate_audit.py --write
```

Read current counts directly from the generated JSON:

```bash
jq '.summary' candidate_inventory.json
```

Do not paste those counts into this document. That was the source of the
previous stale `docs/` and `tools/` totals.

## Organization Invariants

- The root contains policy, canonical routing documents, certificates,
  generated canonical inventories, and supported entry points only.
- Historical research notes belong in
  `docs/research/historical_candidate_notes/`.
- Durable handoffs belong in `docs/handoffs/`.
- Diagnostic outputs that are not candidate results belong in
  `results/probes/`.
- Durable operator queue inputs belong in `operations/queues/`.
- Transient logs and status snapshots belong in `run_logs/`.
- Runnable utilities belong in `tools/`.
- Tool defaults write to those owning directories, not the project root.
- `index.json` is curated; `candidate_inventory.json` covers the full program
  population. Their program counts are not expected to match.
- Every program directory must have an inventory lifecycle classification even
  when it is intentionally absent from `index.json`.

## Tooling Layout

Existing files under `tools/` retain stable flat paths because tests, receipts,
and operator commands invoke them directly. `tools/README.md` is the short
purpose-based router, and `docs/tooling_inventory.md` is the detailed catalog.

This is an explicit compatibility boundary, not an invitation to add unrelated
scripts without documentation. New tools must be added to the routing catalog
and must declare whether they can launch a heavy codec.

## Candidate Registry

The previous audit described every program missing from `index.json` as cleanup
debt. That was too broad. Historical negative, retired, blocked, and exploratory
programs may remain outside the curated public registry.

The actionable defect is one of:

- a program directory has no lifecycle status;
- a measured public program should be in `index.json` but is absent;
- an `index.json` entry has no corresponding program directory;
- generated inventory facts do not match candidate metadata.

Use `tools/candidate_audit.py` and `tools/candidate_triage.py` to resolve those
states. Do not bulk-register historical candidates merely to equalize counts.

## Claim And Runtime Boundaries

Organization cleanup must not mutate candidate source, result receipts, or
active gate artifacts. The target claim remains valid only when:

```text
scope_bytes == 1,000,000,000
official_score_bytes <= 109,500,000
roundtrip_ok == true
```

Runtime status belongs in `docs/status_receipt.md`,
`docs/status_receipt.json`, and `run_logs/`; it does not belong in this stable
audit.
