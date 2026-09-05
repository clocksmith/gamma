# Research Register

[Record index](research_register/README.md) | [Earlier records](research_register/archive/README.md)

## 2026-09-05 - Join the native MIDAS bit boundary and checkpoint state

`lib/midas_bit_predictor.hpp` now connects the causal midpoint scheduler and
byte adapter behind one pre-truth `predict()` / `observe(decoded_bit)` interface.
Combined checkpoint restore rejects inconsistent byte/bit clocks, mismatched
pending-byte ownership, differing pre-truth distributions, excess checkpoint
size, truncation and trailing bytes. All P/K/F/S finite sentinel inverses and
repeats pass through this interface with exact predictor and normalized coder
state agreement. P/K probabilities, payloads and authoritative-state projections
remain identical. Three regression tests and the joined address/undefined-behavior
sanitizer fixture pass.

Evidence: `operations/evidence/20260905_midas_bit_predictor_join_validation.json`.
This is implementation correctness only, with zero score credit and no corpus
access. A real complete-update trainable backend and its parent roundtrip remain
missing; the other owner's compact predictor source was not changed. The prior
source-bound infrastructure receipt remains unchanged and resolves at local
commit `9d327137`.

The user's `rdpush gamma` request created that commit but could not publish:
GitHub rejected SSH public-key authentication and the agent had no loaded
identities. No credential configuration was changed. Authentication must be
restored before publishing these local commits. HORIZON and its sole observer
remain unchanged, without partial scientific access.

## 2026-09-05 - Public FX2 parent reproduction and argmax comparison

| Frozen gate | Population | Exact archive result |
|---|---|---|
| `fx2_cmix_transformer_static_vocab_fixture50051_q0_v1` | Public 50,051-byte profiling fixture | 3,223 bytes; inverse, repeat, malformed envelope and repeated kernel probabilities pass |
| `fx2_cmix_transformer_transfer250k_q0_v2` | Canonical raw `[0,250000)` and `[500000000,500250000)` | 33,429 and 9,499 bytes; independent cold inverses/repeats pass |
| `fx2_bytemodel_argmax_unit_q0_v1` | 32 synthetic families, 256 paths each | Original/P/K/D/C probabilities and state agree; D avoids 4,641,532 of 8,224,768 comparisons per repeat |

The [fixture audit](../operations/provenance/public_fx2_static_vocab_fixture_terminal_20260905.json)
and [transfer audit](../operations/provenance/public_fx2_transfer250k_terminal_20260905.json)
bind the authenticated 205-symbol vocabulary, source, archive hashes and closed
guards. Their reflections are [fixture](../operations/adaptive/reflections/20260905T195118Z_c39265f90c.json)
and [transfer](../operations/adaptive/reflections/20260905T204313Z_bd6edb2ed4.json).
Transfer peak cgroup memory was 5,826,895,872 bytes. Conservative raw inventory
was 9,403,013 bytes, including overlapping source/runtime assets; complete
package closure and model licensing remain unresolved. These direct-WRT cold
slices do not reproduce the public reorder/PHDA pipeline or establish a 1G score.

The [unit audit](../operations/provenance/public_fx2_argmax_unit_terminal_20260905.json)
and [validated unit reflection](../operations/adaptive/reflections/20260905T211007Z_358c05f2db.json)
authorize preparing a native comparison, with no archive or speedup credit.
`fx2_cmix_transformer_argmax_fixture50051_q0_v1` passed all four native
roundtrips/repeats and twelve complete 259,824-bit coder-record streams. Every
archive remains 3,223 bytes. [Native audit](../operations/provenance/public_fx2_argmax_native_terminal_20260905.json)
and [validated reflection](../operations/adaptive/reflections/20260905T212145Z_70e5363a53.json)
retain the exact traces and closed guard. D/K diagnostic CPU ratio was 0.9987045,
missing the frozen 0.99 budget trigger. Hold this correct mechanism without a
larger runtime gate. The following model-packing comparison also failed.
This budget decision does not refute argmax reuse generally. Preserve
[launcher-affinity](../operations/provenance/public_fx2_static_vocab_launch_failure_20260905.json)
and [transfer-v1 preflight](../operations/provenance/public_fx2_transfer250k_preflight_v1_20260905.json)
failures unchanged. Public FX2/CMIX/model authorship remains upstream; Gamma's
framing, comparisons and prospective argmax change receive no compression credit.


`fx2_weight_pack_roundtrip_q0_v1` restores and repeats the full public model exactly,
but grows it from 2,930,652 to 2,938,887 bytes. Six independent synthetic tensor
fixtures and all negative controls pass; peak cgroup memory was 133,156,864 bytes.
The [weight audit](../operations/provenance/public_fx2_weight_pack_terminal_20260905.json)
and [validated reflection](../operations/adaptive/reflections/20260905T215312Z_bd5e9a17b9.json)
retire this exact preceding-symbol configuration before native integration.
Its extra 8,235 asset bytes exclude added loader costs. Other weight coders remain
untested; this result grants no full-corpus score or package qualification.

## 2026-09-05 - Restore missing terminal receipt links

These retained decisions were missing exact candidate references in the logical
register. The table restores navigation without changing their source bytes,
scientific conclusions, or objective bindings. Labels are reported by the source
receipts; they are not new launch authority or independently revalidated results.
Use the linked decision and its canonical terminal reflection before selecting
ancestry. Missing or invalid reflections remain visible in `records --view reviews`.

The public GCC v2 and v3 failures concern compilation and instruction selection;
v4 passed the build but rejected its fixture vocabulary. Its held configuration
requires a separately frozen mapping adapter. The initializer's historical
`authorize-integrated-replay` label is narrowed by its canonical reflection to
fixture reuse; it does not authorize a new integrated codec gate.

