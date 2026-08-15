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
| Project-local Python source closure | `enwiki9_python_source_closure.py` |
| Terminal reflection and evidence-aware ranking | `enwiki9_reflections.py` |
| Objective and receipt validation | `research_contracts.py` |
| Count and stage a dependency closure | `enwiki9_dependency_closure.py` |
| Sealed full-1G package replay | `enwiki9_clean_room_replay.py` |
| Release evidence router | `enwiki9_release_receipts.py` |
| Frozen F/O DELTA-MIDAS residual attribution | `nncp_delta_midas_deep_residual.py` |
| Prospective decoder-visible DELTA-MIDAS probe | `nncp_delta_midas_decoder_feature_probe.py` |
| Direct-F32 DELTA-MIDAS named-gradient retry | `nncp_delta_midas_named_midpoint_gradient_q3.py` |
| Current operator status | `enwiki9_status_receipt.py` |
| Candidate filesystem audit | `candidate_audit.py` |
| Candidate triage | `candidate_triage.py` |
| Normalize receipts and generated views | `enwiki9_normalize_receipts.py` |
| Run with process-tree resource guard | `run_with_rss_guard.py` |
| Record a driver result | `record_driver_result.py` |
| Decide or continue a cmix21 gate | `cmix21_gate_decider.py`, `cmix21_continue_active_gate.py` |
| Rebuild the run ledger | `backfill_run_ledger.py` |
| Freeze a predicate-preserving implementation retry | `enwiki9_freeze_implementation_retry.py` |

New implementation retries should use `--strict-output-manifest` and declare
each newly retained artifact with `--additional-output`. The frozen contract
then requires its terminal result to bind every declared output except the
result itself exactly once. Python runners should also use
`--bind-python-source-closure`; the freezer hashes every project-local imported
module into the prospective input manifest and names the runner and materializer
as closure roots. An implementation-only retry may retain extra diagnostic
observations with `--additional-measurement ID=UNIT=DEFINITION`; this does not
change the inherited promotion or kill predicates.

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

`nncp_delta_midas_named_midpoint_gradient_q3.py` launches the closed NNCP
teacher twice and is zero-credit attribution work. Run it only through a
revision-bound `enwiki9_lab.py enqueue-tool` job wrapped by
`run_with_rss_guard.py`; the experiment must declare its candidate result tree
as guarded scratch. Its q3 materializer cannot launch a process and changes only
the named-gradient squared-energy reduction. Native stderr streams directly to
the declared per-encode log, so live progress and failures remain inspectable.

`enwiki9_python_source_closure.py` cannot launch a process. It recursively
resolves imports that exist under `tools/`, emits their paths and SHA-256
digests, and lets multi-module experiment runners use the same prospectively
declared source set in their terminal source package. Non-Python data inputs
remain explicit additions to the experiment and package.

`enwiki9_dependency_closure.py` cannot launch a compressor. It copies one exact
candidate tree into a new bundle, rejects symlinks and special files, hashes and
counts every member, binds explicit dependencies and SPDX identifiers, and
validates the resulting manifest.

`enwiki9_clean_room_replay.py` launches only the manifest's frozen commands. It
uses these placeholders: `{package}`, `{entry_point}`, `{corpus}`, `{archive}`,
`{restored}`, and `{scratch}`. Build and decode commands cannot contain
`{corpus}`. Compression must name `{corpus}` and `{archive}`; decompression must
name `{archive}` and `{restored}`. The tool builds three fresh copies in sealed
bubblewrap namespaces, exposes the corpus only to the two compression runs,
uses `taskset` plus `run_with_rss_guard.py` for the three runtime phases, and
retains a fail-closed diagnostic attempt if execution cannot compose a receipt.
`enwiki9_release_receipts.py` cannot launch a compressor. It discovers only the
canonical `results/<candidate>/release/<receipt>/` layout and regenerates a
structure-only index; a release claim must still validate every referenced file.
