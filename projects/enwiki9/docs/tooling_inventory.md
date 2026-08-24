# enwiki9 Tooling Inventory

This inventory groups `projects/enwiki9/tools/` by purpose. It is a map for
maintenance and handoff, not a claim that every script is current.

## Heavy-Gate And Driver Support

These scripts can interact with scoring or guard infrastructure. Treat them as
runner-adjacent.

| Tool | Purpose |
|---|---|
| `enwiki9_lab.py` | Primary adaptive experiment loop: creates and clones candidates, records mutation lineage, selects the next exact gate, manages atomic durable jobs, fans out small gates, serializes heavy work, and refreshes inventories and reports after terminal batches. |
| `run_with_rss_guard.py` | Wraps commands with RSS sampling and guard enforcement; writes live and final guard JSON. |
| `cmix_filebacked_fxcm_100m_identity_resource.py` | Coordinates the opening-100M parent/q1 identity arms and observer-free q1 resource arm only after validating the distinct 149-member Python/schema harness closure and all retained q1 antecedents. It emits zero compression and score credit. |
| `cmix_filebacked_fxcm_100m_identity_resource_verify.py` | Cannot launch a compressor; independently rederives the opening-100M harness closure, artifacts, modeled-coordinate identity, phase resources, cleanup, and gate decision from the raw receipt. |
| `cmix_filebacked_fxcm_full_identity_arm.py` | Launches one parent or q1 full-1G diagnostic observer encode on one selected CPU, refuses an active full-1G lease, owns disjoint result/scratch/backing roots, and enforces an explicit `11,500,000 KiB` process-tree plus `100,000,000,000`-byte scratch guard. It retains every-bit probability and seven sparse-state checkpoints but has no resource or score authority. |
| `cmix_filebacked_fxcm_full_identity.py` | Reopens passing qm8 A/B, opening-100M, observer-build, and calibration evidence, validates the exact transitive Python/schema source closure, then launches the parent and q1 full observer arms sequentially into unique roots and emits a zero-credit joint receipt. It cannot run while the exclusive full-1G lease exists. |
| `cmix_filebacked_fxcm_full_identity_verify.py` | Cannot launch a compressor; independently rederives the transitive Python/schema source closure, reparses the raw probability/coder/state manifests, rederives calibration and activation verifiers, validates modeled-coordinate geometry and negative controls, and emits phase-11 verification with no resource or score authority. |
| `cmix_filebacked_fxcm_full_qm8_terminal_dispatch_recover.py` | Cannot launch a verifier or compressor; transactionally rolls back an exact uncommitted qm8 terminal-plan exchange or finalizes a fully validated committed activation, preserving intent/plan evidence and releasing only exact intent-bound stale lock inodes. |
| `wiki_pda_structural_replay_ceiling_q0_v2_authority_v3.py` | Preserves the frozen WIKI-PDA v2 scanner and causal controls while replacing its revoked q1-v4 authority with a future active-policy-v7-or-later q1-v3 receipt, exact stored verification, and fresh independent re-verification; it remains dormant and zero-credit while qm8 owns the full-1G namespace. |
| `wiki_pda_structural_replay_ceiling_q0_v2_authority_v3_verify.py` | Cannot launch the scanner; independently rederives the frozen WIKI-PDA decision, resource and lease evidence, plus the active q1-v3 policy chain and v6 design-policy binding. |
| `enwiki9_dependency_closure.py` | Stages a new exact candidate bundle, rejects implicit filesystem inputs, hashes and counts every package member, and emits the validated dependency/command/license closure without launching a compressor. |
| `enwiki9_clean_room_replay.py` | Runs a frozen full-1G package through two fresh-build compression sandboxes and one corpus-blind fresh-build decode sandbox; all runtime phases use one-core process-tree, wall-time, memory, and temporary-disk guards, and only a complete second-host receipt can close cross-host identity. |
| `enwiki9_release_receipts.py` | Regenerates the schema-valid structural router for canonical dependency bundles, successful run receipts, and failed clean-room attempts; it never upgrades structure-only discovery into artifact-verification credit. |
| `enwiki9_python_source_closure.py` | Cannot launch a process; recursively resolves project-local Python imports under `tools/` and emits stable path/digest rows so prospective inputs and terminal source packages can share one exact code closure. |
| `nncp_delta_midas_named_midpoint_gradient_q3.py` | Launches two closed-teacher F encodes for the zero-credit direct-F32 named-gradient retry, checks a distinct explicit-F32 reference path, and retains q2 comparison as a sensitivity diagnostic; it must run only as a revision-bound job under the process-tree memory and scratch guard. |
| `materialize_nncp_named_midpoint_gradient_q3.py` | Cannot launch a process; replaces q2's BF16 product/reduction observation with LibNC's direct F32 squared-sum plus an explicit BF16-to-F32 multiply-and-sum reference without changing probabilities. |
| `record_driver_result.py` | Records driver/guard evidence into candidate meta rows, including receipt paths, byte sizes, modified UTC stamps, and SHA-256 fingerprints. |
| `cmix21_gate_decider.py` | Reads cmix21 driver and RSS guard receipts, prints the next safe action, and emits terminal apply commands for pass, RSS failure, and non-promotable terminal failures. |
| `cmix21_continue_active_gate.py` | Finds the certificate active gate, calls `cmix21_gate_decider.py`, and optionally applies only terminal actions: pass promotion, RSS lower packaging, or non-promotable failure recording. |
| `cmix21_memory_valve_report.py` | Generates the PPMD cap ladder and archive/RSS tradeoff report. |
| `cmix21_memory_surface_scan.py` | Scans cmix21 result and guard receipts for non-PPMD memory-surface evidence. |
| `hutter_upper_bound_certificate.py` | Builds or refreshes upper-bound certificate state. |
| `hutter_run_ledger.py` | Generates source-bound JSON and Markdown candidate-run ledgers grouped by measured scope, corpus population, evidence tier, proof state, and forecast. |
| `backfill_run_ledger.py` | Rebuilds validated v2 rows in `results/run_ledger.jsonl` only from timestamp-named historical driver results, binding each retained JSON by project-relative path, bytes, and SHA-256; supports append/dry-run modes. |
| `enwiki9_evidence_matrix.py` | Generates `docs/evidence_matrix.md` from result JSONs only. |
| `enwiki9_best_results.py` | Generates `docs/best_results.md`, a compact top-results view by measured scope. |
| `enwiki9_status_receipt.py` | Generates `docs/status_receipt.md/json` from certificate, lock, gate, experiment population, and process state, including explicit byte/symbol scope and a flat `operator_summary` for handoff automation. |
| `enwiki9_normalize_receipts.py` | Regenerates certificate, evidence matrix, memory-valve report, residual matrix, and status receipt in one non-heavy pass. |
| `enwiki9_artifact_fingerprint_audit.py` | Verifies recorded result/guard receipt hashes in candidate meta rows and reports legacy rows missing fingerprints. |
| `enwiki9_doc_lint.py` | Validates live docs, claim flags, active-gate consistency, status-summary fields, stale paths, and tool inventory coverage. |
| `enwiki9_page_shards.py` | Splits an exact XML byte stream at deterministic decoder-visible `<page>` boundaries and proves byte-exact reconstruction. |
| `enwiki9_shard_container.py` | Packs independent shard archives with raw/archive lengths into a reversible fixed-width container; four shards use a 44-byte directory. |
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
| `build_triage_ledger.py` | Builds an execution ledger for triage batches from batch queues and per-candidate logs. |
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
| `nncp_delta_midas_deep_residual.py` | Compares hash-bound retained F/O indexed branch traces under a frozen experiment contract; it cannot launch NNCP or a compressor and emits a zero-credit result plus the executed analyzer source. |
| `nncp_delta_midas_decoder_feature_probe.py` | Runs the prospectively frozen train/validation/test hashed-linear residual probe from retained traces; it cannot launch NNCP or a compressor and binds causal features, shifted control, quantized model, and held-out zero-credit evidence. |
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
| `minify_cpp_source.py` | Lexically removes C/C++ comments while preserving literals, token separation, and line counts, and mirrors non-code package inputs unchanged. |
| `run_fx2_cmix21_backend_identity_screen.py` | Alternates reference and candidate backends on one guarded input to test archive identity and runtime without changing compression arithmetic. |
| `seal_reproducible_source_shar_package.py` | Seals bundle, ZIP, source reconstruction, clean-build, backend, and wrapper identity for the counted source representation. |
| `seal_fx2_cmix21_backend_identity_runtime_screen.py` | Seals arithmetic identity and measured runtime/RSS evidence for a backend-only optimization. |
| `lstm_gate_runtime_probe.cpp` | Compares current, persistent-region, and serial fused three-gate schedules while requiring bit-identical LSTM state and output. |
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
| `endpoint_fixed_share_stack.cpp` | Runs a deterministic decoder-causal Bayesian fixed-share stack over preserved P1 endpoints with development-only configuration selection and exact arithmetic replay. |
| `typed_event_sleeping_bayes_endpoint428.py` | Runs the non-heavy exact opening-1M `causal_shadow` for completed structural-trigger continuation point masses, matched C0/E0/E1 controls, and ideal/Q16 Bayes envelopes over a hash-pinned endpoint428 P1 stream. |
| `compact_layer0_online_mixer_receipt.py` | Seals exact arithmetic and replay evidence for a frozen compact online-mixer probability stream. |
| `endpoint_diagonal_reservoir_screen.cpp` | Screens decoder-built diagonal multi-timescale reservoirs over exact P1 streams or either endpoint of a same-execution pair trace, with development-only selection, exact range-coder accounting, and a neutral zero-update control. |
| `endpoint_sparse_gru_distill_screen.py` | Distills a same-execution slow endpoint into a small causal byte GRU over a fast base endpoint, selects checkpoints without holdout reads, and applies exact truth-codelength plus payload-aware economics gates. |
| `endpoint_dilated_context_screen.py` | Screens a small nonrecurrent residual model over exact prior bytes at power-of-two lags, with development-only selection, sealed holdout, exact range replay, and payload-aware economics. |
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
| `endpoint_residual_history_screen.cpp` | Screens decoder-rebuilt endpoint-surprise histories as causal residual-retrieval keys on exact P1 streams. |
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
| `text3_structural_joint_shadow_qm0.py` | Prices prefix-causal TEXT3-style structural coordinates against the exact Endpoint428 P1 trace with KT, matched controls, and an exact-parent Bayesian fallback. |
| `far_history_cdc_copy_qm0.cpp` | Scans the canonical full 1G corpus for collision-verified, chronologically legal content-defined matches whose sources are more than 100M bytes behind the target. |
| `far_history_cdc_copy_qm0.py` | Repeats the full-corpus far-history scan, verifies deterministic summaries, prices canonical distance/length commands, and emits the zero-credit promotion decision. |
| `far_history_cdc_collective_ledger_qm1.cpp` | Emits QM0's frozen full-1G copy population as exact columnar literal-gap, source-distance, and length streams. |
| `far_history_cdc_collective_ledger_qm1.py` | Repeats, parses, collectively compresses, and target-prices the exact far-history side ledger with deterministic and memory receipts. |
| `far_history_residual_container_qc0.py` | Materializes QM1's frozen full-1G residual, verifies a second derivation digest, and reconstructs canonical enwiki9 exactly from the residual and paid ledger. |
| `cmix_obias_postwrt_far_history_cdc_qm0.py` | Prices collision-verified paid copies beyond cmix-obias's 60M history ring on its receipt-bound 587,138,826-byte modeled stream. |
| `segmented_split_probe.py` | Probes segmented split strategies. |
| `wrt_codeword_split.py` | WRT codeword split experiments. |
| `wrt_plane_split.py` | WRT plane split experiments. |
| `fx2_wrt_code_loss.py` | Loss accounting for WRT code paths. |
| `fx2_reorder_dictionary.py` | Reorder/dictionary experiments. |
| `causal_state_screen.py` | Screens causal state candidates. |
| `sketch_probe.py` | Sketch-based signal probes. |
| `random_window_novelty_screen.py` | Runs deterministic selection/confirmation screens for reversible zero-table Wikipedia transforms on disjoint random 500K/1M windows, with matched controls and two proxy backends. |
| `random_window_fx2_title_echo_gate.py` | Runs a frozen random-window raw/title-echo pair through six serialized, RSS-guarded native FX2/WRT encode/decode/determinism phases. It must own `/tmp/enwiki9-heavy.lock`. |
| `route_d_timestamp_microblock_gate.py` | Runs the non-heavy, zero-credit exact Route D timestamp-envelope rank/parity Q0 diagnostic with page-disjoint and chronological controls; it does not launch a compressor. |
| `route_e_state_preserving_prototype_bypass_gate.py` | Runs the non-heavy, zero-credit exact Route E prior-page prototype bypass Q0 with parent-payload identity, E1/E2/ER controls, finite command coding, residual range payloads, and WRT/raw reconstruction. |
| `mobius2_logos_surface_grammar_ceiling.py` | Runs the non-heavy, zero-credit exact LOGOS ordered-template WRT grammar ceiling with development-frozen rules, an uncharged information ceiling, paid S1/forced-literal SL archives, parent identity, and WRT/raw reconstruction. |
| `atlas_clockwork_seal.py` | Builds and verifies the lifecycle-aware private Atlas-Clockwork commitment; it does not authorize distribution unless verification returns `VALID_BOUND`. |

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
| `mobius2_logos_lexical_frame_ceiling.py` | Runs the zero-cost exact opening-1M LOGOS prose lexical-frame information certificate; read-only discovery plus receipt output, safe without the heavy lock. |