| Candidate | Retained source label |
|---|---|
| `cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v14` | [structured decision; inspect source](../results/cmix_obias_source_ppm_rss_env8192_diskbacked_q0_v14/decision.json) |
| `fx2_cmix_transformer_gcc_fixture50051_q0_v2` | [execution_failed](../results/fx2_cmix_transformer_gcc_fixture50051_q0_v2/decision.json) |
| `fx2_cmix_transformer_gcc_fixture50051_q0_v3` | [execution_failed](../results/fx2_cmix_transformer_gcc_fixture50051_q0_v3/decision.json) |
| `fx2_cmix_transformer_gcc_fixture50051_q0_v4` | [mapping_rejected](../results/fx2_cmix_transformer_gcc_fixture50051_q0_v4/decision.json) |
| `nncp_ggml_postupdate_forward_parity_64_q1_retry_v1` | [retry](../results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v1/decision.json) |
| `nncp_ggml_profile_forward_parity_64_qm13_v1` | [retire_exact_open_profile_forward_port](../results/nncp_ggml_profile_forward_parity_64_qm13_v1/decision.json) |
| `nncp_ggml_profile_forward_parity_64_qm18_v1` | [authorize_production_P_K_O_OK_F_S_attribution](../results/nncp_ggml_profile_forward_parity_64_qm18_v1/decision.json) |
| `nncp_libnc_bf16_gradient_merge_64_q0_retry_v5` | [retire](../results/nncp_libnc_bf16_gradient_merge_64_q0_retry_v5/decision.json) |
| `nncp_libnc_final_rmsnorm_affine_order_64_q0_v1` | [retry](../results/nncp_libnc_final_rmsnorm_affine_order_64_q0_v1/decision.json) |
| `nncp_libnc_final_rmsnorm_order_64_q0_retry_v1` | [retry](../results/nncp_libnc_final_rmsnorm_order_64_q0_retry_v1/decision.json) |
| `nncp_libnc_geglu_gate_avx2_64_q0_v1` | [authorize-successor](../results/nncp_libnc_geglu_gate_avx2_64_q0_v1/decision.json) |
| `nncp_libnc_profile_initial_fixture_65536_closurefix_q0_v1` | [authorize-integrated-replay](../results/nncp_libnc_profile_initial_fixture_65536_closurefix_q0_v1/decision.json) |
| `nncp_libnc_top_attention_product_oracle_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_attention_product_oracle_64_q0_retry_v2/decision.json) |
| `nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1` | [retry](../results/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v1/decision.json) |
| `nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_geglu_branch_adjoints_64_q0_retry_v2/decision.json) |
| `nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_pre_ff_hidden_adjoint_64_q0_retry_v2/decision.json) |
| `nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1` | [authorize-successor](../results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v1/decision.json) |
| `nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2` | [authorize-successor](../results/nncp_libnc_top_pre_ff_norm_branch_adjoint_64_q0_retry_v2/decision.json) |
| `nncp_open_branch_reduction_postupdate_64_q0_retry_v1` | [authorize-exact-reducer-integration](../results/nncp_open_branch_reduction_postupdate_64_q0_retry_v1/decision.json) |
| `nncp_open_concat_head_identity_64_q0_v1` | [authorize-successor](../results/nncp_open_concat_head_identity_64_q0_v1/decision.json) |
| `nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2` | [retire](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_retry_v2/decision.json) |
| `nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1` | [authorize-successor](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v1/decision.json) |
| `nncp_open_top_attention_forward_inputs_64_q0_v1` | [authorize-successor](../results/nncp_open_top_attention_forward_inputs_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_raw_branch_join_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_raw_branch_join_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_residual_conversion_order_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_rmsnorm_backward_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_rmsnorm_backward_state_reduce_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1` | [authorize-successor](../results/nncp_open_top_pre_ff_rmsnorm_output_order_64_q0_v1/decision.json) |
| `nncp_open_top_pre_ff_total_adjoint_64_q0_v1` | [retire](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_v1/decision.json) |
| `nncp_open_w_o_weight_slice_post_add_64_q0_v1` | [authorize-successor](../results/nncp_open_w_o_weight_slice_post_add_64_q0_v1/decision.json) |

## 2026-09-05 - Native MIDAS coder and causal scheduler pass synthetic checks

`lib/midas_native_codec.hpp` provides native finite Q16 arithmetic encoding and
decoding, explicit raw-byte identity framing, a pre-truth byte-to-bit adapter,
complete coder checkpoints and an exact first-state-divergence comparison.
`lib/midas_midpoint_schedule.hpp` provides the P/K/F/S update boundary: ordinary
parent updates after each 64 decoded bytes, an additional F update after the
first 32, and S with those already decoded targets cyclically shifted left once.
Every update rebuilds the active prefix from its retained segment origin. K
executes update and rebuild on a discarded copy, preserving the authoritative
parent. These are reusable components, not a sealed corpus candidate.

Three targeted tests pass with strict C++17 compilation. Separate address and
undefined-behavior sanitizer executions also pass. The native counting-fixture
payload equals the independently implemented Python payload; finite inverses,
repeats, corruption rejection, checkpoint continuation, P/K probability and
payload identity, and encoder/decoder state synchronization pass on synthetic
fixtures. The scheduler's sentinel deliberately invalidates recurrent state at
update, so prediction without rebuilding fails. These fixtures do not implement
or prove a neural predictor, complete-model gradients, or a MIDAS gain.

Evidence: `operations/evidence/20260905_midas_native_codec_scheduler_unit_validation.json`
binds source SHA-256 values, test commands, compiler identity and observed output.
Score credit is zero. The standalone trainable parent roundtrip remains missing.
No corpus experiment was launched and no partial HORIZON science was read.

The concurrent unregistered `programs/compact_midas_open_parent_q0_v1` source
tree was left untouched. Coordinate its owner before integrating the one compact
challenger: validate full gradients and optimizer/recurrent state, measure its
dominant kernel, and prospectively freeze the bounded parent P/K/F/S archive
gate. An independent eligible-parent explorer must preserve that ownership and
HORIZON's sole observer, retain source/package/resource bindings, and produce
exact finite archives without inheriting compression claims from a teacher.

## 2026-09-05 - Execute bounded comparisons against the updated frontier

The active objective is now `gamma-enwiki9-hutter-99m-v2`: at most
99,000,000 complete submission bytes. The 105M v1 contract and every historical
objective digest remain unchanged. `operations/provenance/competitive_frontier_v1.json`
retains September 5 source snapshots and separates the official displayed record
from contingent published submission figures. Endpoint428's 109,389,323-byte
forecast has 10,389,323 bytes of planning debt; no full-corpus deficit is measured.
Committee reference/accounting questions are drafted in
`workbench/committee-inquiry.eml` and have not been sent.

The existing release tools passed a real synthetic canary:
`results/release_canary_rle_q0_v1/release/20260905_acceptance_v1/canary-validation.json`.
Three independently built copies encoded 7,616 bytes into 2,998 archive bytes,
repeated the archive exactly, and decoded without corpus access. The counted
canary total is 5,403 bytes, including package and options; objective credit is
zero. Missing manifest/build files, tiny input presented as full enwik9, and a
canary presented as an objective receipt were rejected. Guard logs and declared
license notices are retained. This closes a release-machinery gate, not a
compression hypothesis or full-corpus certificate.

