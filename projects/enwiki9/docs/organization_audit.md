# enwiki9 Organization Audit

This living guide defines organization invariants and cleanup ownership. The
dated scorecard below records an audit, not live candidate or host status.

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

Organization cleanup must preserve sealed candidate source, result receipts,
and active gate artifacts. The [active objective](../contracts/research/v2/objective-contract.json)
defines the target and required evidence; historical objective bindings remain
unchanged. [Competitive provenance](../operations/provenance/competitive_frontier_v1.json)
separates that engineering objective from accepted prize thresholds. Use the
[package procedure](../ADAPTIVE_WORKFLOW.md#compose-prize-facing-evidence) for
counting, exact reconstruction, deterministic replay, and resource qualification.

Runtime status belongs in `docs/status_receipt.md`,
`docs/status_receipt.json`, and `run_logs/`; it does not belong in this stable
audit.

## Search What Experiments Taught Us

Use the existing entry point and canonical record projections:

```bash
python3 tools/enwiki9_lab.py start
python3 tools/enwiki9_lab.py records --view runs --search 'MECHANISM' --limit 10
python3 tools/enwiki9_lab.py records --candidate CANDIDATE --limit 10
```

Run searches include recorded lessons, localized causes, retired dimensions,
uncertainties, and next actions. Candidate detail includes linked reflection
history with the original scope and classifications. Default algorithm search
also matches that history. Search does not validate a reflection: invalid,
unknown, and unreviewed evidence remains labeled, and source links remain the
authority. Use `--offset` to page run records.

The working loop is ownership and history -> bounded experiment -> execution ->
validated reflection -> recorded decision -> next experiment. The
[command manual](../ADAPTIVE_WORKFLOW.md) owns the commands; the
[record map](../ledger/README.md#record-map) owns storage guidance.

## Organization Scorecard: 2026-09-06

These subjective baseline scores describe the read-only audit at
`6b161145db8d18c29114259c07387767e40297ba`, before the reflection-search fix.
Zero means unusable; ten means clear and maintainable. Read current counts from
the generated inventory instead of treating this assessment as live status.

| Metric | Score / 10 | Evidence and implication |
| --- | ---: | --- |
| Onboarding simplicity | 6 | [README](../README.md) is compact; the [manual](../ADAPTIVE_WORKFLOW.md) still presents many separate lifecycle operations. |
| Canonical-record clarity | 7 | The [record map](../ledger/README.md#record-map) distinguishes authority and projections; this guide previously copied a stale success condition. |
| Duplication management | 4 | The [tool catalogue](tooling_inventory.md) exposes many historical versions; identical wrappers and retained controls require provenance before consolidation. |
| Ability to evolve | 5 | [Immutable revisions](../operations/adaptive/candidate-revisions/) preserve replay; broad source closures encourage new adapters for operational changes. |
| Experiment-loop simplicity | 3 | The [workflow](../ADAPTIVE_WORKFLOW.md) still separates setup, terminal normalization, reflection, conclusions, and report refresh. |
| Historical discoverability | 6 | [Register archives](research_register/README.md) and the [ledger](../ledger/README.md) expose history; reflection lessons were absent from search. |
| Evidence integrity | 8 | [Frozen comparisons](../operations/adaptive/experiments/) retain source and control bindings; selected ancestry still requires validated reflections. |

The baseline average is 5.6/10. Git object identities showed that much apparent
duplication consists of immutable snapshots, controls, and independent repeats.
Identical files do not imply interchangeable candidates or disposable evidence.
Keep their paths stable; reuse maintained helpers when creating successors.

## Action Summary

1. Make recorded learning searchable through the existing ledger. The reflection
   projection now includes lessons, causes, retired dimensions, uncertainties,
   and next actions. [Navigation fixtures](../tests/test_enwiki9_ledger_navigation.py)
   cover searches, candidate history, pagination, and invalid or missing evidence.
2. Add an opt-in terminal-record transaction to the existing driver-result
   recorder. Validate a closed job and declared result index, use distinct arm
   identities, append idempotently, and reuse reflection validation. Test receipt
   replacement, duplicate calls, interruption, concurrent appends, live jobs,
   and missing evidence before adopting it.
3. Separate routine report refresh from complete historical audits in the
   existing normalizer. Test generator selection, stale-view disclosure, and
   failure propagation. `enwiki9_lab.py refresh` runs `candidate_audit.py`, and
   `enwiki9_status_receipt.py` invokes it again; reuse a verified audit snapshot
   within one refresh instead of repeating that filesystem scan.

The latter two items are recommendations. Preserve immutable source, historical
failures, and evidence paths. Improve the shared tools and generated projections
without adding a registry, queue, or another mandatory planning document.