## Maintenance Rules

- Add a tool here when adding it to `tools/`.
- If a tool launches a compressor, document its CPU set, memory guard, and
  owned output directory. Concurrent isolated runs are allowed.
- If a tool only reads cached logs, label it as observation-only in the
  relevant design doc.
- If a tool graduates a measured result, link the result JSON from
  `ALGORITHMS.md`, `CMIX21_LOCK_SAFE_QUEUE.md`, or `UPPER_BOUND_CERTIFICATE.md`
  as appropriate.

### FRACTAL-2 tools added 2026-08-08

- `tools/fractal2_form_echo_joint_qm1.py`: exact-WRT/parent-P1 Gate -1 scorer for FORM/ECHO and B0/F0/E0/C0/S0/J0 controls; diagnostic only, launches no compressor.
- `tools/fractal2_recursive_punct_forest_qm2.py`: materially new recursive punctuation-forest partition layered over frozen QM1 scoring; diagnostic only, launches no compressor.
- `tools/fractal2_endpoint428_recursive_punct_qm3.py`: frozen QM2 repricing wrapper bound to the archive-identical Endpoint428 10M P1 receipt; diagnostic only, launches no compressor.
## `fractal2_endpoint428_paid_mdl_qp1.py`

- Candidate: `fractal2_endpoint428_paid_mdl_qp1_v1` (retired).
- Function: exact paid 10M FORM/ECHO selection, independent paid controls, finite side stream, Endpoint428 residual range stream, deterministic second encode, exact WRT replay, and official raw inverse.
- Measured result: no command was individually profitable; every arm was 1,634,559 bytes before the common 27,348-byte source charge.
- Durable output: `results/fractal2_endpoint428_paid_mdl_qp1_v1/decision.json`.
## FRACTAL QP1 unfiltered-ledger diagnostic