`lib/predictor.py` now supplies a reusable pre-truth Q16 bit interface with
explicit frontend identity, decoded-bit updates, deterministic state serialization
and trace-reuse bindings. Fixtures check encoder/decoder probability and state
agreement and reject silent frontend exchange. The existing `lib/driver.py`
runs frozen parent/bookkeeping/treatment/control arms from one candidate build,
retains exact/repeat artifacts and first-divergence diagnostics, then publishes
an atomic decision. Optional telemetry failures become missing diagnostics;
mandatory evidence remains necessary for promotion. No fixture compression is
credited to Gamma's competitive frontier.

HORIZON retains its original experiment predicates and sole observer. Its
recovery cannot recreate missing continuous resource certification. Independent
public-transformer reproduction and the smallest missing deep-MIDAS initializer
are bounded discovery work; shared-host timing is diagnostic. Fiber-FOSSIL's
failed exact-retrieval configuration remains retired. No joint gain or new
transformer compression inheritance is assumed.

## 2026-09-04 - Fiber-FOSSIL exact semantic retrieval is retired

The corrected opening-1M gate
`wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1` completed with an
authoritative decision. Every evidentiary control passed: the raw inverse and
all eight finite-coder inverses were exact, the repeated semantic tape and
probability construction were identical, `P == K`, the output manifest was
complete, active-HORIZON access was denied, and the owned 512 MiB/zero-swap
cgroup peaked at 273,793,024 bytes and was removed without residue.

The scientific hypothesis was decisively refuted. Parent `P`, bookkeeping `K`,
and inactive opening-scope physical control `G` each produced a 173,859-byte
payload. Same-route exact-continuation `D` produced 173,937 bytes, a loss of 78
bytes instead of the required 4,080-byte saving. Its minimum chronological-third
saving was -42 bytes, its minimum control margin was -42 bytes, and it had zero
positive virtual-distance buckets. Only 311 bytes activated `D`; 253 donor
bytes were correct, confirming again that correct-byte counts do not establish
retained information against a mature parent.

This retires the frozen Fiber-FOSSIL same-route 16-byte exact-retrieval axis and
its dependent Fiber-LOOM/route-fast-weight successors without a parameter
sweep. It does not retire HARM-Delta. HARM-Delta remains a distinct experiment:
it aligns complete prior route values through causal match/substitute/insert/
delete state rather than requiring exact 16-byte lockstep. No Fiber result is
credited to or subtracted from HARM-Delta.

Evidence: `results/wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1/decision.json`,
`results/wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1/receipt.json`,
and `operations/adaptive/reflections/20260904T212450Z_50c3d23da3.json`.

## 2026-09-04 - Independent opening-1M gates may overlap HORIZON

The user's instruction, "we can do things in parallel", supersedes the
scheduling-only wait in the eligibility-first strategy. The active HORIZON
trace and its observer remain unchanged, and HORIZON-dependent analysis still
requires validated terminal recovery. Host admission found 16 physical cores
and 105,779,836 KiB of available memory. The independent CMIX identity gate is
bounded to 10,000,000,000 bytes with zero swap; Fiber is bounded to 536,870,912
bytes with zero swap. Shared-host timing receives no official runtime credit.

The sealed CMIX env8192 v13 runner passes its existing validation unchanged.
It can execute the opening-1M comparator, repeated treatment and exact decode
on CPU 2 under its own managed lease. Its resource eligibility remains N_A
and it authorizes no larger gate. Fiber v8 cannot execute through the current
adaptive workflow because its frozen workflow digest is stale. New v9
preserves the byte-identical v4 scientific core and the v8 runner after
namespace substitution, including all controls, HORIZON denial and
decision-last authority. It binds the current workflow and unique output
namespace at tree `43db3b59add06042b97fdd935cb56b8a00a9c1133a4fe400ea6320dc08468b3b`.
Contract and candidate validation pass. Synthetic lifecycle validation passed
the 512 MiB cap, zero swap, hard address-space limit, HORIZON denial, child
exit and same-inode cgroup cleanup with a 14,544,896-byte peak. The independent
Fiber CPU is 3. Queue records and exact
terminal receipts remain the execution authorities; this decision grants no
measured gain or score.

Geekbench 5 preparation proceeds independently. Its official version-specific
download is identified, but no qualifying local executable or current-host
raw report was found. No calibration or larger CMIX gate follows from that
preparation alone.

Evidence: `operations/planning/hutter_parallel_opening1m_20260904.json`,
`operations/evidence/20260904_cmix_env8192_v13_parallel_launch_static_audit.json`,
`operations/evidence/20260904_cmix_env8192_v13_parallel_validation_only.json`,
`operations/evidence/20260904_fiber_fossil_v9_parallel_validation_only.json`,
and `operations/provenance/geekbench5_runtime_authority_preparation_20260904.json`.

The shared-workspace workers consumed CMIX job
`20260904T205826Z_fdcae0ea3e` and Fiber job
`20260904T205845Z_7dcfb4f773` before this coordinator's planned launch.
CMIX entered its guarded comparator on CPU 2. Fiber failed before its denial
probe, candidate import or corpus access: the enqueue command omitted the
required `--scratch-directory
results/wiki_fiber_fossil_endpoint428_opening1m_q0_v9`. Its output directory
remained absent. This is a launch-configuration failure, not a scientific
result. The same sealed v9 can be retried with that argument after a validated
retry reflection. The canonical enqueue operation rejects an occupied CMIX
lease, so retry admission waits for that owner to release its lease; no lease
is removed or bypassed.

CMIX's comparator subsequently terminalized with its exact frozen
172,605-byte payload and 464,298-byte archive, no outer resource violation,
and verified lease cleanup. The stage failed its combined codec-exit or
internal-telemetry check and discarded the execution dictionary. The exact
trigger therefore remains unknown. Source review identified a disappearing
child between `/proc` stat and I/O reads, missing durable failure telemetry,
and an affinity check that rejects the guard's valid empty terminal sample.
The v13 reflection is infrastructure-failure/not-tested/retry, with no
scientific kill or promotion. New v14 is restricted to correcting those
execution defects while preserving the codec and opening-1M experiment.

