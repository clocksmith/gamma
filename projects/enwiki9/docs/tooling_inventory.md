# enwiki9 Tooling Inventory

This inventory groups `projects/enwiki9/tools/` by purpose. It is a map for
maintenance and handoff, not a claim that every script is current.

## Heavy-Gate And Driver Support

These scripts can interact with scoring or guard infrastructure. Treat them as
runner-adjacent.

| Tool | Purpose |
|---|---|
| `run_with_rss_guard.py` | Wraps commands with RSS sampling and guard enforcement; writes live and final guard JSON. |
| `record_driver_result.py` | Records driver/guard evidence into candidate meta rows, including receipt paths, byte sizes, modified UTC stamps, and SHA-256 fingerprints. |
| `cmix21_gate_decider.py` | Reads cmix21 driver and RSS guard receipts, prints the next safe action, and emits terminal apply commands for pass, RSS failure, and non-promotable terminal failures. |
| `cmix21_continue_active_gate.py` | Finds the certificate active gate, calls `cmix21_gate_decider.py`, and optionally applies only terminal actions: pass promotion, RSS lower packaging, or non-promotable failure recording. |
| `cmix21_memory_valve_report.py` | Generates the PPMD cap ladder and archive/RSS tradeoff report. |
| `cmix21_memory_surface_scan.py` | Scans cmix21 result and guard receipts for non-PPMD memory-surface evidence. |
| `hutter_upper_bound_certificate.py` | Builds or refreshes upper-bound certificate state. |
| `enwiki9_evidence_matrix.py` | Generates `docs/evidence_matrix.md` from result JSONs only. |
| `enwiki9_best_results.py` | Generates `docs/best_results.md`, a compact top-results view by measured scope. |
| `enwiki9_status_receipt.py` | Generates `docs/status_receipt.md/json` from certificate, lock, gate, and process state, including a flat `operator_summary` for handoff automation. |
| `enwiki9_normalize_receipts.py` | Regenerates certificate, evidence matrix, memory-valve report, residual matrix, and status receipt in one non-heavy pass. |
| `enwiki9_artifact_fingerprint_audit.py` | Verifies recorded result/guard receipt hashes in candidate meta rows and reports legacy rows missing fingerprints. |
| `enwiki9_doc_lint.py` | Validates live docs, claim flags, active-gate consistency, status-summary fields, stale paths, and tool inventory coverage. |
| `frontier_target_report.py` | Ranks projected or exact rows against a target percentage. |
| `forecast_frontier.py` | Forecast/frontier reporting for candidate triage. |

Do not start a new heavy gate from these while `/tmp/enwiki9-heavy.lock` is
owned by another run.

`forecast_frontier.py` and `frontier_target_report.py` are read-only, but they
can consume substantial CPU/RAM while scanning the result corpus. Do not run
them beside an active guarded scorer unless the scorer has already released the
heavy lane.

## Candidate Audit And Triage

| Tool | Purpose |
|---|---|
| `candidate_audit.py` | Audits candidate contracts, registry state, source files, and evidence. |
| `candidate_triage.py` | Selects benchmark-or-retire candidates and prints locked gate plans. |
| `cmix21_package_candidate.py` | Packages cmix21 variants into candidate directories. |

## cmix/fx2 Core Tuning And Reproduction

| Tool | Purpose |
|---|---|
| `fx2_core_tune_package.py` | Packages native fx2 tuning variants. |
| `fx2_core_tune_queue.py` | Queues core-tuning candidates. |
| `fx2_public_repro_queue.py` | Handles the public fx2-cmix reproduction lane. |
| `fx2_profile_summary.py` | Summarizes fx2 profile/result data. |
| `fx2_arbitrage_report.py` | Reports score/arbitrage opportunities across fx2 variants. |
| `fx2_rdo_feasibility.py` | Screens rate-distortion-style feasibility. |

## Residual, Shadow, And SSE Research

