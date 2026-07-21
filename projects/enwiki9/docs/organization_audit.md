# enwiki9 Organization Audit

This audit records organization state and cleanup obligations. It is not a
benchmark report and does not launch or require any scorer work.

## Snapshot

Current shallow workspace observations:

```text
program directories under programs/: 540
registered programs in index.json: 225
docs file entries under docs/: 30
tools files under tools/: 86
active: 24
candidate: 17
measured_negative: 77
blocked_dependency: 30
retired: 392
track_source_before_evolution: 2
```

Interpretation:

- candidate folders have outpaced the generated audit snapshot;
- generated inventory currently reports a different live candidate status split; refresh
  `candidate_inventory.json` when active gating work advances, then mirror those
  counts here.
- the PPMD-only ladder is retired, and its FXCM2/full-buffer replacement is
  also retired after the `100M` first archive missed the unified-executable
  screen by `149,143` bytes. No heavy target-bearing gate is active;
- live dirty-worktree counts belong in `docs/status_receipt.md`, not this stable
  organization snapshot;
- `tools/enwiki9_delayed_status_check.sh` now reports live process RSS,
  `cmix21_gate_decider.py` output, and any unguarded `cmix21-mmap-bin`
  process outside the RSS-guard tree.
- `docs/status_receipt.md` now reports current single-process RSS, process-tree
  RSS, decode progress from the staging file, and the single-process guard
  boundary distinction.

## Ownership Fixes Added

The following ownership documents now exist:

| File | Purpose |
|---|---|
| `PROJECT_ORGANIZATION.md` | Canonical map for docs, evidence, strategy, active proof lane, and update rules. |
| `docs/algorithm_cards.md` | Mechanism, score, proof-boundary, and next-action cards for the main algorithms. |
| `docs/best_results.md` | Generated compact top-results view by measured scope. |
| `docs/tooling_inventory.md` | Grouped inventory for `tools/` scripts and lock-safety expectations. |
| `docs/evidence_receipts.md` | Standard receipt schemas for operator status, gates, memory values, residuals, and official claims. |
| `docs/official_accounting_checklist.md` | Official score and promoted-candidate accounting checklist. |
| `docs/shadow_coder_spec.md` | Residual/SSE trace schema and validation contract. |
| `docs/residual_shadow_matrix.md` | Generated matrix of cached residual/SSE shadow receipts and constructive-proof status. |
| `docs/streaming_retrieval_mixer.md` | Generated causal sketch-retrieval algorithm, receipt schema, implementation queue, and kill gates. |
| `docs/streaming_retrieval_block_regime_audit.md` | Offline teacher-only SRSTC regression labels and weak-positive controls. |
| `docs/streaming_retrieval_block_teacher_manifest.jsonl` | All `4,000` block-gain labels and contiguous teacher splits; never a decoder-side lookup. |
| `tools/streaming_retrieval_shadow.py` | Exact-shadow SRSTC/sketch-retrieval scorer over cached residual traces. |
| `tools/streaming_retrieval_block_regime_audit.py` | Generates the teacher-only block audit and training manifest from complete receipt rows. |
| `tools/streaming_retrieval_continue_shadow.py` | Safe continuation helper that prioritizes the target-closing block-posterior replay and honors the cmix heavy lock by default. |
| `docs/embedding_teacher_rules.md` | Offline embedding-teacher boundaries and distilled-rule rules. |
| `docs/research_register.md` | Strategy and novel-algorithm register with promote and kill gates. |
| `docs/status_receipt.md` / `docs/status_receipt.json` | Generated one-page operator state from certificate, lock, gate, and RSS artifacts. |
| `docs/takeover_runbook.md` | Continuation procedure for active-run checks, result recording, and promotion decisions. |
| `tools/enwiki9_doc_lint.py` | Live documentation and claim-boundary lint now wired into receipt normalization. |

Entry points patched:

- `README.md` links to `PROJECT_ORGANIZATION.md`.
- `ALGORITHMS.md` links to the new organization and tooling docs.
- `CANDIDATES.md` delegates project-wide routing to
  `PROJECT_ORGANIZATION.md`.
- `docs/takeover_runbook.md` starts with `tools/enwiki9_status_receipt.py`.

## Remaining Cleanup Queue

### Candidate Registry

Problem:

```text
programs/ contains more candidate directories than index.json registers
```

Action:

```text
Use candidate_audit.py and candidate_triage.py after the active sidecar result
is recorded. Register, retire, or source-boundary-block each unregistered
folder.
```

### Generated Inventory

Problem:

```text
candidate_inventory.json and CANDIDATE_INVENTORY.md can become stale relative
to programs/ and results/.
```

Action:

```text
Refresh generated inventory only after the current active run has a recorded
result or failure receipt.
```

### cmix21 Memory-Value Table

Problem:

```text
PPMD cap rows are partly filled, but FXCM index, FXCM RCM, PAQ RCM, rolling
buffer, sparse-map, and mmap allocator rows are still pending.
```

Action:

```text
Fill memory-value rows only from exact same-scope evidence. Do not use archive
ceiling skips as if they were deterministic replay results.
```

### Residual/SSE Lane

Problem:

```text
Several tools exist, but proof acceptance requires a single trace schema and
block-level held-out criterion.
```

Action:

```text
Use docs/shadow_coder_spec.md as the gate. Do not promote residual/SSE ideas
without exact shadow bytes and counted code/table size.
Use docs/residual_shadow_matrix.md to separate positive measured or held-out
shadow rows from constructive certificates.
```

### Embedding-Teacher Lane

Problem:

```text
Embedding and hierarchical teacher tools can be misread as final compressor
payloads.
```

Action:

```text
Keep embeddings offline. Promote only deterministic distilled rules whose
bytes are counted and whose gains are exact.
```

### Public fx2-cmix Reproduction Lane

Problem:

```text
The public reproduction lane can be confused with the active target-bearing
path.
```

Action:

```text
Keep it as an accounting and reproducibility anchor. Do not substitute it for
a target-bearing candidate that has cleared cumulative counted economics.
```

## Claim Hygiene

Allowed:

```text
The candidate passed an exact prefix replay at scope N.
The candidate failed the RSS guard by X KiB.
The candidate has first-pass archive bytes but no replay result yet.
```

Forbidden:

```text
The project hit 10.95%.
```

unless:

```text
scope_bytes == 1,000,000,000
official_score_bytes <= 109,500,000
roundtrip_ok == true
```