Fiber retry `20260904T210420Z_720cd4eb87` correctly precreated its output root,
then failed before science when the unchanged access guard rejected its own
`horizon-denial-probe.json` diagnostic filename. Its reflection records an
implementation failure. Our selected correction keeps that guard policy and
the exact scientific core, renames the diagnostic, and exercises the actual
guarded diagnostic publication in synthetic validation. Concurrent workspace
edits occupied the proposed v10 namespace, so this coordinator's correction
uses the distinct `wiki_fiber_fossil_endpoint428_opening1m_receiptfix_q0_v1`
identity. The unrelated v10 candidate is not adopted or launched here.

Evidence: `operations/evidence/20260904_cmix_env8192_v13_p_terminal_failure.json`,
`operations/evidence/20260904_cmix_v13_terminal_telemetry_diagnosis.json`,
`operations/adaptive/reflections/20260904T205826Z_fdcae0ea3e.json`, and
`operations/adaptive/reflections/20260904T210420Z_720cd4eb87.json`.

The correction-only CMIX v14 is sealed at candidate tree
`0079bc6e5aaedc3e9237e15499fe2fcbf22cd5e89e452d464a338c7978346759`.
Its source closure is
`2606d31563ec33cfc4be41ab78b2f4793110e30f64a336439e2ca6231f4d42ed`.
Validation records 13 process-lifecycle cases and six terminal-affinity cases.
Per-process I/O samples remain diagnostic; unique-tree I/O totals are unknown
because parent counters may include waited-for children. The inherited v13
memory guard, original codec, P/E-A/E-B/decode arms, package accounting and
opening-1M authority remain unchanged. Fiber receiptfix-v1 is sealed at tree
`1cf407a40b2258071c6d0c201c9b4057eb061463861ac3ca0af5756dc387a847`.
It preserves the access classifier and scientific core while publishing
`source-access-denial-probe.json`. Its synthetic validation now exercises that
actual guarded publication and readback under the resource cap. Both
corrections require their own validated queue records and unique output roots;
neither inherits a scientific result from the failed wrappers.

Fiber's capped validation passed actual diagnostic publication and readback,
one denied synthetic access, a 14,819,328-byte memory peak, zero memory events,
successful child exit and verified cgroup removal. Evidence:
`operations/evidence/20260904_fiber_fossil_receiptfix_q0_v1_guarded_publication_validation.json`,
`operations/evidence/20260904_cmix_v14_lifecycle_affinity_preflight_validation.json`,
and `operations/provenance/cmix_v14_independent_source_review_20260904.json`.

Fiber job `20260904T212450Z_50c3d23da3` completed successfully with a valid
scientific miss. The exact D payload is 173,937 bytes versus 173,859 for P/K:
78 bytes larger, against the required 4,080-byte saving. D loses bytes in all
three chronological thirds and all six distance buckets. All inverse,
repeatability, denial, output-manifest and cgroup-lifecycle checks pass. Peak
cgroup memory is 273,793,024 bytes, with zero memory events and zero swap.
The independently verified reflection retires this frozen exact-retrieval
configuration; it gives no archive or full-corpus score credit. The canonical
run-ledger entry retains null complete-package metrics and binds a diagnostic
registration outside the immutable 22-output namespace.

CMIX v14 job `20260904T212504Z_3be6dfb803` entered execution under the published
source and queue ownership. Host inspection verified its comparator process
on CPU 2, with the 10,000,000,000-byte requested cap rounded down by the kernel
to 9,999,998,976 bytes, zero swap and no resource violations. Its native guard
and persistent candidate worker own execution through P/E-A/E-B/decode.
HORIZON remains nonterminal under its existing observer; no partial science
access or duplicate monitor is introduced. Neither live operation authorizes
a larger gate before its frozen terminal requirements are evaluated.

Evidence: `operations/evidence/20260904_fiber_fossil_receiptfix_q0_v1_terminal_independent_audit.json`,
`operations/adaptive/reflections/20260904T212450Z_50c3d23da3.json`,
`operations/evidence/20260904_fiber_receiptfix_canonical_ledger_registration.json`,
and `operations/evidence/20260904_parallel_opening1m_live_handoff.json`.

The v14 comparator subsequently stopped on a now-localized implementation
failure. Its retained execution report proves codec exit zero and identifies
the exact previously sampled process as a zombie before and after its I/O
read returned EACCES. The v14 classifier handles vanished processes but still
rejects this terminal-zombie case. Treatment and decode arms did not execute;
the reflection is implementation-failure/not-tested/retry. The selected
correction requires an earlier successful sample of the exact same PID and
start ticks plus stable Z/X terminal state. Unreadable live, unsampled or
reused process identities remain fatal. This new revision preserves all codec,
opening-1M, source-accounting and resource requirements.

The correction is materialized as
`cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1`, with sealed source closure
`2ca009caca219f8a2e7b65bc611c933ac095d0a72e1e3d0cabfda32830f18abc`.
Its lifecycle validation includes the retained v14 observation and requires
prior successful exact-identity sampling for terminal EACCES. Nonterminal,
never-sampled, changed-identity and other unreadable cases remain failures.
The experiment contract validates, and the original four-arm opening-1M
identity procedure and resource limits are unchanged. Evidence:
`operations/evidence/20260904_cmix_zombiefix_lifecycle_source_validation.json`
and `operations/evidence/20260904_cmix_zombiefix_final_preflight_validation.json`.

Job `20260904T213959Z_0fd9095639` now passes the complete frozen opening-1M
identity gate. P, E-A and E-B each produce the exact baseline 172,605-byte
payload and 464,298-byte archive. The env8192 archive decodes to the exact
canonical 1,000,000 bytes. All four guards and terminal execution receipts
pass, including one retained, previously sampled terminal-zombie EACCES event
per arm. Peak cgroup memory is 8,587,251,712 bytes; scratch, owned cgroups and
the canonical lease are removed. The counted opening package is 955,881 bytes,
including the 100 command bytes. This is output-identity evidence only:
memory, runtime and PPM-trigger eligibility remain N_A, and full-corpus score
credit is zero. The canonical reflection is valid/supported/hold, with no
larger-gate authority. The next constructive CMIX step is a separately frozen
resource experiment, including runtime authority, before larger execution.

Both independent opening gates are now terminal: CMIX identity passes and
Fiber's frozen retrieval configuration is retired after its scientific miss.
HORIZON remains observing under its existing native observer, without early
science access. The full objective remains unproved. Exact final handoff:
`operations/evidence/20260904_parallel_opening1m_terminal_handoff.json`.
CMIX's canonical ledger registration is
`operations/evidence/20260904_cmix_zombiefix_canonical_ledger_registration.json`.