| Tool | Purpose |
|---|---|
| `fx2_loss_probe.py` | Probes loss data from fx2-style runs. |
| `fx2_loss_ledger.py` | Builds loss accounting views. |
| `fx2_loss_windows.py` | Breaks loss into windows. |
| `fx2_loss_spans.py` | Reports loss spans. |
| `fx2_loss_sample_summary.py` | Summarizes sampled loss rows. |
| `fx2_residual_probe.py` | Builds flag-clean FX2 residual probes, including archive-neutral WRT observation traces. |
| `fx2_residual_cache.py` | Caches legacy and WRT Wiki shell residual state. |
| `fx2_residual_heatmap.py` | Builds residual heatmaps. |
| `fx2_residual_apm_score.py` | Scores APM-style residual corrections. |
| `fx2_residual_gain_certificate.py` | Certifies residual gains. |
| `fx2_residual_oracle_partitions.py` | Builds oracle partitions for residual analysis. |
| `fx2_residual_oracle_upper_bound.py` | Estimates residual upper-bound potential. |
| `fx2_residual_state_search.py` | Searches residual state families. |
| `fx2_residual_state_search_stream.py` | Streamed residual state search. |
| `fx2_residual_xml_ledger.py` | Runs legacy or WRT Wiki shell residual ledgers on an exact FX2 trace with qbit screening, abstention, and exact replay for selected keys. |
| `wrt_trace_extract.py` | Reconstructs the exact WRT byte stream from an aligned FX2 bit trace and writes a hash-counted alignment receipt. |
| `wrt_wiki_shell_copy_rule_ledger.py` | Distills bounded WRT copy evidence into tiny causal rules and confirms selected rules on an untouched split with counted code cost. |
| `wrt_wiki_shell_residual_tree.py` | Trains and exports a small causal residual decision tree from WRT shell state with held-out promotion thresholds and counted node cost. |
| `fx2_shadow_residual_coder.py` | Shadow-coder evaluator for residual probabilities. |
| `fx2_residual_shadow_matrix.py` | Generates `docs/residual_shadow_matrix.md` from cached residual/SSE JSON receipts. |
| `fx2_xml_residual_screen.py` | Ranks compact causal XML/Wiki residual correction keys on cached FX2 traces with held-out/code-cost accounting. |
| `streaming_retrieval_mixer_plan.py` | Generates `docs/streaming_retrieval_mixer.md`, the lock-safe SRSTC causal sketch-retrieval algorithm and receipt contract. |
| `streaming_retrieval_shadow.py` | Runs exact-shadow SRSTC/sketch retrieval on raw, legacy-row, or aligned WRT shell traces, including independently routed byte-memory bands. |
| `streaming_retrieval_raw_shadow.py` | Runs exact-shadow SRSTC/sketch-retrieval probes on raw byte-aligned corpus bits with an adaptive raw baseline. |
| `streaming_retrieval_codec.py` | Experimental SRSTC codec harness for turning raw shadow probabilities into replayable archive bytes. |
| `streaming_retrieval_receipt_audit.py` | Audits cached SRSTC receipts for held-out net savings, alignment safety, state bounds, and complete block-regression evidence. |
| `streaming_retrieval_block_regime_audit.py` | Labels regressing and weak-positive SRSTC blocks with offline teacher-only Wikipedia/XML regime diagnostics and causal prefix checkpoints. |
| `streaming_retrieval_continue_shadow.py` | Reads the SRSTC audit queues, prioritizes the target-closing block-posterior replay, and by default refuses to execute while the cmix heavy lock is held. |
| `streaming_retrieval_fx2_trace_queue.py` | Prints lock-safe SRSTC shadow commands for an existing `FX2_RESIDUAL_ROW` log or residual-probe manifest; it does not launch a compressor. |
| `fx2_mwcc_router_shadow.py` | Deterministic router shadow evaluation. |
| `fx2_manifold_outer_sse_search.py` | Manifold/outer-SSE search lane. |
| `fx2_issa_shadow_search.py` | Integer state-space attractor shadow lane. |
| `fx2_sc_schema_scale_sweep.py` | Schema-scale sweep for FX2-SC. |