- Reused the immutable QP1 generators through runtime overrides; no measured candidate file was changed.
- J0 diagnostic: 708,455 selected fragments, 114,825.615 gross bytes, 3,049,038 raw ledger bytes, 780,964 LZMA ledger bytes.
- This is negative mechanism evidence only and is not a codec or score claim.
## `fractal3_prefix_triggered_qm4.py`

- Candidate: `fractal3_prefix_triggered_qm4_v1` (retired realization).
- Function: correct Endpoint428 P1 ceiling with each FORM first terminal left in the parent stream, later FORM terminals free, and matched ECHO controls on the same population.
- Durable output: `results/fractal3_prefix_triggered_qm4_v1/decision.json`.
## `fractal3_shortest_unique_trigger_qm5.py`

- Candidate: `fractal3_shortest_unique_trigger_qm5_v1` (retired realization).
- Function: exact-event prefix trie over learned FORM first terminals, retaining only uniquely dispatchable suffixes.
- Durable output: `results/fractal3_shortest_unique_trigger_qm5_v1/decision.json`.
## `fractal3_causal_rule_transition_qm6.py`

- Candidate: `fractal3_causal_rule_transition_qm6_v1` (retired realization).
- Function: online order-2 transition learning over completed non-overlapping FORM rules, shortest-unique fallback, and an explicit no-transition control.
- Durable output: `results/fractal3_causal_rule_transition_qm6_v1/decision.json`.
## Compact final-P1 trace and causal transfer tools