The sealed correction then completed all four opening-1M arms. P, E-A and E-B
each reproduced the exact known 172,605-byte payload and 464,298-byte archive;
E-A decoded exactly to the canonical 1,000,000-byte prefix. Every arm retained
one prior-sampled, same-PID/start terminal EACCES event and no other telemetry
error. The 42-file output closure, lease, cleanup and one-CPU/zero-swap guards
all passed. This supports output-neutral identity only: observed peak cgroup
memory was 8,574,197,760 to 8,587,251,712 bytes, resource eligibility remains
N/A, and no larger gate is authorized. A separate prospectively frozen
resource experiment is mandatory. Evidence:
`results/cmix_obias_source_ppm_rss_env8192_zombiefix_q0_v1/decision.json`,
`operations/evidence/20260904_cmix_zombiefix_opening1m_terminal_independent_audit.json`,
and `operations/adaptive/reflections/20260904T213959Z_0fd9095639.json`.

## 2026-09-04 - Adaptive ranking now respects candidate lifecycle

The proposal ranker previously considered proposal status, experiment
validity, and parent reflection but not the developed candidate's own state.
That made the live HORIZON trace and already reflected, held HARM-Delta source
fixtures appear eligible for duplicate scheduling. `enwiki9_reflections.py`
now overlays candidate metadata and all durable queue states before granting
eligibility. Pending or running candidates, candidates marked
`blocked_dependency`, `measured_negative`, or `retired`, and candidates whose
latest terminal job still awaits reflection are fail-closed. A reflected
`retry` or `next-gate` remains actionable.

Nine focused tests cover held/negative/retired states, pending and running
jobs, the latest-terminal reflection barrier, reflected retry, and an
undeveloped proposal. The real inventory check now excludes both running
HORIZON candidates and all four reflected HARM-Delta source prerequisites.
This is scheduling-integrity evidence only; it changes no candidate,
probability, experiment population, scientific result, archive, or score.

## 2026-09-04 - Live Hutter rule authority remains byte-identical

The official task, detailed-rules, and FAQ pages were fetched directly over
HTTPS and rehashed. Their returned sizes and SHA-256 values remain exactly
equal to the frozen authority documents in
`hutter_prize_rules_20260822`: `48,606` bytes and
`065186dc3e6ef61f295aa30873c142bd6e4a2f6f310cfbd1d28ec09cbc6cbff7`,
`15,907` bytes and
`e55d9f96b227e61ec0996adaf36304185d74db8c17093b403bb325240b2dc163`,
and `96,252` bytes and
`9233864b9ab2ce7b75ca2092416b518b196fcd498ab4e70e8c8f20b1bc42f52b`.
No rule migration is required: the published record remains `110,793,128`
bytes, the minimum eligible next score remains strictly below `109,685,197`,
and Gamma's `105,000,000`-byte objective remains the stronger threshold. The
single-CPU-core, no-GPU, decimal-`10 GB` RAM, decimal-`100 GB` temporary-disk,
Geekbench5 wall-time, necessary-option-byte, self-contained execution, and
public documented OSI-source requirements remain binding.

This is rule evidence only. It grants no candidate score, package, resource,
or eligibility credit, and the live pages must be checked again immediately
before an actual submission. Evidence:
`operations/provenance/hutter_prize_rules_20260904_revalidation.json`.

## 2026-09-04 - Reflected exact HORIZON recovery bridge is sealed

`endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3` closes the
single admissibility gap created when the original retained-parent controller
disappeared but its exact wrapper and CMIX child continued. It is a new
zero-credit candidate, not a repair or mutation of the active v1 source. The
only scientific input change is evidence admission: v3 requires the
prospective orphan observer to publish a validated `SEALED_IMMUTABLE_TRACE`
result with both adopted identities absent, complete geometry, unchanged
static inputs, no scientific access, and
`continuousResourceProofPass=false`. A valid adaptive reflection must bind the
exact recovery-result digest before any probability row is opened.

V3 does not synthesize the missing terminal v1 decision or pretend that
forward observation repairs the stopped resource guard. It verifies the
candidate snapshot and complete source binding before trace access. It then
resolves `parent.p1`, `parent.archive`, and `manifest-a.bin` only through the
recovery receipt; checks regular-file, one-link, size, digest, device, inode,
timestamp, and trace-header identity; and rehashes those inputs after analysis.

The scientific code remains byte-identical. Two independent builds and runs
of the frozen v1 floating-posterior analyzer must agree. Two independent
builds and runs of the frozen exact-v2 unsigned-`__int128` analyzer must agree.
The latter's embedded legacy trajectory must reproduce the former's complete
aggregate values. The arbitrary-precision Q63 fixture, exact `2^63` half-up
law, `2,331,505` active coordinates, D/S/R/N controls, chronological thirds,
and `40,163,160`-bit target-bearing gate are unchanged. Each phase uses one
logical CPU. The diagnostic analyzer ceiling is `9,500,000 KiB`, below the
official decimal limit; this accommodates the frozen sparse `mmap` working set
and conveys no native resource authority.

The selected candidate is sealed at tree
`39e29c51d13b3b16c1178007d1c98de981b220018e017191199ebf5416f9323f`
and remains dormant while the observer is live. The independently prepared
`endpoint428_horizon_retained_parent_trace_recovered_exact_q0_v3` tree
`a236ae6296c7bb86fd3c804fb8bd75e5ca8a32c4a548b411f9d05f6b164e2946`
is retained but will not execute: its `1,048,576 KiB` ceiling is not credible
for the frozen sparse mapping and it omitted the required adaptive reflection.
This is a pre-execution infrastructure rejection, not HORIZON evidence.

A complete selected-v3 pass may authorize only a recovered-dependency version
of the already-planned native P/K/D implementation. It grants no archive
score, inverse proof, package credit, composite resource evidence, or Hutter
result. Recovery, identity, fixture, repeat, legacy-crosscheck, or resource
failure invalidates the analysis attempt without judging HORIZON. With those
foundations valid, missing target scale, any nonpositive third, or any failed
control margin retires physical HORIZON without reinterpretation.

Evidence:
`operations/planning/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.json`,
`operations/adaptive/experiments/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.json`,
`operations/adaptive/proposals/developed/000_endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.json`,
`operations/adaptive/candidate-revisions/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3/20260904T142927224038Z_39e29c51d13b.json`,
`programs/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3/`,
and
`tools/endpoint428_horizon_retained_parent_trace_exact_recovery_q0_v3.py`.

