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
| `run_fx2_cmix21_wrapper_proof.py` | Runs a serialized guarded source-wrapper archive-identity, roundtrip, and deterministic-replay proof only after a sealed `10M` screen authorizes it. |
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
| `fx2_cmix21_nested_endpoint_screen.cpp` | Validates archive-neutral matched `96x2`/CMIX endpoint traces, selects only on development rows, and performs exact fixed-point range encode/decode and economics replay. |
| `fx2_cmix21_contextual_endpoint_screen.py` | Kill-gates train-fitted causal context selection over frozen matched `96x2` endpoint blends before any online-mixer integration. |
| `fx2_cmix21_affine_endpoint_screen.py` | Fits a training-only affine-logit correction over matched FX2/CMIX endpoints and reports disjoint train, development, and holdout qbit economics. |
| `build_cmix21_p1_matched_trace.py` | Converts an observation-only CMX21P1 probability stream plus its reversible WRT store into the minimal CMNEST1 truth/probability trace accepted by the exact endpoint replay. |
| `build_reproducible_source_shar.py` | Reconstructs a declared text source tree through one readable deterministic shell bundle and can emit the standard two-entry bzip2 source ZIP. |
| `build_reproducible_source_zip.py` | Builds deterministic direct-entry ZIP variants from an explicit source file list for package-method comparisons. |
| `run_fx2_cmix21_backend_identity_screen.py` | Alternates reference and candidate backends on one guarded input to test archive identity and runtime without changing compression arithmetic. |
| `seal_reproducible_source_shar_package.py` | Seals bundle, ZIP, source reconstruction, clean-build, backend, and wrapper identity for the counted source representation. |
| `seal_fx2_cmix21_backend_identity_runtime_screen.py` | Seals arithmetic identity and measured runtime/RSS evidence for a backend-only optimization. |
| `seal_fx2_cmix21_lstm200_source_frontier.py` | Combines constructive 200x2 evidence, reproducible package cost, and source equivalence into the frozen disjoint-screen boundary. |
| `seal_fx2_cmix21_lstm200_disjoint.py` | Seals the exact offset-500M reset-slice economics decision for source-built 200x2. |
| `seal_fx2_cmix21_matched_disjoint.py` | Combines the frozen same-store 96x2/full-CMIX replay, clean guards, and revised package economics into a native-integration or retirement decision. |
| `seal_fx2_cmix21_source_package_accounting.py` | Applies a verified source-package representation to an existing wrapper proof without relabeling codec evidence. |
| `seal_fx2_cmix21_dual_rate_receipt.py` | Seals source, archive, roundtrip, determinism, runtime, and accounting evidence for the quarantined phase-aligned recurrent candidate. |
| `seal_fx2_cmix21_lstm112_10m_receipt.py` | Verifies and seals the terminal native-112 cumulative-10M archive, RSS, source-mismatch, and counted economics decision. |
| `seal_fx2_cmix21_lstm112_plus80_10m_receipt.py` | Verifies the exact geometry-title package, transform, clean source binary, cumulative-10M archive, RSS, and counted heterogeneous-endpoint decision. |
| `seal_fx2_cmix21_lstm112_plus80_terminal.py` | Combines the passed exact 10M wrapper proof with matched opening/later recurrent receipts and seals the no-larger-gate retirement decision. |
| `seal_fx2_cmix21_original_order_blend.py` | Seals the frozen exact-original-order FX2/compact-200 blend across the opening 1M and confirmation 10M scopes, including ordering and source-package economics. |
| `fx2_attribution_external_base_screen.py` | Screens causal component endpoints against an exact external base probability stream with train/dev/holdout separation, exact range replay, and regression/economics gates. |
| `cmix_aux_logit_blend_screen.py` | Selects and replays bounded logit blends between a frozen CMIX base and an independently evolved causal endpoint, including fixed-point-ready weights and held-out block audits. |
| `endpoint428_paired_trace.py` | Validates same-execution compact-base, endpoint428, hybrid, and truth streams; proves trace-on/off archive identity and emits an exact `FX2PT01` hybrid trace. |
| `compact_layer0_blend_screen.py` | Selects one compact layer-0 residual endpoint over endpoint428 using development rows before sealed holdout replay. |
| `compact_layer0_sparse_blend_screen.py` | Fits and exactly replays a sparse fixed-point compact layer-0 blend over endpoint428. |
| `compact_layer0_online_mixer_screen.cpp` | Runs the causal fixed-point online endpoint428/compact layer-0 residual mixer with frozen holdout boundaries. |
| `compact_layer0_online_mixer_receipt.py` | Seals exact arithmetic and replay evidence for a frozen compact online-mixer probability stream. |
| `endpoint428_mxx_sse_shadow.py` | Screens decoder-causal endpoint428 SSE tables keyed by FX2's reconstructed `mxx` state. |
| `fx2lite_fxcm_hash_mixer_trace.cpp` | Emits causal compact hashed-mixer endpoints from FX2-lite's already-computed FXCM probability vector. |
| `fx2_compact_trace_window.py` | Extracts and seals identity-checked cold-reset or cumulative compact probability windows without relabeling them as prefix evidence. |
| `p1_wrt_to_fx2pt_trace.py` | Combines an exact P1 probability stream with its matching WRT store into the compact `FX2PT01` truth/probability trace format. |
| `wikiir_prior_page_columnar_probe.py` | Repackages the exact prior-page ADD/COPY/RUN IR into fourteen typed columns, verifies byte-identical IR/raw reconstruction, and applies per-column MDL accounting. |
| `wikiir_materialize.py` | Materializes a deterministic WikiIR prefix, verifies exact raw inversion, and seals program/input/IR identities before a target-backend probe. |
| `wikiir_title_vertex_tail_layout.py` | Repackages the exact title-as-vertex choices with the text skeleton first and a self-locating directory trailer, isolating backend adaptation from selected information. |
| `wrt_sequence_memoizer_trace.py` | Emits a deterministic bounded integer Sequence-Memoizer endpoint over completed WRT token suffixes for exact matched hybrid replay. |
| `wrt_entity_trie_fx2_shadow.py` | Reconstructs title and link entities from the unchanged WRT stream, builds decoder-causal entity tries, and scores fixed-point continuation probabilities against an exact FX2-compatible base trace. |
| `wrt_entity_node_backoff_trace.py` | Emits a bounded endpoint428-relative residual calibration trace keyed by decoder-built entity-trie node and support. |
| `wrt_event_srstc_trace.py` | Emits an endpoint428-relative SRSTC-style continuation endpoint keyed by decoder-rebuilt raw semantic state before each completed WRT event. |
| `wrt_reference_prefix_cts_shadow.py` | Scores a causal prior-reference WRT continuation table against an exact FX2 trace, with development/holdout qbits, positive-event oracle accounting, and exact range replay. |
| `wrt_normalized_phrase_copy_shadow.py` | Scores exact and number/whitespace-normalized long WRT event-suffix continuation models against an exact FX2 trace with chronological partitions and exact range replay. |
| `wrt_normalized_phrase_endpoint_trace.py` | Emits a causal normalized long-context WRT phrase endpoint as a `CMXAUX1` pair plus exact FX2 `CMX21P1` base for frozen generic calibration. |
| `wrt_hashed_residual_online_screen.cpp` | Screens payload-free online hashed residual SSE over FX2 probability, completed WRT event-history hashes, causal current-event prefix, bit phase, and prior byte. |
| `seal_wrt_hashed_residual_online.py` | Freezes the development-selected WRT residual variant, ignores confirmation-local reselection, binds both raw-FX2 traces and inputs by hash, and records endpoint428 debt economics. |
| `wrt_hierarchical_phase_residual_screen.cpp` | Applies payload-free integer Bayesian residual backoff across WRT event phase, 2-bit, 4-bit, and full byte prefixes with tail-sensitive FX2 probability buckets. |
| `seal_wrt_hierarchical_phase_residual.py` | Freezes the log-bucket hierarchy, binds three raw-FX2 and two target-substrate replays by content hash, retires insufficient direct endpoint428 transfer, and accounts the layer-0 composite counterfactual without forecast credit. |
| `wrt_phase_residual_native.cpp` and `wrt_phase_residual_native.h` | Production-shaped zero-payload `Predict/Perceive` component for the frozen hierarchical event-phase residual, with all state rebuilt online. |
| `wrt_phase_residual_native_replay.cpp` | Replays the production component against an exact `CMX21P1` stream and WRT truth store using the archive range coder. |
| `seal_wrt_phase_residual_native.py` | Requires two byte-identical clean builds and exact duplicate P1 replays, binds component source/input hashes, and records compressed source and state cost. |
| `wrt_event_context_tree_residual_screen.cpp` | Compares cumulative phase-prefix residual calibration with nested completed-event identity and exponentially decayed phase variants on an exact P1/WRT stream. |
| `wrt_phase_strength_router_screen.cpp` | Causally routes scaled frozen-phase corrections and tests a decoder-reconstructed Wiki-mode residual backoff against exact P1 controls. |
| `wrt_phase_newton_residual_screen.cpp` | Compares fixed-point WRT-phase logit-gradient/curvature endpoints and one frozen/Newton blend against exact endpoint P1 controls. |
| `wrt_shell_regime_extract.py` | Converts aligned WRT shell rows into an overlapping page/title/prose/ref/URL/table/list/template mode mask without treating concurrent modes as exclusive. |
| `cmix_aux_bucket_calibration.py` | Trains then freezes a compact decoder-rebuilt probability-bucket calibration over an auxiliary endpoint and exact base trace. |
| `wikiir_page_list_referentiation_probe.py` | Measures WebGraph-style ordered link-list COPY/ADD headroom against earlier pages with a deterministic random-prior control. |
| `wikiir_template_value_referentiation_probe.py` | Measures complete-page-causal same-skeleton template-field COPY/ADD headroom against a matched deterministic prior-template control. |
| `wikiir_url_prefix_reuse_probe.py` | Screens a self-trained URL host-plus-first-path-prefix reference event with full opcode and identifier costs before inverse construction. |
| `wikiir_citation_field_columnar_probe.py` | Screens an exact reversible citation-template field-value columnar transform against matched ordinal buckets on deterministic random 500K/1M windows. |
| `wikiir_named_ref_intern_probe.py` | Screens exact decoder-built interning of repeated `<ref name>` values against a matched literal-mode container on deterministic random 500K/1M windows. |
| `wikiir_reference_delta_probe.py` | Screens exact causal COPY/ADD deltas against earlier same-skeleton reference bodies on event-dense and random 500K/1M windows with a matched literal-container control. |
| `wrt_entity_regret_router_shadow.py` | Applies node-local causal reflected regret to the exact WRT entity-trie endpoint with frozen train/held-out accounting. |
| `wrt_entity_context_mixer_shadow.py` | Selects and exactly replays a causal contextual mixer over WRT entity-trie residual experts. |
| `wrt_exact.py` | Parses FX2/CMIX21 WRT stores into exact decoded bytes and completed causal events shared by WRT-native scorers. |
| `wrt_title_token_automaton.py` | Scores hard current-title transition rules and previous-title controls against an exact compact probability trace with raw/store/archive identity checks. |
| `wrt_title_support_backoff.py` | Scores integer hierarchical title-transition probabilities and current-minus-previous contrast against the same exact substrate. |
| `wrt_typed_skip_cts_trace.py` | Emits a residual-aware integer endpoint from global and decoder-rebuilt Wiki field/mode/slot suffix histories that skip intervening regimes. |
| `seal_wikiir_target_backend_probe.py` | Seals an exact raw-to-IR inverse and guarded target-backend encode economics result; it explicitly withholds codec-proof status when a terminal archive miss makes backend decode irrational. |
| `seal_cmix21_lstm200_fx2lite428_native.py` | Seals native compact-200 plus endpoint428 wrapper identity, roundtrip, determinism, aggregate decimal RSS, reproducible source-package identity, and conservative forecast economics. |
| `seal_cmix21_lstm200_fx2lite428_ppmd_recovery.py` | Seals the endpoint428 PPMD failure reproduction, repaired 1M archive identity, 1.5M roundtrip/determinism, clean source reconstruction, decimal tree RSS, and adjusted strict-10M economics ceiling. |
| `seal_cmix21_lstm200_fx2lite428_10m.py` | Seals the canonical original-order 10M archive screen and, only after an economics pass, its exact roundtrip and deterministic replay while keeping 1G authorization separate. |
| `seal_cmix21_lstm200_fx2lite428_10m_codec_failure.py` | Seals a non-memory endpoint428 10M codec termination, preserved WRT stream, and archive-identical RAM-PPMD control without manufacturing an archive or economics result. |
| `seal_cmix21_lstm200_fx2lite428_ram_recovery.py` | Seals archive-neutral composition of RAM-backed auxiliary PPMD storage and deterministic context recovery through the exact 1.5M boundary, including clean source and adjusted 10M economics. |
| `seal_cmix21_lstm200_fx2lite428_stats_failure.py` | Maps the combined-recovery exact-10M SIGSEGV from the kernel fault address through a machine-code-identical symbol build to the FX2-lite PPMD statistics dereference, while preserving the no-score boundary. |
| `seal_cmix21_lstm200_fx2lite428_stats_recovery.py` | Seals the clean-built statistics-span recovery at exact 1M, requires archive identity and deterministic source reconstruction, and recalculates the strict exact-10M accounting ceiling. |
| `seal_cmix21_lstm200_fx2lite428_allocator_failure.py` | Maps the repaired exact-10M SIGSEGV through a machine-code-identical symbol build to the FX2-lite PPMD free-list allocator chain, preserves the no-score boundary, and authorizes only a full primary-PPMD safety port with exact-1M identity replay. |
| `seal_cmix21_lstm200_fx2lite428_primaryppmd_identity_failure.py` | Seals the wholesale primary-PPMD exact-1M archive regression under a clean decimal-memory guard and authorizes only a selective allocator/free-list port that retains the archive-neutral v9 model behavior. |
| `seal_cmix21_lstm200_fx2lite428_allocator_recovery.py` | Seals the selective allocator/free-list recovery with exact-1M archive identity, roundtrip, independent clean-build determinism, decimal tree-RSS guards, reproducible counted source, and a recalculated strict exact-10M ceiling. |
| `seal_cmix21_lstm200_fx2lite428_context_restore_failure.py` | Maps the allocator-recovered exact-10M SIGSEGV through a machine-code-identical symbol build to the FX2-lite PPMD `RestoreModelRare` suffix walk, preserves the no-score boundary, and authorizes only bounded context-restore recovery. |
| `seal_cmix21_lstm200_fx2lite428_context_recovery.py` | Seals bounded reset-time context/suffix recovery with exact-1M archive identity, roundtrip, independent clean-build determinism, decimal tree-RSS guards, reproducible counted source, and a revised strict exact-10M ceiling. |
| `seal_endpoint428_pair_layer0_native.py` | Seals native endpoint428 pair/layer-0 1M identity, roundtrip, deterministic source accounting, disjoint transfer, and exact 10M economics. |
| `seal_endpoint428_pair_layer0_10m.py` | Seals the frozen pair/layer-0 exact-10M archive screen and authorizes codec replay only after the receipt-derived economics ceiling passes. |
| `seal_endpoint428_pair_layer0_lzma_package.py` | Seals the direct-entry LZMA source-package accounting bridge, exact 10M roundtrip, independent deterministic replay, decimal-memory guards, and full-gate authorization. |
| `continue_endpoint428_pair_layer0_10m.py` | Waits silently for the frozen 10M encode, seals its economics, and runs serialized guarded decode plus independent clean-build re-encode only after an exact ceiling pass; it cannot authorize 1G. |
| `seal_wrt_static_boundary_swap_disjoint.py` | Seals an untouched reset-slice archive comparison for the static WRT dictionary boundary-swap candidate. |
| `seal_wrt_static_boundary_swap_geometry_title_proxy.py` | Seals reversible geometry-title proxy evidence and compressed store/dictionary costs for a static WRT boundary swap. |
| `seal_wrt_static_boundary_swap_112plus80_gate.py` | Seals the exact 10M static-WRT-swap comparison against the source-built 112+80 codec, including package delta and projected-score accounting. |
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
| `enwiki9_gate_watch.py` | Silently samples a live native gate and emits durable JSON events only at progress milestones or guard, memory, identity, lock, process, and terminal state changes. |

## Maintenance Rules

- Add a tool here when adding it to `tools/`.
- If a tool launches a compressor, document whether it must respect
  `/tmp/enwiki9-heavy.lock`.
- If a tool only reads cached logs, label it as safe parallel work in the
  relevant design doc.
- If a tool graduates a measured result, link the result JSON from
  `ALGORITHMS.md`, `CMIX21_LOCK_SAFE_QUEUE.md`, or `UPPER_BOUND_CERTIFICATE.md`
  as appropriate.