- `tools/materialize_compact_final_p1_trace.py`: hash-bound isolated-source materializer adding only an observation hook for compact's final WRT P1; trace-on/reference identity is mandatory.
- `tools/fractal2_compact_replacement_transfer_qm4.py`: rejected tombstone; the frozen QM3 universe failed decoder-causality review and must not be run.
- `tools/fractal3_compact_shortest_unique_transfer_qc0.py`: one-shot repricing of QM5's frozen causal spans on the receipt-bound compact trace; terminal zero-credit rejection at `89,993.155` displaced bytes.
- Durable outputs: `results/fractal2_compact_trace_10m_v1/decision.json` and `results/fractal3_compact_shortest_unique_transfer_qc0_v1/decision.json`.
## `wrt_page_trie_implicit_copy_qm0.py`

- Candidate: `wrt_page_trie_implicit_copy_qm0_v1` (retired realization).
- Function: one-pass paid-qbit screen over decoder-derived exact WRT event suffixes, implicit unique sources, adaptive copy selectors, power-of-two length symbols, and typed/untyped/shuffled controls.
- Result: T0 `-283,348.140` net bytes at canonical `10M`; every chronological third negative; peak guarded RSS `2,088,104` KiB.
- Durable output: `results/wrt_page_trie_implicit_copy_qm0_v1/decision.json`.
## `fractal4_slot_residual_quotient_qm1.py`

- Candidate: `fractal4_slot_residual_quotient_qm1_v1` (retired realization).
- Function: exact Q16 online Bayesian logit quotient over non-overlapping FORM slot values with ordinary, flat, and capacity-matched shuffled controls.
- Durable output: `results/fractal4_slot_residual_quotient_qm1_v1/decision.json`.
## `fractal4_slot_sleeping_trie_qm2.py`

- Candidate: `fractal4_slot_sleeping_trie_qm2_v1` (retired realization).
- Function: causal KT continuation probabilities keyed by FORM slot, two completed WRT bytes, and bit position under a global exact-parent Bayesian fallback.
- Durable output: `results/fractal4_slot_sleeping_trie_qm2_v1/decision.json`.
## `fractal5_vulcan_event_parent_control_qm0.py`

- Candidate: `fractal5_vulcan_event_parent_control_qm0_v1` (retired route).
- Function: constructive VULCAN event-PPM encode, exact decode, deterministic second encode, source packaging, and direct Endpoint428 archive-gap accounting on canonical 10M WRT.
- Durable output: `results/fractal5_vulcan_event_parent_control_qm0_v1/decision.json`.