## 2026-09-04 - Isolated open dP is terminal negative; only integrated replay remains

The open top-attention probability-adjoint lineage has a valid terminal
scientific answer. Two v2 jobs failed before arithmetic because their runners
compared raw `meta.json` bytes against revisions whose identity contract uses
`semantic-meta-v1`; those jobs are implementation evidence only. The single
correction-only v3 then executed the complete `5,242,880`-word population twice
under external single-core resource guards. Scalar and AVX2/FMA treatments are
byte-identical, both repetitions are exact, the negated control is live, the
source package and dependency closure pass, and no work tree survived.

The frozen primary source-layout predicate nevertheless fails. Treatment and
source differ at `5,197,470` BF16 words. The prospectively registered alternate
serialization, originally labeled the wrong-layout control, equals all
`5,242,880` source words exactly and has SHA-256
`94763dc5ad7c78020c2620a06b0824fd7f2280c6a2a4c3783618931da44dbe22`.
The open kernel emits `state,head,stream,key`; the retained source tensor is
`state,stream,head,key`. This is an exact representation bridge, not a passed
isolated dP gate.

A separate read-only verifier independently recounted the treatment mismatch,
materialized the fixed permutation twice, reproduced the source digest, and
validated the population, repeats, controls, resource receipts, package,
dependency log, cleanup, terminal job, and source reflection. Its valid
reflection promotes only that zero-credit bridge. The OMEGA exclusion retires
the frozen source-equivalence claim and every further isolated dP layout,
permutation, tolerance, or correction successor. V3 receives no arithmetic,
compression, package-score, or objective credit.

The only allowable MIDAS continuation is
`nncp_open_integrated_midpoint_segment_replay_65536_q0_v2`. Its modern
experiment and proposal are prospectively frozen and validate, but the proposal
is `dormant_dependency`. It preserves three exact boundaries: the retained
`65,536`-row, `917,527`-branch F/O probability population; the one-boundary open
chain in which all `246` Adam parameter payloads, `20` memory layers, `244`
next-forward tensor groups, and `896` branch rows match; and the exact dP layout
bridge. Those boundaries do not compose themselves.

Activation still requires a complete open backward that generates every update
target without captured teacher gradients, a canonical full-population lock for
model, optimizer, recurrent, attention, cache, truth, activation, and oracle
state, and one sealed LibNC-free integrated runner. Missing closure keeps the
experiment dormant and is not a MIDAS failure. No more disconnected backward
primitive is authorized. Even complete integrated parity would remain a
zero-credit causality proof; finite archive gain would require a later compact
native candidate and fresh replay.

Source implementation has begun inside that single integrated identity without
activating or executing the experiment. Revision
`651287cce12b60e38e5e49b058a4b04cccf55317098a529b0d5e42151bac9e98`
implements a canonical duplicate-key-safe input-lock inspector and a one-thread
LibNC-free C++ arithmetic library. The library consolidates the already
attributed BF16 rules for flat and chronological-state parameter reductions,
ordered 128-coordinate transpose panels, final-root and sequential RMSNorm
backward, GEGLU, residual joins, causal loss residuals, scalar softmax backward,
the value-product probability adjoint, and the frozen head/stream layout bridge.
Seven local source tests pass, including compilation with AVX2/FMA and disabled
implicit contraction. Replay remains fail-closed: full forward caches,
remaining attention/QKV backward, optimizer/state traversal, population input
lock, oracle parity, repeats, and resource closure are still absent. This is an
implementation checkpoint with zero scientific or objective credit.

A second source-only revision,
`08b47bf743395906b76884a03f28b5e2646555dcd7fe886c3b56198e8186a669`,
now implements a candidate complete reverse topology. It adds content and
relative attention adjoints, Q/K/V and projection paths, reverse traversal of
all transformer layers, shared `b_r_0` accumulation, the output and final-norm
roots, the F32 embedding gradient, and the exact 246-entry production gradient
descriptor order. Release and ASAN/UBSAN self-tests pass, and the focused
seven-test source suite still passes. This does not yet satisfy the
`complete_open_backward` dependency: several previously unattributed reduction
schedules remain implementation hypotheses until the treatment materializes
all 246 payloads and compares them against prospectively bound oracles. No
teacher gradient payload was read as a treatment input, and this checkpoint
receives zero arithmetic, compression, archive, package, or objective credit.

A third source-only revision,
`d4e5927df08df92d42d5b0f5e5f5cd56ce40710da5f30f3b04fa5e29389a7192`,
closes the source-materialization boundary without activating the experiment.
It adds a bounds-checked tensor-container parser, an exact production fixture
loader that refuses to consume retained `train_h` activations as treatment
inputs, a candidate full open transformer forward, and a separate treatment
executable with no oracle-path argument. The executable binds every produced
gradient to the canonical 246-entry descriptor sequence and emits typed
BF16/F32 payloads plus checkpoints through collision-refusing partial files,
with its completion marker written last. A small end-to-end emitter test,
release build, ASAN/UBSAN build, and the seven focused source-contract tests
pass. Forward checkpoints and all 246 gradients have not yet been compared to
prospectively bound teacher payloads, so the arithmetic remains unvalidated
and this revision receives zero scientific, compression, package, or objective
credit. Adam, recurrent transition, midpoint rebuild, population locking, and
the O/K/F/S replay remain missing.

A fourth source-only revision,
`a9261969f38c518eaee3b365213672a40d1369434e010ad7e4c824c6bfadf93b`,
composes the next previously exact boundaries without running the production
population. It loads the 491-tensor optimizer state under exact names, types,
shapes, and configuration; binds it to the same canonical parameter/gradient
topology; and implements per-tensor norm and clipping, compensated BF16 low
words, the F32 embedding path, second-moment state, and the two-update bias
correction schedule. The update-5 scalar schedule matches the retained exact
Adam receipt bit-for-bit. It also implements the decoder-visible recurrent
shift-and-append law and the frozen segment sequence: zeroed future graph,
first-half update, full causal rebuild without shifting persistent memory,
second-half update, and one end-of-segment memory shift. Synthetic topology,
causality, exact-repeat, release, ASAN/UBSAN, and focused contract tests pass.
The test changes second-half inputs and truths and confirms first-half
probability identity. This remains an unvalidated implementation: no
production treatment has been materialized and compared against forward or
all-gradient oracles, no complete-population state lock exists, and O/K/F/S
have not run. It receives zero arithmetic, compression, archive, package, or
objective credit.