These tools are non-heavy when they operate on existing logs or cached traces.
They become runner-adjacent if they invoke a compressor.

## Ordering, Geometry, And Embedding Teachers

| Tool | Purpose |
|---|---|
| `embedding_teacher_order.py` | Offline embedding-teacher ordering experiments. |
| `article_order_teacher_distill.py` | Distills deterministic order keys against the upstream Voyage/t-SNE article-order teacher. |
| `hierarchical_chunk_embedding_teacher.py` | Hierarchical chunk embedding-teacher probes. |
| `hierarchical_retrieval_shadow.py` | Retrieval-style shadow experiments. |
| `page_order_screen.py` | Screens page ordering rules. |
| `page_order_gepa.py` | GEPA page-order experiments. |
| `page_order_gepa_screen.py` | Screens GEPA ordering candidates. |
| `page_order_gepa_boundary.py` | Boundary-focused GEPA ordering. |
| `page_order_gepa_hybrid.py` | Hybrid GEPA ordering. |
| `fx2_gepa_order_package.py` | Packages fx2 GEPA ordering variants. |
| `gepa_validation_queue.py` | Validates GEPA candidates. |
| `page_family_gate.py` | Screens page-family state. |
| `frontier_strategy_search.py` | Searches frontier strategies. |
| `monte_carlo_strategy_search.py` | Randomized strategy search over candidate surfaces. |

Final Hutter candidates may use only distilled deterministic rules from these
lanes unless all model/index bytes are counted.

## Typed Anchors, Macros, And Structural Transforms

| Tool | Purpose |
|---|---|
| `typed_anchor_signal_report.py` | Reports typed-anchor signal. |
| `fx2_typed_anchor_soft_queue.py` | Queues soft typed-anchor experiments. |
| `macro_token_search.py` | Searches macro-token candidates. |
| `macro_residual_package.py` | Packages macro-residual variants. |
| `online_bpe_gate.py` | Screens online BPE gates. |
| `segmented_split_probe.py` | Probes segmented split strategies. |
| `wrt_codeword_split.py` | WRT codeword split experiments. |
| `wrt_plane_split.py` | WRT plane split experiments. |
| `fx2_wrt_code_loss.py` | Loss accounting for WRT code paths. |
| `fx2_reorder_dictionary.py` | Reorder/dictionary experiments. |
| `causal_state_screen.py` | Screens causal state candidates. |
| `sketch_probe.py` | Sketch-based signal probes. |
| `random_window_novelty_screen.py` | Runs deterministic selection/confirmation screens for reversible zero-table Wikipedia transforms on disjoint random 500K/1M windows, with matched controls and two proxy backends. |
| `random_window_fx2_title_echo_gate.py` | Runs a frozen random-window raw/title-echo pair through six serialized, RSS-guarded native FX2/WRT encode/decode/determinism phases. It must own `/tmp/enwiki9-heavy.lock`. |

## Native Codec Prototypes

| Tool | Purpose |
|---|---|
| `qm_context_codec_v1.cpp` | Native context codec prototype. |
| `phda9_wit_tool.cpp` | Native WIT/prototype tool. |

## Utility Scripts

| Tool | Purpose |
|---|---|
| `enwiki9_delayed_status_check.sh` | Delayed status probe for active runs, including cmix phase, staging temp files, decode scope progress, lock state, gate-decider output, and a stable `run_logs/enwiki9_delayed_status_latest.log` pointer. |

## Maintenance Rules

- Add a tool here when adding it to `tools/`.
- If a tool launches a compressor, document whether it must respect
  `/tmp/enwiki9-heavy.lock`.
- If a tool only reads cached logs, label it as safe parallel work in the
  relevant design doc.
- If a tool graduates a measured result, link the result JSON from
  `ALGORITHMS.md`, `CMIX21_LOCK_SAFE_QUEUE.md`, or `UPPER_BOUND_CERTIFICATE.md`
  as appropriate.
