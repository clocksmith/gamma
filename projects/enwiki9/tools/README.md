# enwiki9 Tool Router

`tools/` is a stable compatibility surface. Tests, receipts, and operator
commands invoke these filenames directly, so existing tools are grouped by
purpose here instead of being mass-moved.

## Primary Entry Point

Use `enwiki9_lab.py` to propose and claim algorithms, create, clone, mutate,
queue, adaptively select gates, run parallel workers, inspect durable state,
and refresh generated views:

```bash
python3 projects/enwiki9/tools/enwiki9_lab.py --help
```

See `../ADAPTIVE_WORKFLOW.md` for the operating loop.

## Start Here

| Task | Entry point |
|---|---|
| Adaptive experiment loop | `enwiki9_lab.py` |
| Candidate revision and immutable blob binding | `enwiki9_candidate_revisions.py` |
| Terminal reflection and evidence-aware ranking | `enwiki9_reflections.py` |
| Objective and receipt validation | `research_contracts.py` |
| Frozen F/O DELTA-MIDAS residual attribution | `nncp_delta_midas_deep_residual.py` |
| Prospective decoder-visible DELTA-MIDAS probe | `nncp_delta_midas_decoder_feature_probe.py` |
| Current operator status | `enwiki9_status_receipt.py` |
| Candidate filesystem audit | `candidate_audit.py` |
| Candidate triage | `candidate_triage.py` |
| Normalize receipts and generated views | `enwiki9_normalize_receipts.py` |
| Run with process-tree resource guard | `run_with_rss_guard.py` |
| Record a driver result | `record_driver_result.py` |
| Decide or continue a cmix21 gate | `cmix21_gate_decider.py`, `cmix21_continue_active_gate.py` |
| Rebuild the run ledger | `backfill_run_ledger.py` |

## Filename Families

| Pattern | Purpose |
|---|---|
| `enwiki9_*`, `candidate_*`, `*_audit.py`, `*_ledger.py` | Status, inventory, evidence, and maintenance |
| `run_*`, `continue_*`, `seal_*`, `*_gate*.py` | Execution, continuation, proof sealing, and promotion gates |
| `fx2_*`, `cmix21_*`, `endpoint*` | FX2/cmix integration and endpoint experiments |
| `wrt_*` | WRT parsing, traces, transforms, and residual models |
| `wikiir_*` | Reversible WikiIR transforms and structural probes |
| `streaming_retrieval_*`, `*_shadow.py` | Retrieval and exact shadow evaluation |
| `page_*`, `*_teacher*`, `embedding_*` | Ordering and offline teacher discovery |
| `build_*`, `package_*` | Reproducible artifacts and source packaging |

The detailed per-file catalog and lock-safety notes are in
`../docs/tooling_inventory.md`.

## Placement Rules

- Keep established tool paths stable.
- Put generated probe outputs in `../results/probes/`.
- Put durable queue inputs in `../operations/queues/`.
- Put handoff artifacts in `../docs/handoffs/`.
- Put runtime logs and transient status snapshots in `../run_logs/`.
- Add every new tool to `docs/tooling_inventory.md`.
- State whether a tool can launch a compressor and which memory, process, and
  output-path guards it uses.

`nncp_delta_midas_deep_residual.py` cannot launch a compressor or teacher. It
reads two hash-bound retained traces, refuses to overwrite its result boundary,
and emits a zero-credit experiment receipt with a copy of the executed analyzer.
`nncp_delta_midas_decoder_feature_probe.py` likewise cannot launch a compressor
or teacher; it fits only its frozen train partition and emits sealed validation,
test, shifted-control, quantized-payload, and causal-feature evidence.