A fifth source-only revision,
`28a2f9b6960eeac24ec9644f036e0e90bdf3fa0d32c2bffe37f80dc303203580`,
adds the isolated production-comparator boundary without reading any retained
gradient payload during implementation. The treatment executable still has no
oracle argument. A separately linked comparator first requires the completed
full-comparator treatment marker and exact zero-teacher-input receipt; only
then may it open the retained oracle fixture. It verifies the canonical
metadata and every byte of all `246` gradient payloads plus all `20` rebuilt
`train_h` tensors, accounts for length differences, records the first differing
byte, and emits a collision-refusing zero-credit receipt. Release and
ASAN/UBSAN builds, the focused seven-test suite, and synthetic exact,
one-byte-different, and incomplete-treatment cases pass. No production oracle
comparison has run, so exact arithmetic parity, compression gain, package
credit, and objective credit remain unproved and zero.

A sixth source-only revision,
`2dcf287e75f259565c1bf44ea932c98cc91adccf2612dedec677fc2ea95404a4`,
implements the four frozen segment arms without activating the population.
F commits the complete first-half gradient; O computes and commits only
`embed_out` and `out_bias`; K executes the complete backward bookkeeping but
commits exactly those same two gradients; and S changes only the first-half
truth association to the frozen next-state cyclic control. All arms then use
the same causal rebuild, complete second-half update, and one terminal memory
shift. The selected Adam path advances the global exponent while preserving
every unselected parameter, low word, and moment. On a synthetic causal model,
O and K are bit-identical across probabilities, parameters, optimizer state,
and memory, while S is identical before the update and changes the rebuilt
probabilities. Release, ASAN/UBSAN, and focused source tests pass. Production
parity and all compression and objective credit remain unproved and zero.

A seventh source-only revision,
`90f33d9a2229c7d712b9edef9dd81203174b66db73013bbd55af627189edd6c8`,
separates probability production from retained-teacher inspection. The
treatment side now writes a compact collision-refusing branch trace using the
attributed LibNC AVX2 reduction, balanced-tree path, and integer quantization;
it accepts no oracle path and seals its completion header only after every row
is closed. A separately linked comparator then checks the completed candidate
against the retained NNNTR4 population by original coordinate, execution
order, symbol, vocabulary, truth branch, branch count, and integer
probability. Synthetic exact and one-count-different traces pass their expected
verdicts under release and ASAN/UBSAN builds, and the focused seven-test source
suite passes. The production 65,536-row trace has not run, so this is still
zero-credit implementation evidence and establishes no arithmetic parity,
compression gain, archive saving, or objective progress.

An eighth source-only revision,
`44116ba66e9d6c05f29a1a03c6be6a60d5ff6aee257925d8e8e5de02438cc082`,
implements the complete treatment trajectory without activating it. It reads
exactly 65,536 big-endian symbols, bridges the 32 stream-major sequences into
32 model-update batches of 64 states, and preserves the distinct count of
1,024 per-stream analytical segments. Original coordinates are checked for
complete one-to-one coverage. Each batch executes the frozen O, K, F, or S
two-update law at the exact parent-batch learning rate and emits only a compact
integer branch trace plus SHA-256 witnesses over every future-affecting model,
compensated low-word, Adam-moment, update-exponent, and recurrent-memory byte.

The treatment executable has no oracle parameter. Its separately linked
comparator requires the exact four-file output closure, a complete 32-batch
state-witness trajectory, and explicit zero teacher/oracle inputs before the
retained trace path is opened. Known-answer SHA-256, symbol decoding,
coordinate mapping, q3 learning-rate bits, state sensitivity, exact/mutated
trace comparison, and pre-oracle rejection tests pass in release and
ASAN/UBSAN builds; the focused seven-test suite also passes. Activation still
requires a prospectively bound block-zero parameter, optimizer, recurrent
state, and symbol fixture plus its complete input lock. No production arm has
run, so all arithmetic, compression, archive, package, and objective credit
remain unproved and zero.

A ninth source-only revision,
`cc0c7f3c292ee97eac4acea145fb5086247411bcc08f098980c7c312e4fb8789`,
hardens that pending block-zero boundary. The production population executable
now uses a distinct initial-state loader that accepts only the two symbol
tensors and one recurrent-memory tensor per layer. It rejects every retained
`train_h` activation and every extra tensor; the activation-bearing q3 fixture
format remains confined to the separate bounded comparator loader. A synthetic
stripped state loads exactly, the corresponding activation-bearing state is
rejected, and release, ASAN/UBSAN, and focused source tests pass. The required
block-zero fixture has not been materialized and no production replay has run,
so this remains zero-credit implementation evidence.

A tenth source-only checkpoint freezes the missing block-zero producer without
executing it. The first proposal, q0 v1, was rejected at development because
its intended q3 lifecycle parent has historically valid oracle evidence but an
obsolete runtime-source binding: the current validator correctly refuses to
treat that legacy experiment as live successor authority. Q0 v2 is therefore a
standalone oracle candidate. It still hash-binds q3's decision and reflection
as evidence, the exact `cc0c7f3c292e...` Gamma consumer tree, and the rejected
v1 registration, but claims no parent-derived credit.

The v2 runner patches the exact retained LibNC source immediately after model
reset and exits before the first normal forward loop. It directly constructs
the causal block-zero input/target batch from the frozen 32-by-2,048 stream
partition and permits only `246` initial parameters, `491` optimizer tensors,
`20` zero recurrent memories, and the exact `65,536`-symbol BE16 population.
`train_h`, gradients, post-update state, and teacher probabilities are absent.
The patch compiles, its standalone self-test passes, and four focused tests
pass. Revision `eee5b268497a7ca1bce7736f3f3a91ef6833cf141086677b4313d77f89504108`
is sealed. Its guarded enqueue command is frozen but execution remains disabled
until HORIZON terminalizes and releases the heavy lane. No fixture has been
materialized, no MIDAS arm has run, and all scientific, compression, package,
and objective credit remains zero.

Evidence:
[`v3 decision`](../results/nncp_open_top_attention_probability_adjoint_64_q0_v3/decision.json),
[`terminal verification`](../results/nncp_open_top_attention_probability_adjoint_64_q0_v3_terminal_verify_q0_v1/verification.json),
[`valid reflection`](../operations/adaptive/reflections/20260904T152612Z_cde41120fb.json),
[`OMEGA exclusion`](../operations/adaptive/exclusions/nncp_open_top_attention_probability_adjoint_64_q0_v3_source_layout_negative.json),
[`integrated v2 plan`](../operations/planning/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2.json),
[`integrated v2 experiment`](../operations/adaptive/experiments/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2.json),
[`integrated source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T182911157959Z_651287cce12b.json),
[`complete-topology source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T184647005158Z_08b47bf74339.json),
[`forward and treatment source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T191749467383Z_d4e5927df08d.json),
[`Adam and midpoint-segment source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T193633977336Z_a9261969f38c.json),
[`post-treatment comparator source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T195020353197Z_28a2f9b6960e.json),
[`O/K/F/S segment-arm source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T200044496649Z_2dcf287e75f2.json),
[`treatment-only branch-trace source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T201112895649Z_90f33d9a2229.json),
[`complete population-driver source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T202742577734Z_44116ba66e9d.json),
[`stripped initial-state loader source revision`](../operations/adaptive/candidate-revisions/nncp_open_integrated_midpoint_segment_replay_65536_q0_v2/20260904T203102394482Z_cc0c7f3c292e.json),
[`rejected legacy-parent initializer proposal`](../operations/adaptive/proposals/rejected/000_nncp_libnc_profile_initial_fixture_65536_q0_v1.json),
[`standalone initializer experiment`](../operations/adaptive/experiments/nncp_libnc_profile_initial_fixture_65536_q0_v2.json),
[`standalone initializer proposal`](../operations/adaptive/proposals/developed/000_nncp_libnc_profile_initial_fixture_65536_q0_v2.json),
[`standalone initializer source revision`](../operations/adaptive/candidate-revisions/nncp_libnc_profile_initial_fixture_65536_q0_v2/20260904T205258240267Z_eee5b268497a.json),
[`held initializer execution plan`](../operations/planning/nncp_libnc_profile_initial_fixture_65536_q0_v2.json),
and
[`integrated v2 proposal`](../operations/adaptive/proposals/proposed/934_nncp_open_integrated_midpoint_segment_replay_65536_q0_v2.json).

## 2026-09-04 - PALIMPSEST-MARKET-v2 is frozen as a nested finite-coder shadow

`palimpsest_market_v2` is the separately versioned successor to the retained
HARM mechanism, not a revival of the historical broad PALIMPSEST factorization.
The old portfolio warning remains binding: semantic elegance does not excuse
parser, realization, source, framing, model, table, package, runtime, or memory
cost. The proposal is therefore `dormant_dependency` while the active HORIZON
experiment continues unchanged. No corpus replay may read HORIZON's scientific
outputs before its fail-closed terminal route.

The later explicit PALIMPSEST directive supersedes the earlier instruction to
retain only HARM-Delta when deciding whether this shadow may be frozen. Its
nested arms are matched ablations inside one zero-credit experiment, not a
combination of separately measured score gains. The prohibition on a broad
replacement codec and on adding gains across changed probability trajectories
remains fully binding.

The frozen nested arms are `P/K/A/M/H/T/X/C/G`. A is exactly HARM-Delta's
latest completed exact-route value and generic causal edit transducer. M changes
only the exact-route reservoir depth from one to eight. H adds only normalized
route-shape and content-type backoff, with current content type inferred from
the already decoded value prefix. T adds one fixed typed leaf per unchanged H
donor: signed-integer affine variants, delimiter-preserving substitution,
bounded token alignment, or prefix/suffix grafting. X preserves T geometry but
permutes donor routes within power-of-two age and length buckets. C retains the
correct donors and generic leaves but changes every typed-kernel assignment to
a different valid kernel. G uses physical-history donors matched to each H
donor's exact causal age, content type, and length bucket. P is immutable;
K executes all bookkeeping while sending only P to its coder.

All markets use fixed factorized priors: equivalence masses `8/5/3`, newest to
oldest ancestor masses `128/64/32/16/8/4/2/1`, and generic-to-typed masses
`3/1`. Per-occurrence leaf weights and the global parent-versus-market weight
use exact Q63 sleeping Bayesian updates. A sleeping leaf is multiplied by the
awake market truth count, preserving its relative mass; transducers update only
after the complete truth byte. Coin betting is excluded from v2 and can enter
only as a new one-axis successor.

The decision surface is literal finite arithmetic, not ideal gain. Every arm
owns a 32-bit E1/E2/E3 arithmetic interval, explicit bit-count frame,
termination, byte padding, and decoder replay. P and K must match at every Q16
probability, interval transition, payload byte, and hash. Actual payload,
framing, source, model, table, and transmitted package bytes enter economics.
Process-tree memory and measured runtime remain separate hard gates and are
never converted into fictional byte charges. Bootstrap and ideal-log-loss
summaries are diagnostic only.

The prospective populations remain canonical raw opening `[0,1,000,000)` and
distant `[500,000,000,510,000,000)`, state-warm from raw byte zero. T must save
at least `5,021` and `50,204` exact payload bytes respectively and be positive
in every independently terminated chronological third. M must beat A by at
least `9/82` opening/distant bytes, H must beat M by `33/328`, and T must beat H
by `66/656`; these are density screens for frozen incremental package ceilings
of `8,192`, `32,768`, and `65,536` full-scope bytes. T must also beat admissible
A/M/H/X/C/G controls economically on both scopes. Any extension failure stops
at the simpler surviving arm without a rescue sweep. Only a complete T pass
may authorize one new native candidate, which still requires fresh package and
composite resource evidence.

The source-only implementation now fixes the reservoirs, all four typed
kernels, hierarchical sleeping updates, matched controls, and independent
finite coder. It opens no corpus and grants zero credit. Repeated fixture replay
passes exact HARM-A probability identity, P/K probability/interval/payload
identity, X/G admissibility, every arm's finite decode, a 4,096-bit coder stress
roundtrip, and all typed-kernel exercises. The known-answer run SHA-256 is
`a0614457cd000abf604fbe333458fe883d55a44a4f2bb4bd62d2be61147c82fa`.

MIDAS is not privileged as a combination. A later study must measure both
conditional PALIMPSEST marginals given MIDAS active/asleep and reverse MIDAS
marginals given PALIMPSEST active/asleep. Dominant overlap routes to expert
competition. Complementary residuals may expose only decoder-visible posterior
entropy, selected transformation family, and parent-surprise gap, followed by a
fresh joint finite archive. Separate gains are never added.

Evidence: `operations/planning/palimpsest_market_v2.json`,
`operations/adaptive/experiments/palimpsest_market_v2.json`,
`operations/adaptive/proposals/proposed/000_palimpsest_market_v2.json`, and
`programs/palimpsest_market_v2/`.
