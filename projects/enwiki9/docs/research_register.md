# enwiki9 Research Register

## 2026-08-23 - canonical CMIX/q1 interpretation and corrected launch ladder

This section supersedes any wording that implied CMIX had already been
repaired, qualified, or improved. The frozen evidence state is:

```text
External archive size reproduced:          true
External payload reproduced:               true
Arm A exact canonical inverse:              true
Arm B independent encode identity:          true
Arm B independent full roundtrip:           false
Arm B decode completion:                    false, terminated at 39.07%
External implementation memory eligible:    false
File-backed q1 probability identity:         proven on bounded scopes
File-backed q1 compression improvement:      none
File-backed q1 full-1G qualification:        unproven
Gamma authorship credit:                     0
Gamma score credit:                          0
```

Arm B reproduced the `107,730,531`-byte payload and `108,022,224`-byte
self-extracting archive exactly. That proves two-run encode identity under the
bound external package. It does not prove a second roundtrip: decode stopped at
`39.07%`. The shared-scope OOM was the immediate infrastructure termination,
and `/dev/shm` scratch aggravated the pressure, but the CMIX process was also
independently ineligible at `VmHWM=10,425,744 KiB`, `660,119 KiB` above the
strict `9,765,625 KiB` ceiling. The correct classification is therefore
infrastructure-terminated plus implementation resource failure, not a
compression-math failure and not an environment-only excuse.

q1 is an identity-preserving eligibility correction. It has matched exact
post-head integer probabilities, traces, payloads, and decoded output on three
cold 250KB scopes, one cumulative opening 1M scope, and opening plus distant
cold-reset 10M scopes. It has not proved full-stream probability or state
identity, full-1G archive identity and inverse, runtime eligibility, package
closure, or any archive-byte improvement. The interior reset populations prove
parent/q1 decoded-output identity, not standalone raw inversion.

The corrected next-launch ladder reserves headroom for a Gamma mechanism. The
next newly launched expensive q1 gate, if terminal evidence still requires one,
is a 100M identity and phase-resolved resource run. It must bind parent/q1
integer probabilities, payload/archive identity, exact raw inverse, rolling
persistent-state identity, process-tree RSS, per-process VmHWM, cgroup peak,
phase-specific mappings and buffers, and scratch logical/allocated bytes. Its
engineering gate is at most `9,000,000 KiB`, not merely below the official
`9,765,625 KiB` ceiling. The prospective, execution-disabled arm separation
and terminal branches are frozen in the
[`100M gate`](../operations/planning/cmix_filebacked_fxcm_100m_identity_resource_q0_v1.json).
At that gate, “archive identity” is split precisely: the parent and q1
arithmetic payloads must be byte-identical, while each self-extracting archive
must be exact, invertible, and separately package-accounted. The complete
self-extracting files are not expected to be byte-identical because q1
necessarily contains different allocator code; requiring that equality would
confuse predictor preservation with package identity.

The diagnostic observer source, matched observer-build runner, calibration
runner/verifier, and joint 100M coordinator/verifier are now sealed; all
execution receipts remain absent. The coordinator refuses an active full-1G
lease, independently hashes the canonical opening prefix before creating its
result root, then runs instrumented `I-P` and `I-Q` roundtrips followed by one
observer-free `R-Q` release roundtrip. `R-Q` is guarded by cgroup v2 at the
strict `10,000,000,000`-byte hard cap and a restorable `9,000,000,000`-byte
`memory.high` pressure boundary. Its eight ordered phases independently record
process-tree RSS, per-process VmHWM, cgroup memory composition, and scratch
logical/allocated peaks. The independent verifier reconstructs every semantic
state-manifest digest, validates exact observer checkpoint geometry, and proves
that the release executable is the literal concatenation of the independently
built q1 binary plus the sealed dictionary, article-order, and header assets.
No syntax, schema, or hash-closure check is an execution result.

A subsequent adversarial proof audit found and closed one pre-execution gap:
the verifier had validated the release-stage receipt and the resource-guard
receipt independently without proving that they described the same child
command. The verifier now recomputes the guard's NUL-delimited argv digest and
requires it to equal both the release-stage command digest and the `R-Q` arm
binding. It also rehashes the soft-high wrapper's underlying v3 guard, binds
the wrapper and guard to the same cgroup path/inode and `memory.events.high`
count, and independently matches the raw 16-event phase-marker stream to the
eight ordered phase records. Both instrumented arms now schema-validate their
v2 guard receipts and bind the exact encode/decode argv, diagnostic labels,
limits, sampling, disk, and affinity observations. These are prospective proof
hardening changes only; they add no execution evidence or compression credit.
The same audit found that this detailed plan still named the generic dormant
campaign schema despite not conforming to it. The plan now validates against a
dedicated strict schema whose digest is pinned independently by both the
coordinator and verifier; the plan also carries that digest explicitly.
Observer build, observer calibration, calibration verification, joint
coordination, and joint verification now all invoke the same schema-pinned
plan validator before accepting or producing evidence.

The build runner requires two byte-identical builds within each I-P/I-Q arm
before packaging replicate A. The observer registers the
same source-ordered semantic ranges in both arms and requires exactly `26`
allocations of at least `67,108,864` bytes. At coded-byte checkpoints `0`,
`16,777,216`, `33,554,432`, `50,331,648`, and terminal, it hashes each range's
ordinal, requested semantic size, alignment, and exact semantic bytes. It also
hashes every post-head `uint16` probability immediately before the arithmetic
split and records clone-finalized coder checkpoints. Virtual addresses,
mapping padding, filenames, inode identities, page residency, and fault history
are excluded. The q1 diagnostic arm may page out already-hashed file-backed
ranges; therefore neither diagnostic arm has memory authority. The independent
`R-Q` arm remains the observer-free sealed release. Exact `--fuzz=0` patch
application and frozen-definition C++ syntax validation pass; no observer build
has been executed, and no calibration, 100M identity result, or resource result
is claimed.

Semantic-coverage audit: q1 can enter `AllocateBacked` only through the two
`fxcmv1.cpp` allocation templates, `alloc` and aligned `alloc1`, and only at
the same 64 MiB threshold used by the observer. The observer hooks both the
file-backed and ordinary allocation branches after allocation. `alloc` hashes
the exact requested object extent; `alloc1` hashes the aligned data pointer and
exact usable extent while excluding allocator/alignment padding. `Begin` then
requires all 26 runtime registrations before coding can start. Thus every
allocation whose storage implementation q1 changes is inside the state
manifest, while non-semantic mapping slack remains correctly excluded.

`cmix_filebacked_fxcm_full_a_qm8_v1` was already running when this launch-order
correction was adopted. It remains an unchanged zero-credit diagnostic and is
not killed or retroactively promoted. No new independent full-1G arm or native
compression mechanism is launched from bounded identity evidence alone. An
identity failure authorizes only first-divergence localization; identity with
insufficient headroom authorizes one phase-specific memory successor; failure
to create useful headroom moves the prize-facing primary lane to the compact
open NNCP student. New CMIX midpoint, MIDAS, SAFE-FORK, or structural mechanisms
remain execution-blocked until q1 is an exact memory-safe parent. Their eventual
archive effects require fresh joint replay and cannot be added algebraically.

## 2026-08-23 - WIKI-SCHEMA-VM replaces checkpointing as the primary new information-source proposal

SAFE-FORK is classified as checkpoint/fork/rejoin infrastructure, not a novel
compression algorithm. It may later contain an independently valuable causal
expert, but checkpointing CMIX does not itself address the `3,513,707`-byte
counted-score debt and receives no scientific priority on that basis.

The new zero-credit proposal is `wiki_schema_vm_ceiling_q0_v1`: a bounded
online virtual machine over opaque post-WRT bytes. It parses `PP`/`RR` template
invocations, conditions on the decoded template name, prior field key, and
field index, and learns deterministic next-key-plus-equals programs from
completed prior invocations. No rule identifier, value, dictionary decoding,
raw-corpus oracle, or future delimiter is transmitted or consulted.

A pre-measurement audit found that the first source draft updated its program
table at key completion, which would allow later fields to learn from the same
still-open invocation. The sealed implementation instead stages at most 64
state/target programs per template and commits them in source order only when
that invocation closes. Staging overflow discards that invocation's complete
staged learning set. Its `32,768 x 4` fixed table retains two deterministic
Space-Saving candidates per state; parser depth, atom lengths, collision
policy, replacement order, storage, and controls are all frozen.

Treatment D predicts only at causally selected field boundaries and stops at
its first mismatch. R substitutes deterministic SplitMix bytes at the exact D
positions. S uses the immediately preceding completed template-name state at
the matched prior-key/index coordinate and target length. K is the same
parse/lookup/learn state machine with prediction disabled. Two fresh processes
must emit byte-identical receipts.

The sealed candidate tree is `3d110ac4...680c5`; strict C++17 syntax validation
and all registered JSON schemas pass. The prospective threshold remains
`4,079,243` correct D bytes, with every chronological third positive and D
strictly above R and S. This number is a frozen hypothesis, not a result. No
scan or decision receipt exists. The runner fails closed unless it receives a
fully positive, independently verified q1 qualification with runtime and
package closure, process-tree peak at most `9,000,000 KiB`, and a released
full-1G lease. See the
[`execution contract`](../operations/planning/wiki_schema_vm_ceiling_q0_v1.json),
[`experiment`](../operations/adaptive/experiments/wiki_schema_vm_ceiling_q0_v1.json),
and
[`interface`](../programs/wiki_schema_vm_ceiling_q0_v1/interface-contract.json).

## 2026-08-23 - cmix-obias Arm B terminalizes as an OOM/resource failure

The source-built full-1G Arm A remains an exact host-bound external baseline.
Its `108,022,224`-byte archive and `107,730,531`-byte payload decode to the
canonical `1,000,000,000` bytes with SHA-256
`159b8535...744bc`. Charging the independently reproduced `491,483`-byte
program package gives a counted total of `108,513,707` bytes. This is an
external-candidate measurement, not Gamma-authored score credit.

Arm B completed encoding and reproduced Arm A's archive and payload
byte-for-byte, but it did not complete inversion. Its decode log stops at
`39.07%` at the same host event where the kernel OOM snapshot contains the
wrapper and `archive9` decoder and the enclosing tmux scope failed with
`oom-kill`. The preserved strict-memory observation records
`VmHWM=10,425,744 KiB`, exceeding the decimal `9,765,625 KiB` limit by
`660,119 KiB`; the independent tmpfs-aware receipt is also a resource failure.
The incomplete scratch tree remains unchanged in `/dev/shm` as evidence.

Recovery-only terminalization archived both stale runtime sidecars before
removing them from the live lease namespace. The independent verification
rehashed every retained archive, payload, log, sidecar snapshot, and OOM log;
all 18 checks pass. The terminal A/B audit consequently records
`correctness_pass=false` and `strict_resource_pass=false`: the pair proves
repeat encode identity on this host, but not a second exact inverse or a
resource-qualified deterministic full-1G package. Arm B receives zero score
and authorship credit and must never be resumed or rerun. Evidence:
[`Arm A`](../results/cmix_obias_source_full1g_roundtrip_a_qm0_v1/decision.json),
[`Arm B terminal receipt`](../results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-receipt.json),
[`independent verification`](../results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-verification.json),
and [`A/B audit`](../results/cmix_obias_source_full1g_ab_terminal_audit_v2/decision.json).

The unique authorized successor is the correction-only file-backed
memory-safe parent. It must first prove output identity and process-tree plus
file-backed residency compliance at the smallest frozen gate. No midpoint,
mixture, or structural mechanism may inherit compression credit from this
resource correction.

## 2026-08-23 - q1 file-backed parent passes reset scopes and cumulative 1M

The q1 correction now has a clean, content-addressed qm7 build lineage. Two
release builds are byte-identical with SHA-256 `610edd6a...5a8808`; two harness
builds are byte-identical with SHA-256 `8fc7b519...b65f`. All 17 compiler
controls and the isolated allocator positive fixture plus all 15 allocator
negative controls pass. The packaged shared allocator event descriptor is not
used as a lifecycle sequence: package creation launches helper CMIX processes
that inherit the descriptor, so its stream contains three concatenated
lifecycles. Lifecycle authority remains the isolated fixture and controls,
while each codec arm must leave its backing directory empty.

The corrected v2 reset-scope receipt passes opening, middle, and tail 250KB
cold-start populations. Parent and q1 have identical post-head integer
probabilities, complete residual and byte traces, payloads, and decoded output
within every scope. The aggregate scoped probability hash is
`cc232442...11afe9`. Opening restores the exact 250,000 raw bytes. The
specialized preprocessor restores 249,871 bytes for the middle fragment and
249,350 for the tail fragment; those two populations therefore require exact
parent/q1 decoded-output identity rather than the invalid claim that an
arbitrary interior fragment is a standalone raw round trip. All 12 guards
pass, with worst sampled tree RSS `8,351,304 KiB`, and q1 backing cleanup is
exact. See the
[`scope receipt`](../results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/06_scope_identity/fixed-reset-scopes/scope-identity-receipt.json).

The cumulative opening-1M successor also passes. Both arms emit the same
`172,605`-byte payload (`a723ca62...d70db7`), the same exact probability stream
(`d34a8d4b...5458d`), and byte-identical complete traces; both restore the
canonical 1,000,000-byte prefix with SHA-256 `369b6889...52cad`. Its four
guards pass at worst sampled tree RSS `8,388,568 KiB`, worst sampled scratch
`20,991,792,710` bytes, and one allowed CPU. See the
[`cumulative receipt`](../results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/07_cumulative_identity_1m/cumulative-identity-receipt.json).

These are exact parent-preservation and resource-feasibility results, not a
compression improvement. q1 remains unqualified for full-stream authority,
Gamma compression credit, or score credit. The next bounded gate is the
frozen opening-prefix and distant cold-reset 10M transfer pair; the latter is
explicitly not a byte-zero persistent-state claim.

## 2026-08-23 - q1 passes 10M transfer, then exposes a cgroup-cache full-1G failure

The opening and distant cold-reset 10M transfer phase passes. Opening q1 emits
the same `1,599,341`-byte payload as its qualified parent and restores the
canonical opening 10M bytes. The distant scope emits the same `459,091`-byte
payload and decoded stream as its parent. Both scopes have exact post-head
integer-probability identity; worst sampled tree RSS is `8,503,092 KiB`, worst
scratch is about `23.5 GB`, every guard passes, and the independent verifier
rehashes both populations and receipts. This remains bounded reset/transfer
evidence and does not establish the byte-zero persistent full-1G trajectory.

Candidate-owned full Arm A `cmix_filebacked_fxcm_full_a_qm7_v2` then failed at
a new phase boundary. The two package-helper compressions completed and the
real transformed-payload compressor reached pretraining `0.39%`, but its
cgroup hit the effective page-rounded hard cap of `9,999,998,976` bytes and
recorded `537` `memory.events.max` events. The guard terminated the tree with
SIGTERM. There was no OOM kill, process-tree RSS itself peaked at only
`7,395,300 KiB`, no encode-stage receipt was written, decode never started,
and all output, inverse, qualification, and score claims correctly remain
false. The scratch tree is preserved. All independent failure-verifier checks
pass; see the
[`terminal receipt`](../results/cmix_filebacked_fxcm_full_a_qm7_v2/full-roundtrip-receipt.json),
[`verification`](../results/cmix_filebacked_fxcm_full_a_qm7_v2/full-failure-verification.json),
and
[`reflection`](../operations/adaptive/reflections/20260823T213424Z_653b446c89.json).

The single correction-only successor is
`cmix_filebacked_fxcm_full_a_qm8_v1`. It leaves the q1 binary, package bytes,
model, coder, preprocessing, corpus, accounting, and 10,000,000,000-byte hard
cap unchanged. A bound wrapper instead sets cgroup `memory.high` to a
page-rounded `8,999,997,440` bytes so Linux initiates cache reclaim before the
hard cap, then restores the prior value. The wrapper preflight passes and is
schema-validated. Adaptive job `20260823T215147Z_7827ad9bc5` is the only
authorized full-1G execution for this correction. It receives zero score
credit unless a later exact package receipt independently closes every prize
gate.

## 2026-08-23 - phase-11 audit preserves post-head evidence and finds a dead residency hook

A harder read-only audit corrected a false concern before it could mutate the
qualification route. The source closure's stock `KH_TRACE` call is pre-head,
but the retained qm7 identity populations did not execute that source
unchanged. Their content-addressed diagnostic build applies
`exact-integer-probability-trace.patch` (`09c87e09...71e`), which moves
`KhWriteRes` after `KhBitLstm32Head::Adjust` and immediately before the
arithmetic range split. The materialized build confirms that placement, and
its receipt explicitly binds the patch and post-head contract. The opening and
distant 10M probability hashes `d6512550...4e97a` and
`4ab13c5d...ec59` therefore remain valid exact coder-probability evidence.

The same audit found a real resource-observer defect. q1 defines
`FXCM::ByteUpdate()` to invoke the 1,048,576-modeled-byte pageout cadence, but
`Predictor::Perceive()` never calls `fxcm_model_.ByteUpdate()`. Source-wide
call-site inspection finds only the method definition. Thus qm8 exercises the
constructor's initial `PageOutAll` plus kernel reclaim under `memory.high`, not
the declared periodic hook. This does not change predictor arithmetic or
invalidate the live run, but its resource receipt must be interpreted under
that actual mechanism. Repairing the hook inside qm8 is forbidden; any repair
would be a new correction-only candidate.

The unbound phase-11 successor is recorded only as a draft at
[`cmix_filebacked_fxcm_full_probability_state_identity_q0_v1`](../operations/planning/cmix_filebacked_fxcm_full_probability_state_identity_q0_v1.json).
It replaces the infeasible full `KH_TRACE` with an online post-head uint16
SHA-256 stream calibrated against both retained 10M digests, coder-state
checkpoints, and source-ordered semantic hashes of every large allocation that
the q1 mutation can affect. It has no execution authority until exact,
independently verified full A/B roundtrips release the full-1G lease.

## 2026-08-16 - The layer-19 output projection is open in both directions

A same-run production probe sealed the tensor immediately after
`concat_head` and before `w_o_19`, its input adjoint, and the initial
`w_o_19` matrix over all 64 states and 32 streams. Both complete source
populations were byte-identical, every non-probe fixture file was unchanged,
and the retained matrix-gradient identity held. The source job completed the
science but named an undeclared pre-cleanup decision artifact; its receipt-only
successor rehashed both 256-file probe populations, published the three durable
BF16 artifacts, and removed the transient capture trees. See the valid
[`decision`](../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T162351Z_97a6519638.json).

The open matrix-gradient attribution first reproduced a prospectively fixed
128-row slice, then expanded the same chronological kernel across all
1,048,576 `w_o_19` weights. Each state accumulates its 32-stream dot from
zero with sequential AVX2 FMAs, adds the decoded prior BF16 gradient after the
dot, and rounds once to BF16. The full treatment is exact; its sign-negated
control differs everywhere. See the full
[`decision`](../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T163533Z_7a29124cd9.json).

The complete transpose then transferred the independently attributed
128-feature panel schedule to `w_o_19`. Eight ordered panels reproduce every
one of the 2,097,152 source input-adjoint words exactly across two replays. A
single unblocked 1,024-feature chain differs in 285 words and the sign-negated
control differs everywhere. The evaluator has no LibNC, GGML, CUDA, OpenMP,
BLAS, or other forbidden dynamic dependency. See the
[`decision`](../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T164348Z_ff5718724e.json).

Finally, the already exact 32-stream open forward exposed its existing
layer-19 merged-attention value without changing arithmetic. Two full
populations retained zero mismatch across all 640 layer-input checkpoints and
equal aggregate hashes. State-major assembly reproduces all 2,097,152 source
pre-`w_o` words exactly; the prospectively frozen stream-major control differs
in 2,088,943 words. The expensive run first failed before science because its
fixture parent was absent. Its retry completed every predicate but used a
decision label outside the result schema. A receipt-only successor freshly
rechecked the source tensor, replay receipts, control, artifact copy, and
original resource envelope, then emitted a contract-valid result. See its
[`decision`](../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/decision.json),
[`execution receipt`](../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/execution.json),
[`guard`](../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json).

This closes the layer-19 output projection's forward value, parameter
gradient, and input adjoint. It remains zero-credit teacher-removal evidence:
the forward binds a pinned static GGML source archive and sealed fixture, and
none of these results proves a compact predictor, recursive adaptation,
compression gain, transfer, package closure, or a Hutter score. The next live
boundary is the eight-head value-attention product and `concat_head` backward.

## 2026-08-16 - The layer-19 pre-FF total adjoint is open and exact

The residual-join investigation found an evidence-lineage error rather than a
new arithmetic rule. A production same-run probe captured the pre-FF input,
total adjoint, RMSNorm branch adjoint, and direct residual adjoint in one graph
over the complete retained population. Both source captures were complete,
byte-identical, fixture-preserving, and within the decimal-memory and scratch
limits. The total and branch reproduced their independently sealed source
artifacts exactly. The direct differed from the older
`final_norm_backward` artifact in eight BF16 words, but reproduced the already
promoted streaming-dot final-RMSNorm residual in every word. Adding the
same-run branch and direct in F32 and rounding once to BF16 reproduced every
source total word; the negated control remained live. See the terminal
[`decision`](../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/decision.json),
[`execution receipt`](../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/execution.json),
[`guard`](../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T155008Z_4831e25438.json).

This supersedes the earlier interpretation of the three-word total mismatch.
Five of the eight corrected direct words did not cross the final BF16 sum
boundary; three did. The generic shared-BF16 merge experiments were therefore
driven by a stale direct input and do not establish special merge behavior.
Raw F32 branch joins, coordinate repair, and special residual accumulation are
not needed. Historical receipts remain unchanged.

The first source job completed both large captures but failed at finalization
because it imported the comparator from the wrong module. Its manifest-only
retry completed every scientific comparison, staged durable artifacts, and
removed the transient capture trees before schema validation rejected an
extra `id` in the result's experiment reference. A receipt-only immutable
successor rebound those staged artifacts and published the valid result. The
two implementation failures and their reflections remain part of the audit
trail; no teacher rerun was used to repair either finalization error.

Finally,
`nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1` replaced only the stale
direct input with the promotion-backed streaming-dot artifact. Two
teacher-free full-population compositions replay byte-for-byte and reproduce
the complete sealed source total with zero error. The small executable has no
LibNC, GGML, BLAS, OpenMP, or CUDA dependency. See its
[`decision`](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T155508Z_53d5388d2c.json).

This closes the open backward boundary through the layer-19 FF block and its
pre-FF normalization/residual join. It remains zero-credit teacher-removal
evidence and proves no attention backward, recursive update, compression
gain, transfer, package, or Hutter result. The next frozen boundary is the
layer-19 attention output projection: the pre-`w_o_19` value tensor, its input
adjoint, the retained `w_o_19` gradient, and the transpose residual.

## 2026-08-16 - The complete top FF1 backward is open through its input adjoint

Three prospectively frozen experiments resolved the remaining `ff1_19`
matrix-gradient boundary. The source attribution first replayed 64
chronological graph states over a fixed 128-output by 1,024-input slice. Its
LibNC treatment matched the retained gradient exactly, while a flat
whole-population product missed 101,753 words and reverse state order missed
110,634. This established that matrix gradients, like bias gradients, retain
BF16 materialization at every graph-state boundary. See the
[`decision`](../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T114029Z_4b8fd50e01.json).

The first open arithmetic grid then refuted its frozen prior-initialized FMA
hypothesis: that cell and the nonfused cell each missed 43 of 131,072 words.
The prospectively declared post-dot cell was exact. Its immutable successor
confirmed the localized contract over the entire slice and two replays:
accumulate each 32-stream dot from zero with sequential AVX2 FMAs, add the
decoded prior BF16 gradient after the dot, then round-to-nearest-even BF16
once per state. It also reproduced the independent reverse-state and
sign-negated oracles exactly while retaining both 43-word failures. See the
grid
[`decision`](../results/nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1/decision.json)
and
[`reflection`](../operations/adaptive/reflections/20260816T115801Z_99a2e7695e.json),
then the immutable successor
[`decision`](../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T120602Z_ec1474d292.json).

Finally,
`nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1` expanded that uniform
kernel to the complete 1,024-input by 6,144-output matrix without changing
arithmetic. Both full 6,291,456-word projections replayed byte-for-byte. Every
one of 48 prospectively fixed 128-row partitions, the inherited parent slice,
and the retained production gradient matched exactly. The generated gradient
also reproduces the retained artifact SHA-256. The executable has no LibNC,
GGML, BLAS, OpenMP, or CUDA dependency and passed the decimal-memory,
temporary-disk, source-closure, and cleanup guards. See the
[`decision`](../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T121133Z_b2c70f9ec5.json).

The next source probe attached a marked zero tensor immediately before the
production `ff1_19` matmul and sealed two complete input and input-adjoint
populations. Its raw science was sound but its first gate retried: the reused
fixture helper excluded only the historical `top_ff2_` namespace and counted
all 256 declared `top_ff1_` probe files in each capture as fixture mutations.
An immutable manifest-only correction did not rerun the teacher. It proved
that all 512 stale mismatches were exactly the enumerated probe paths and that
every non-probe fixture payload remained identical. The corrected oracle
retains two byte-identical 2,097,152-word adjoints, exact source/open FF1 input
identity, and a verbatim 6,291,456-word initial BF16 matrix. See the original
[`decision`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_v1/decision.json)
and
[`reflection`](../operations/adaptive/reflections/20260816T121911Z_d066eaf1cf.json),
then the corrected
[`decision`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/guard.json),
and
[`reflection`](../operations/adaptive/reflections/20260816T123446Z_5cbfc56c6d.json).

Finally, `nncp_open_top_ff1_input_adjoint_block128_64_q0_v1` transferred the
already attributed LibNC matmul-driver schedule from FF2 to the wider FF1
transpose. Forty-eight ordered 128-feature panels reproduced every source
input-adjoint word exactly across two full replays. A one-panel unbroken
6,144-feature reduction differed in 1,256 words, proving that the panel
boundary remains operationally live. The generated open artifact reproduces
the source-oracle digest and the executable has no LibNC, GGML, BLAS, OpenMP,
or CUDA dependency. See the
[`decision`](../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T123635Z_f1f6615808.json).

This retires LibNC for both top-FF1 parameter gradients and the complete FF1
input-adjoint projection. It remains zero-credit teacher-removal evidence: no
compression, transfer, package, or Hutter improvement follows. The next live
top-layer boundary is the layer-19 pre-FF normalization backward, including
`ln_g_39`, `ln_b_39`, its input adjoint, and the direct FF residual branch.

## 2026-08-16 - The top FF1 bias gradient is fully open and exact

The complete top-layer backward chain now has an open exact projection through
`ff_bias1_19`. Candidate
`nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1` combined the promoted
128-feature-panel FF2 transpose with the attributed AVX2 bounded-exp GELU
backward. Both complete populations replayed byte-for-byte. All 6,291,456
FF2-input residual words, all 6,291,456 gate-branch words, and all 6,291,456
value-branch words matched their independent source captures exactly. The
remaining flat bias projection still differed in 4,708 of 6,144 words, with
maximum absolute error `1.52587890625e-05`, localizing the discrepancy after
the elementwise FF1-output adjoint. See the
[`decision`](../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/execution.json),
and
[`guard`](../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/guard.json).

Static `nc_backward` attribution showed that each broadcast-bias parameter
node invokes `nc_reduce_sum(existing_gradient, state_gradient, 1)`. Candidate
`nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1` therefore replayed the 64
chronological `[6144, 32]` state panels instead of flattening all 2,048
samples. The source operation reproduced every retained word exactly; the
flat control retained 4,708 mismatches and the reverse-state control retained
5,099. See its
[`decision`](../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T111831Z_64dcc1173e.json).

The immutable LibNC-free successor
`nncp_open_ff1_bias_state_reduce_64_q0_v1` then implemented the attributed
contract directly: decode the prior BF16 gradient, add streams 0 through 31
sequentially in float32, and round-to-nearest-even BF16 once after each state.
Two complete executions were byte-identical and matched all 6,144 independent
LibNC oracle words with zero error. The flat, reverse-order, and sign-negated
controls remained live; the executable had no LibNC, GGML, BLAS, or OpenMP
dependency. See the
[`decision`](../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/guard.json), and
terminal
[`reflection`](../operations/adaptive/reflections/20260816T112548Z_7841e2cc5b.json).

This retires both flattened bias accumulation and LibNC as an FF1-bias
dependency. It remains zero-credit teacher-removal evidence: no compression,
transfer, package, or Hutter result follows. The next unproven top-layer
parameter boundary is the `ff1_19` matrix gradient. Its gate must preserve the
same chronological graph-state accumulation rather than borrowing a flat
whole-population reducer.

## 2026-08-16 - The exact FF2 transpose uses ordered 128-feature panels

Two prospectively frozen arithmetic attributions resolved the 775-word
source/open FF2-input-adjoint boundary. The first mapped SIMD lanes to
adjacent output features and accumulated each lane through one unbroken
1,024-feature FMA stream. It was valid but worse: 929 of 6,291,456 source
BF16 words differed, with maximum absolute error
`2.9802322387695312e-08`. This retires the unblocked lane stream and shows
that identifying the inner kernel alone is insufficient. See its
[`decision`](../results/nncp_libnc_ff2_transpose_lane_order_64_q0_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T093214Z_c6950a77d0.json).

Static dispatch attribution then exposed the missing driver boundary: the
1,024-feature reduction is executed as eight ordered 128-feature panels. The
second candidate preserved adjacent-feature lanes, reset each lane
accumulator at every panel, and added each completed panel to the prior
output. Two complete executions replay byte-for-byte and reproduce every one
of the 6,291,456 independent source-adjoint words with zero error. The
horizontal and unblocked controls retain their distinct 775-word and
929-word mismatch populations, so the panel boundary is live. Parameter and
LibNC digests, strict outputs, source closure, memory, scratch, and cleanup
guards pass. See the
[`decision`](../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json).

This authorizes one uniform open FF2-transpose implementation: adjacent
output-feature SIMD lanes, ordered 128-feature reduction panels, one panel
combination before the next panel, and one final BF16 conversion. It remains
zero-credit teacher-removal evidence and proves no GEGLU, FF1, recursive
update, compression improvement, transfer, package, or Hutter result.

## 2026-08-16 - The first remaining divergence is the FF2 transpose

Candidate `nncp_libnc_top_ff2_input_adjoint_64_q0_v1` placed a marked zero
probe on the production layer-19 GEGLU output immediately before `ff2_19` and
captured its complete backward adjoint twice. The frozen comparison withheld
the open residual until both source populations were complete and preserved
all non-probe fixture payloads.

The experiment is valid and its byte-identity hypothesis is refuted. Both
source captures replay exactly, expose all 6,291,456 expected BF16 input and
adjoint words, leave the production fixture unchanged, retain a live
comparator, and pass strict output, source, memory, scratch, and cleanup
guards. The source adjoint nevertheless differs from the open streaming
transpose residual in 775 words, with maximum absolute error
`2.9802322387695312e-08`. See the
[`decision`](../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_top_ff2_input_adjoint_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T090818Z_428a8e6c62.json).

This is the first measured divergence after the exact final-RMSNorm adjoint
and exact `ff2_19` parameter gradient. GEGLU backward is downstream of an
already-nonexact residual and is therefore not needed to explain the retained
`ff_bias1_19` mismatch. The current eight-lane streaming transpose is retired
as source-exact, but FF2 transpose itself is not. The next gate must compare
frozen arithmetic variants against the captured source adjoint before GEGLU
is reopened. This source oracle has zero objective credit and proves no
recursive update, compression improvement, transfer, package, or Hutter
result.

## 2026-08-16 - The first open GEGLU backward contract is refuted

Candidate `nncp_open_profile_top_ff1_bias_gradient_64_q0_v1` started from the
promoted exact final-RMSNorm input residual, regenerated both complete forward
populations with fresh layer-19 FF1 outputs, and applied one frozen backward
contract: streaming BF16 FF2-transpose dots, a BF16 transpose-output boundary,
the measured unfused tanh-GELU derivative, and explicit BF16 product
boundaries. The retained `ff_bias1_19` gradient remained unavailable until both
open projections were complete.

The experiment is valid and the hypothesis is refuted. Both populations and
their complete FF2-input and FF1-output residuals replay byte-for-byte, all
forward checkpoints remain exact, the sign-negated control changes, strict
outputs validate, and dependency, source, memory, scratch, and cleanup guards
pass. Nevertheless, 4,708 of 6,144 retained `ff_bias1_19` BF16 words differ,
with maximum absolute error `1.52587890625e-05`. Both the gate and value halves
contain mismatches, so the bias projection alone cannot distinguish the shared
FF2-transpose adjoint from branch-specific GEGLU arithmetic. See the
[`decision`](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_top_ff1_bias_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T084751Z_2949ede196.json).

This retires the combined contract, not FF2 transpose or GELU individually.
The next justified experiment must capture or independently validate the
production FF2-input adjoint before changing activation arithmetic. Tuning
against the retained bias vector is forbidden. This result has zero objective
credit and proves no FF1 matrix gradient, earlier-layer backward, recursive
update, compression improvement, transfer, package, or Hutter result.

## 2026-08-16 - The open tail is exact through the top FF2 gradient

Candidate `nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_v1` installed
only the source-attributed streaming eight-lane FMA reduction at the final
RMSNorm `g*y` dot. Its first job stopped during digest-bound preflight because
the wrapper retargeted an inherited antecedent checker; no scientific payload
was produced. The first immutable retry completed both populations and every
scientific comparison, but strict validation rejected its result because the
cloned output manifest still named the ancestor candidate. Both failures are
retained as implementation evidence in their terminal
[`preflight reflection`](../operations/adaptive/reflections/20260816T080014Z_9da1ba0532.json)
and
[`manifest reflection`](../operations/adaptive/reflections/20260816T080451Z_d5838c6e4e.json).

The manifest-only second retry preserved the C++ algorithm byte-for-byte and
reran the complete guarded population. The prospectively frozen gate passed
every predicate. Two independent 32-stream executions preserve all inherited
forward, output-head, final-normalization parameter, and projection results;
the complete final-RMSNorm input residual matches the independent source
adjoint in all 2,097,152 BF16 words; and all 3,145,728 retained `ff2_19`
gradient words are exact. Replay is deterministic, the residual-negation and
FF2-negation controls remain live, the strict nine-output manifest validates,
and dependency, source, memory, and scratch guards pass. See the
[`decision`](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/execution.json),
[`guard`](../results/nncp_open_profile_top_ff2_gradient_stream_dot_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T082228Z_f0bff9b6df.json).

This opens the production backward tail from the output head through final
RMSNorm and the top-layer FF2 parameter gradient. It remains a zero-credit
teacher-removal result. It proves no FF2 input residual, GEGLU derivative,
`ff1_19` or bias gradient, earlier transformer backward, recursive update,
compression improvement, transfer, package, or Hutter result. The next frozen
boundary is the FF2 transpose residual through GEGLU into the top-layer FF1
and bias gradients.

## 2026-08-16 - The final RMSNorm discrepancy is the product reduction

The four-cell
`nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1` attribution crossed two
product-reduction orders with two algebraically equivalent scalar placements.
Both generic block-combined dot cells reproduced the retained open residual
and differed from the source adjoint in the same 8 BF16 words. Both ordered
eight-lane streaming FMA cells reproduced the independent source adjoint
exactly. Mean-scaled versus width-scaled placement was BF16-identical across
the complete population, so the frozen uniqueness hypothesis was refuted even
though the causal boundary became sharper.

This retires generic 64-element block combination as a source-equivalent
implementation of the final-RMSNorm `g*y` dot and retires scalar placement as
the cause on this population. It authorizes one uniform streaming reduction,
not coordinate patches or tolerance. See the
[`decision`](../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/execution.json),
[`guard`](../results/nncp_libnc_final_rmsnorm_reduction_scale_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T075342Z_b33521b4a0.json).

The attribution uses retained source tensors only as post-completion
comparators and has zero objective credit. No source executable, captured
adjoint, gradient, trace, or probability may enter a submitted codec.

## 2026-08-16 - The production top-layer FF2 adjoint is localized

The first `nncp_libnc_top_ff2_adjoint_64_q0_v1` job stopped before measurement:
its probe definitions were below their first call sites and lacked forward
declarations. The terminal
[`reflection`](../operations/adaptive/reflections/20260816T064522Z_bd9f01360c.json)
classifies that compiler failure as implementation evidence and preserves the
unchanged scientific predicates.

The declaration-only retry attached a zero-valued marked parameter after the
production layer-19 FF2 bias at the first retained update. Two complete source
executions each emitted the same 757-file population and aggregate hash. Every
non-probe file remained byte-identical to the retained production fixture, and
the combined source FF2 inputs, post-FF2 adjoints, reconstructed gradients, and
sign-negated controls replayed byte-for-byte.

The attribution is exact. Source input plus source adjoint under the frozen
128-sample reducer reproduces all 3,145,728 retained `ff2_19` BF16 words with
zero error. The open final-normalization input residual differs from the source
post-FF2 adjoint in 8 of 2,097,152 words across 8 output features, with maximum
absolute error `2.9802322387695312e-08`. This retires FF2 outer-product
reduction order as the cause of the prior 184-word mismatch and moves the next
boundary to an operation-level decomposition of the open final RMSNorm
per-sample adjoint. See the retry
[`decision`](../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_libnc_top_ff2_adjoint_64_q0_retry_v1/guard.json), and
terminal
[`reflection`](../operations/adaptive/reflections/20260816T065037Z_1d8853ab41.json).

This source capture is a zero-credit attribution oracle. No teacher
executable, LibNC dependency, captured tensor, gradient, trace, or probability
may ship in a submitted codec, and no compression, transfer, package, or
Hutter result follows.

## 2026-08-16 - The first top-layer FF2 reduction is narrowly refuted

Candidate `nncp_open_profile_top_ff2_gradient_64_q0_v1` retained the complete
exact output-head and final-normalization tails, exposed fresh BF16 layer-19
GEGLU outputs, and applied the promoted 128-sample output-head matrix-gradient
reduction directly to the complete `ff2_19` outer product. Both 32-stream
executions were byte-identical, every inherited comparator remained exact,
both negative controls changed, and dependency, source, memory, scratch, and
finalization guards passed.

The FF2 claim itself failed exactly: 184 of 3,145,728 retained BF16 words
differed, with maximum absolute error `9.5367431640625e-07`. This valid result
localizes the remaining discrepancy to operation-specific FF2 product or
reduction semantics. It retires direct reuse of the output-head reduction
without an FF2-specific arithmetic boundary; it does not weaken exact parity
or authorize tolerance. See the
[`decision`](../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_top_ff2_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T055603Z_52a69ff065.json).

The first immutable retry tested a uniform BF16 boundary after the final
RMSNorm incoming-gradient times gain product. It was a valid numerical no-op:
the digest-bound initial `ln_g_40` tensor is BF16 `1.0` in every coordinate,
and the retry reproduced both the normalization-input residual and `ff2_19`
gradient artifact hashes byte-for-byte, including the same mismatch set. This
retires that boundary at the selected update. See its
[`decision`](../results/nncp_open_profile_top_ff2_gradient_64_q0_retry_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T061837Z_1dfa2ae8f8.json).

This experiment has zero Hutter objective credit. The next justified gate is
a zero-credit source capture of the actual production post-FF2 residual-join
adjoint. It must compare that complete per-sample tensor with the open
normalization-input residual before another arithmetic retry is authorized.

## 2026-08-16 - The complete final RMSNorm backward tail is open and exact

The first `nncp_open_profile_final_norm_backward_64_q0_v1` execution generated
both full open populations but failed during result finalization because its
runner removed the work tree before reading cached element counts. Its
terminal
[`reflection`](../operations/adaptive/reflections/20260816T045714Z_6eb299ed8d.json)
classifies that attempt as an implementation failure rather than scientific
evidence.

The first immutable retry fixed finalization, applied the already measured
concat-root centered RMSNorm input rule, and changed `ln_g_40` to the promoted
chunked reduction. Its valid result isolated two different outcomes. The
centered input residual reproduced every retained top-layer `ff_bias2_19`
projection word exactly, but the gain gradient retained the same mismatches as
the unchunked attempt. This retired reduction reassociation as the gain cause.
See its
[`decision`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T051419Z_4df92ec3b4.json).

Candidate `nncp_open_profile_final_norm_backward_64_q0_retry_v2` changed one
remaining boundary: every per-sample normalized-state times incoming-gradient
product is rounded to BF16 before the unchanged reduction. The prospectively
frozen gate then passed every predicate. Both full executions reproduce all
retained output-head gradients, the promoted final-hidden residual, all
`ln_g_40` and `ln_b_40` words, and all `ff_bias2_19` projection words exactly.
The complete centered normalization-input residual replays byte-for-byte, both
negative controls remain live, the open executables have no forbidden dynamic
dependency, and source and resource guards pass. See the
[`decision`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/decision.json),
[`execution receipt`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/execution.json),
[`guard`](../results/nncp_open_profile_final_norm_backward_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T053159Z_b79233ecb1.json).

This opens the complete production final-normalization affine and centered
input-backward tail. It proves no FF2 activation residual, GEGLU backward,
earlier normalization, attention, recursive training, transfer, archive
score, package eligibility, or full-corpus reconstruction and has zero Hutter
objective credit. The next frozen boundary is the complete top-layer
`ff2_19` parameter gradient from the exact normalization-input residual and a
fresh open GEGLU output.

## 2026-08-16 - The complete output-head activation residual is open

Candidate `nncp_open_profile_final_hidden_residual_64_q0_v1` advances the
exact open BF16 loss residual through the digest-bound initial `embed_out`
transpose. The standalone reducer consumes only decoder-visible targets,
freshly generated probabilities and final hidden states, and initial
parameters. It generates both complete activation-residual payloads before
hash-verifying or reading any retained gradient comparator.

The prospectively frozen gate passed every predicate. Two independent
32-stream executions emitted byte-identical 2,097,152-word BF16 final-hidden
residuals. Their broadcast reductions reproduce all 1,024 retained `ln_b_40`
gradient words exactly, while both previously promoted output-head parameter
gradients remain exact and the cyclic target-shift control changes. The open
executables have no forbidden dynamic dependency, the dependency-closed
incremental source remains within its frozen ceiling, and the guarded work
tree was removed. See the
[`decision`](../results/nncp_open_profile_final_hidden_residual_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_final_hidden_residual_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_final_hidden_residual_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T043203Z_ca54b4761d.json).

This independently validates the complete output-head activation residual by
an exact retained final-normalization bias projection. It does not provide a
direct retained comparator for every per-sample residual word and proves no
final-normalization gain or input gradient, transformer-layer backward,
recursive training, transfer, archive score, package eligibility, or
full-corpus reconstruction. It has zero Hutter objective credit. The next
frozen boundary reconstructs `ln_g_40` and the final-normalization input
residual separately, using the retained top-layer `ff_bias2_19` gradient as an
independent projection before entering the transformer block.

## 2026-08-16 - The complete output-head parameter gradient is open and exact

Candidate `nncp_open_profile_output_matrix_gradient_64_q0_v1` advances the
promoted BF16 loss residual through the complete open final hidden state. The
standalone reducer consumes only digest-bound initial parameters and state,
decoder-visible targets, and freshly generated probabilities and hidden
states. Both retained gradient comparators are hash-verified only after two
complete open payloads exist.

The prospectively frozen gate passed every predicate. Two independently built
32-stream executions match all 640 layer-input checkpoints, all 16,392
`out_bias` gradient words, and all 16,785,408 `embed_out` gradient words
exactly. Both gradients and the forward trees replay byte-for-byte, while a
cyclic target remap changes an independently reduced matrix slice. The open
executables have no forbidden dynamic dependency, the counted incremental
source remains below its frozen ceiling, and the guarded work tree is removed.
See the
[`decision`](../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/execution.json),
[`guard`](../results/nncp_open_profile_output_matrix_gradient_64_q0_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T040455Z_f7722f8e27.json).

This removes the complete output-head parameter-gradient tail from the closed
teacher. It does not yet prove the residual propagated into the final hidden
state, normalization backward, any transformer layer, recursive training,
transfer, archive size, package eligibility, or full-corpus reconstruction. It
has zero Hutter objective credit. The next frozen boundary is the
`embed_out`-transpose activation residual, independently checked through the
retained final-normalization bias gradient before any deeper-backward claim.

## 2026-08-15 - The production loss-to-output-bias backward tail is exact

The first all-stream open backward attempt completed both forward populations
but failed before evidence finalization because its source packer treated a
candidate-owned materializer as a project tool. It also exposed a control-design
error: permuting target states preserves the target histogram and therefore
cannot change a bias-only gradient. The failed job and terminal
[`reflection`](../operations/adaptive/reflections/20260816T031213Z_57a9477621.json)
retain those defects as implementation evidence; its scientific hypothesis was
not tested.

Diagnosis from the independently generated outputs localized the remaining
arithmetic boundary. The production graph converts each per-sample F32 softmax
residual to BF16 before reducing the broadcast output bias. An F32-only
reduction was close but not identical. Candidate
`nncp_open_profile_output_bias_gradient_64_q0_retry_v1` preserves the complete
forward and loss population, applies that BF16 boundary explicitly, packages
candidate source without broadening the tool closure, and replaces the dead
state permutation with a cyclic vocabulary-successor target remap.

The guarded retry passed every frozen predicate. Two independently rebuilt
32-stream populations match all 640 retained layer-input checkpoints and all
16,392 BF16 output-bias gradient words exactly, with zero maximum error,
byte-identical replay, a live negative control, no forbidden dynamic
dependency, and a dependency-closed source package below its frozen ceiling.
See the
[`decision`](../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/decision.json),
[`execution receipt`](../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/execution.json),
[`guard`](../results/nncp_open_profile_output_bias_gradient_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T033450Z_727c49438a.json).

This proves only the production negative-log-likelihood tail through
`out_bias`. It has zero objective credit and proves no output-matrix,
normalization, transformer-layer, embedding, recursive-training, archive,
transfer, package, or full-corpus result. The next teacher-removal boundary is
the output-matrix gradient and hidden-state residual generated from this exact
open BF16 logit residual.

## 2026-08-15 - One causal open production segment transition is exact

The post-update boundary is no longer an incumbent-state-only forward probe.
The retained post-update fixture first exposed a small arithmetic mismatch:
the complete open forward matched all tensors, while a scalar left-fold tree
reduction changed a subset of integer branch counts. Focused candidate
`nncp_open_branch_reduction_postupdate_64_q0_retry_v2` proved that the
previously promoted LibNC-order reducer eliminates the difference. Candidate
`nncp_ggml_postupdate_forward_parity_64_q1_retry_v2` then replayed the complete
retained next segment twice with exact tensor, topology, truth-path, and branch
parity. See its
[`decision`](../results/nncp_ggml_postupdate_forward_parity_64_q1_retry_v2/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T021607Z_81c2c9ae94.json).

The first joint integration attempt was deliberately retained as an
implementation failure. Its canonical Adam reports and all recurrent-memory
layers were exact, but a separately duplicated output loop emitted `203`
parameter payloads differently. The resulting next-forward error was therefore
not evidence against the open update. Its
[`decision`](../results/nncp_open_profile_update_forward_chain_64_q0_v1/decision.json)
and
[`reflection`](../operations/adaptive/reflections/20260816T023511Z_83fa6c7a64.json)
record the non-equivalent treatment and authorize only an emitter retry.

Candidate `nncp_open_profile_update_forward_chain_64_q0_retry_v1` removes that
duplicate arithmetic. A reproducible source patch writes each predicted word
from the canonical exact Adam replay function immediately before its existing
comparison. Two fresh chains independently generate all `246` parameter
payloads, both complete pre-update forwards, all `20` target-stream recurrent
memory layers, and both complete next-segment forwards. The incumbent
post-update parameter and state containers are removed before the chained
forward. All `244` next-forward tensor groups and `896` arithmetic branches are
exact in both repetitions, with byte-deterministic outputs and no forbidden
dynamic dependency. The guarded run stayed below the frozen decimal-memory and
scratch limits. See the
[`decision`](../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/decision.json),
[`chain receipt`](../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/chain-receipt.json),
[`guard`](../results/nncp_open_profile_update_forward_chain_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T024338Z_3839f396a6.json).

This is one causal open production segment transition, not recursive training.
Its dense gradients remain captured teacher outputs. It has zero objective
credit and proves no open backward pass, archive gain, transfer, package
economics, or full-corpus result. The next honest teacher-removal boundary is
an open backward pass that reproduces the same named dense gradients and then
feeds this unchanged update-to-forward chain. The best source-bound forecast
and target debt are unchanged.

## 2026-08-15 - Complete open production optimizer replay is exact

The segment-transition program now has a complete, retained production update
oracle. The Q0 through Q2 fixture attempts were terminal implementation
evidence: stale external digests, callback identity, and incomplete gradient
naming prevented a scientific conclusion. Candidate
`nncp_libnc_profile_update_fixture_64_q3_v1` corrected the shared callback
boundary by using the callback's opaque `NCParam` pointer as the parameter-name
key. Two fresh teacher executions then emitted byte-identical complete
fixtures. The retained local fixture contains all `246` dense gradients,
initial and final parameter/optimizer containers, initial and final recurrent
state, and the train-step `4` to `5` boundary. See its
[`decision`](../results/nncp_libnc_profile_update_fixture_64_q3_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T235124Z_86c7e4f805.json).

The first two official open-replay jobs stopped before arithmetic. Their
separate reflections preserve two general orchestration defects: a consumer
decoded the structured reflection decision as a scalar, then rejected the
empty scratch root that `enqueue-tool` had correctly pre-created. Measured
source and experiment bindings were not edited in place. Each repair received
a new candidate and prospective experiment, leaving both failed jobs
auditable.

Candidate `nncp_open_profile_adam_replay_64_q0_retry_v2` passed the resulting
gate. Its standalone Gamma-authored C++ implementation parses the retained
containers and reproduces the complete production update without calling
LibNC. It implements the exact 64-value reduction, per-tensor norm clipping,
step-five Adam correction, deterministic fast reciprocal square root, fused
update order, BF16 round-to-nearest-even, and biased low-word serialization.
Across `313,000,456` parameter words, `245` BF16 tensors, one F32 tensor, and
all variance tensors, both fresh reports are byte-identical and every mismatch
counter is zero. The dependency-closed source package is retained with the
[`decision`](../results/nncp_open_profile_adam_replay_64_q0_retry_v2/decision.json),
[`guard`](../results/nncp_open_profile_adam_replay_64_q0_retry_v2/guard.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260816T003855Z_aab09244b0.json).

This closes the optimizer and serialization oracle, not recursive training.
The dense gradients are still captured teacher outputs, the result has zero
objective credit, and no open backward pass, second-segment forward, archive
gain, transfer result, or full-corpus package exists. The next admissible gate
is a separately frozen post-update forward fixture and open
update-to-next-forward replay. Only after that passes may work claim one
causally continuous segment transition; open gradient generation remains the
larger teacher-removal blocker.

## 2026-08-15 - Open production arithmetic identity is exact

The retained Q18 GGML forward already matched every exported output tensor,
but its scalar left-fold tree reduction differed from LibNC by one integer
frequency count on a small subset of visited branches. Candidate
`nncp_ggml_profile_arithmetic_64_q0_v1` terminated both paths through the same
fixed Gamma range coder and independent decoder. Both payloads reconstructed
the exact frozen transformed symbols and had equal length, but their bytes
differed. The terminal
[`reflection`](../operations/adaptive/reflections/20260815T225004Z_10e9a0f5af.json)
therefore retires one-count branch tolerance as sufficient codec-boundary
evidence. It does not reject the open GGML forward or the Gamma coder.

Candidate `nncp_ggml_profile_arithmetic_64_q1_v1` changed only that final
reduction. Its counted source reconstructs LibNC's 64-value AVX reduction,
masked-tail semantics, and binary partial accumulation; model parameters,
forward tensors, softmax, quantizer, coder, fixture, and population remained
frozen. The prospective
[`experiment`](../operations/adaptive/experiments/nncp_ggml_profile_arithmetic_64_q1_v1.json)
required zero frequency drift rather than preserving Q18's tolerance.

The guarded run passed. Every visited integer branch frequency is exact, both
open tree paths repeat byte-for-byte, oracle/open/repeated-open payloads are
identical, and all three payloads independently decode the exact symbols. See
the [`decision`](../results/nncp_ggml_profile_arithmetic_64_q1_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T230010Z_836682be9c.json).
This is a real open-runtime correctness gain with zero objective credit: it
proves one production-profile segment, not online parameter updates,
multi-segment continuity, package economics, transfer, or archive improvement.

The next admissible integration had to preserve this exact arithmetic boundary
while exposing the segment transition explicitly. Candidate
`nncp_ggml_profile_memory_transition_64_q0_v1` compiled LibNC's visible
`mem_update` rule into a counted shift-and-append transform. For every layer it
independently combined the retained initial teacher memory with either the
ordered teacher layer inputs or one of two open executions. All layer states
match byte-for-byte and all three aggregate state digests are identical. See
the [`decision`](../results/nncp_ggml_profile_memory_transition_64_q0_v1/decision.json),
[`state receipt`](../results/nncp_ggml_profile_memory_transition_64_q0_v1/state-digests.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T231108Z_4912fe7f1f.json).

This removes memory movement as the blocker, but it does not authorize a
fixed-parameter second segment. The incumbent also computes full deep
gradients, clipping, optimizer moments, and updated parameters after each
production segment. The next honest boundary is therefore a prospectively
frozen full-update receipt, followed only after a pass by a later-segment
oracle. Generic prefix compressor jobs for these infrastructure descriptors
remain held because they would compare different work.

## 2026-08-15 - Direct-F32 named-gradient oracle retires the localization lineage

The q0 named-gradient implementation reached the first production F backward
pass and reproducibly aborted at `libnc.c:7564`: `nc_free_tensor` observed an
already-consumed tensor reference. The defect is localized: LibNC's
`nc_tensor_isfinite` consumes its input, while q0 passed the callback-owned
gradient without first duplicating the reference. The
[`reproduction guard`](../results/delta_midas_named_midpoint_gradient_65536_q0_v1/abort-reproduction.guard.json)
records the same `SIGABRT` under the declared memory and scratch bounds.

Candidate `delta_midas_named_midpoint_gradient_65536_q1_v1` is an immutable
implementation retry. Its
[`experiment contract`](../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q1_v1.json)
changes only reference ownership by calling `nc_tensor_isfinite` on a duplicate
and makes subprocess failure streams durable. Population, F-arm behavior,
grouping, thresholds, repeats, promotion, kill conditions, and zero-credit
boundary are unchanged. Q0 remains terminal implementation evidence; q1 must
still prove both exact archives and complete deterministic rows before any
gradient localization conclusion is allowed.

Q1 then preserved the native stream and exposed the next exact defect:
`nc_get_scalar_f32` rejected the non-F32 squared-energy reduction. Its
[`reflection`](../operations/adaptive/reflections/20260815T172412Z_47ccd874f6.json)
again leaves the scientific hypothesis untested. Candidate
`delta_midas_named_midpoint_gradient_65536_q2_v1` is frozen from q1 with the
new implementation-retry composer: every scientific field and predicate is
inherited, while the runner, materializer, parent revision, negative control,
failure evidence, outputs, and declared implementation delta are rebound. Q2
converts only the completed BF16 squared-energy reduction to `NC_TYPE_F32`
before the scalar read. That restores the scalar-reader type contract but does
not make the accumulated energy authoritative: a direct F32 reducer must
re-evaluate the unchanged localization predicates before any group ablation can
be authorized. Agreement with q2 is a sensitivity diagnostic, not a promotion
condition, because q2's low-precision ranking is not scientific ground truth.

Q2 subsequently completed both encodes with byte-identical retained F archives
and identical complete named-gradient rows. Its schema and semantic receipt
validation pass, including the 64-state block coordinates, parameter coverage,
artifact hashes, and predicate derivation. The low-precision summary selects
feed-forward overall but not in every chronological third, falls below the
frozen minimum-third share, and remains output-head dominated. Those values are
retained as sensitivity evidence only. The terminal
[`reflection`](../operations/adaptive/reflections/20260815T172824Z_465e6837f4.json)
classifies the ranking as incomplete evidence, authorizes `retry`, and retires
only post-reduction F32 conversion as an authoritative localization oracle.

Candidate `delta_midas_named_midpoint_gradient_65536_q3_v1` was frozen from
that reflection. Its
[`experiment contract`](../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q3_v1.json)
binds the direct reducer, explicit F32 reference, complete runtime source and
JSON-contract closure, q2 decision/detail/reflection, retained F comparator,
exact midpoint patch, and strict output set before execution. Direct-reference
finiteness and relative agreement are prerequisites for both promotion and
retirement. Q2 comparisons are diagnostic only. Q3 remains closed-teacher,
zero-credit attribution; it cannot claim codec savings or objective progress.

Job `20260815T200718Z_9b504935f5` completed both encodes under the declared
process-tree memory and scratch guard. The two archives are byte-identical to
each other and to retained F, the two complete named-gradient tables repeat
exactly, and every direct-F32 energy equals its independent explicit-F32
reference. The valid result remains output-head dominated. Feed-forward is the
largest non-head group overall but the dominant non-head group changes across
chronological thirds, and the minimum-third share misses its prospectively
frozen threshold. See the [`decision`](../results/delta_midas_named_midpoint_gradient_65536_q3_v1/decision.json),
[`gradient detail`](../results/delta_midas_named_midpoint_gradient_65536_q3_v1/gradient-detail.json),
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T200718Z_9b504935f5.json).

The exact hypothesis is refuted: squared-gradient energy does not select one
stable deep midpoint parameter group on the frozen production F population.
No group ablation is authorized, and this entire localization lineage is
retired with zero objective credit. The result does not refute a multi-group,
signed-logit, Hessian, activation-residual, or decoder-visible causal
mechanism. The next experiment must be materially different and prospectively
bound; it may not inherit teacher energy, archive savings, or score credit.

## 2026-08-15 - Named production midpoint-gradient localization is prospectively frozen

Candidate `delta_midas_named_midpoint_gradient_65536_q0_v1` is the next
bounded teacher attribution after the positive deep F-versus-O residual and
the negative compact hashed-linear probe. Its structured
[`experiment contract`](../operations/adaptive/experiments/delta_midas_named_midpoint_gradient_65536_q0_v1.json)
binds the exact `65,536`-symbol production population, the legacy attribution
receipt that names retained F, closed-source inputs, immutable parent revision,
analyzer, materializer, two repeat encodes, and zero-credit boundary. That
legacy receipt carries the retained archive digest, but q0 through q2 do not
bind the archive itself as a separate prospective input; their archive-identity
measurement is therefore useful execution evidence, not a tamper-evident
comparator boundary.

The only changed mechanism is observation: during each F-arm first-half
midpoint backward pass, the instrumented teacher emits the stable `NCParam`
name, gradient shape, hash, finiteness, and squared gradient energy. The
instrumented archive must remain byte-identical to retained F, both encodes and
complete named-gradient rows must repeat exactly, and every block must expose
the same parameter set. A successor is authorized only if one non-head group
is dominant in every chronological third, its minimum share of non-head energy
is at least `0.35`, and the output-head share of total energy is at most `0.5`.

Passing selects exactly one separately preregistered group-ablation arm.
Failing the localization thresholds with all integrity predicates intact
retires gradient-energy localization. Gradient magnitude is not probability
attribution, the closed LibNC teacher remains unshippable, and this run cannot
claim archive savings, an open correction, transfer, package economics, or
objective bytes.

The first queued execution, job `20260815T170528Z_778414d866`, stopped before
the teacher began because the guard required its declared result scratch
directory to pre-exist. The terminal
[`reflection`](../operations/adaptive/reflections/20260815T170528Z_778414d866.json)
classifies this as an infrastructure failure and leaves the hypothesis
untested. The general executor boundary now records candidate-owned scratch
directories in the job, constrains them below `results/<candidate_id>/`, and
materializes them before guard preflight. Retry job
`20260815T171447Z_33eeb89e5c` retains the same experiment, candidate revision,
proposal, and runner bindings while adding that explicit lifecycle input.
That retry confirmed the lifecycle fix and entered the first instrumented F
encode, then NNCP terminated with `SIGABRT` before archive completion. Peak
sampled process-tree RSS remained below the declared guard; the terminal
[`implementation reflection`](../operations/adaptive/reflections/20260815T171447Z_33eeb89e5c.json)
keeps the hypothesis untested. Because the analyzer discarded captured native
stderr when `check=True` raised, the next action is an exact stream-preserving
reproduction, not a localization conclusion or parameter sweep.

## 2026-08-15 - Fixed decoder-visible DELTA-MIDAS probe is terminal negative

The first prospective successor to the deep-residual receipt is terminal
`REJECT`. Candidate `delta_midas_decoder_feature_probe_65536_q0_v1` froze one
`4,096`-weight hashed-linear model, four normalized online passes, chronological
train/validation/test partitions, int16 replay, an `8,200`-byte payload ceiling,
and a one-segment shifted-label control before execution.

The experiment was causally valid but lost `887.0184641356755` ideal bits on
validation and `1,080.7027626223207` on sealed test. Every test third was
negative, only `13` of `171` test segments improved, and the aligned treatment
was `696.9629361023035` bits worse than the shifted-label control. See the
[`decision`](../results/delta_midas_decoder_feature_probe_65536_q0_v1/decision.json)
and terminal
[`reflection`](../operations/adaptive/reflections/20260815T162913Z_047c55d5ea.json).

This retires the exact feature map, optimizer, clipping, partition,
quantization, and O-offset replay contract without sweeps. It does not refute
the measured deep teacher residual. Any recurrent or low-rank successor must be
a materially new, prospectively bound mechanism; it cannot be a parameter retry
or inherit archive bytes, transfer, package economics, or score credit.

A source-bound design audit confirms that LibNC exposes stable `NCParam` names
at the midpoint backward callback (`embed`, output head, attention, feed-forward,
normalization, and per-layer parameters). The next justified teacher action is
the now-frozen F-arm midpoint-only named gradient projection above, summarized
by group and chronological third. Its only possible consequence is selection
of one later group-ablation arm; gradient magnitude is not itself probability
attribution. It remains zero-credit teacher work.

## 2026-08-15 - DELTA-MIDAS deep residual survives exact retained-trace gate

Terminal candidate
`nncp_libnc_output_head_midpoint_attribution_65536_qm1_v1` closes the
output-head theory. On its same-run population, rebuild-only `K` is `148,141` bytes, full midpoint `F` is
`143,414`, and output-head-only `O` is `148,709`. Thus F beats K by `4,727`
bytes while O is `568` bytes worse than K. The earlier bridge reports `4,726`
because its parent archive is one byte smaller; those values come from
different exact runs and are not combined. The terminal decision remains a
four-thread closed-LibNC teacher result with zero score credit.

Proposals `nncp_gram_midas_full_hidden_65536_qm0_v1` and
`gamma_orbit192_gram_midas_65536_qm0_v1` are retired because both depended on
an output-head gain that does not exist. Their rejection receipts preserve the
closed neighborhood; the ORBIT feature idea is not inherited into a new result.

Experiment `delta_midas_deep_residual_65536_q0_v1` retrospectively froze an
exact F-versus-O retained-trace analysis before its analyzer emitted a result.
All `65,536` rows and `917,527` truth-path branches aligned. On second halves,
F beats O by `22,783.981772296793` ideal bits. All original-coordinate thirds
are positive, and `1,001` of `1,024` segments are positive. See
[`decision.json`](../results/delta_midas_deep_residual_65536_q0_v1/decision.json)
and the hash-linked
[`reflection`](../operations/adaptive/reflections/20260815T161658Z_636aa4dd6c.json).

The result localizes useful information beyond the output head and authorizes
only one prospectively frozen decoder-visible feature-capture experiment. It
does not show realizable archive savings, a compact student, transfer, package
cost, or Hutter score credit. Hidden state, teacher probabilities, and the
closed LibNC executable remain forbidden submission inputs.

The running q2 named-gradient retry has a separate numeric-validity boundary.
The production profile defaults parameters to BF16, and q1's retained native
[`nc_get1_f32` assertion](../results/delta_midas_named_midpoint_gradient_65536_q1_v1/F_named_gradient_1.stderr)
proves the squared-energy reduction did not produce an F32 tensor. The
[`q2 materializer`](../tools/materialize_nncp_named_midpoint_gradient_q2.py)
converts only after the BF16 elementwise square and reduction, so it repairs
the scalar-reader crash but does not establish precision-stable group shares.
The hash-bound LibNC binary exports `nc_reduce_sum_sqr`; its implementation
creates an F32 scalar and dispatches BF16 inputs through the direct
`vec_sum_sqr_bf16` F32 accumulation path. Therefore q2 may retain archive,
gradient-hash, coverage, and implementation-liveness evidence, but its energy
ranking cannot by itself authorize a group ablation. The smallest valid
measurement retry replaces only the energy expression with
`nc_reduce_sum_sqr(nc_dup_tensor(gradient))`, repeats both exact F encodes, and
cross-checks every value against an explicit BF16-to-F32 multiply-and-sum path.
Both paths must be finite and pass the frozen relative-error bound before the
original group and chronological-third predicates can authorize or retire an
ablation. Agreement with q2 remains diagnostic because q2's BF16 ranking is not
an oracle. Q3 also binds retained `F_clean.nncp` directly and checks its path,
byte count, and digest against the legacy attribution receipt before starting
the teacher, closing the comparator-identity gap instead of inheriting it.

## 2026-08-15 - Recursive self-improvement boundary audited

The adaptive lane now binds the objective, immutable candidate revisions,
structured experiments, terminal reflections, evidence-aware selection,
dependency packaging, and clean-room receipt composition. The executor uses
three fresh builds, two archive-identity runs, and a corpus-blind decode under
sealed one-core resource guards. It is still not authorized for unattended
mutation or prize-facing promotion because no eligible Gamma candidate has
produced a complete full-1G package receipt or second-host identity receipt.
See [`recursive_self_improvement_system_audit.md`](recursive_self_improvement_system_audit.md).
Missing roundtrip, determinism, process-tree resource, dependency-closure, or
peer evidence still fails closed.

## 2026-08-09 - Agent A/B strategy and ownership merge under the 105M target

Agent B has accepted Agent A's handoff and now owns both active scientific
tracks. The canonical objective is an exact, self-contained full-1G score no
larger than `105,000,000` bytes. `cmix-obias` is David Freelan's externally
authored submission candidate, derived from Ibrahim Marcouch's `cmix-lex` and
earlier cmix/PAQ work; Gamma did not invent it and cannot treat reproduction as
a Gamma prize entry. Its reported `108,492,825` score leaves `3,492,825` bytes
of counted debt to the project target. The active full-corpus jobs are
zero-credit external-baseline, provenance, determinism, and resource evidence
only. They may support an independently novel, fully attributed Gamma child,
but they cannot satisfy the objective by themselves. KAIROS was the first
same-stream Gamma correction test, but its completed paid opening replay
retired the frozen dyadic final-head realization; it is no longer a promotion
path.

The independent NNCP lane has now confirmed that the changed update cadence
persists over `1,998,848` symbols, saving `82,432` actual encode-only archive
bytes. That teacher result authorizes the predeclared production-alphabet
state-refresh/output-head/full-update attribution and, only if attribution
passes, a compact MIDAS-style descendant.

The external cmix-obias baseline and NNCP teacher lanes do not inherit or add
projected savings. Only a separately attributable Gamma mechanism may enter
the winning path, and any use of upstream code requires complete attribution
and compliance with its authorship and licensing boundary. A future
combination is authorized only after the new mechanism independently passes
its paid gate, and then only through a new exact joint coder replay with
complete package and memory accounting. The XML-safe far-history/copy family
and the measured KAIROS dyadic realization remain terminally closed.

## 2026-08-09 - Local cmix-obias archive and source snapshot are hash-bound

The previously external-only cmix-obias evidence is now present locally under
`/home/x/enwiki9-nonproof/cmix-obias-donor`. The tracked outer repository is
clean at commit `51488a0c1228dbeab7c1be837fc90ceaed351728`; its tracked
`cmix-obias` subtree has Git tree
`23de249ff899db5ba84dd3514a6a1bb52a83d0f5`. Untracked entries are confined to
the locally provisioned Clang, LLD, compatibility-library, and UPX tools.

The local `final/archive9` is exactly `108,009,834` bytes with SHA-256
`664823c5d9f167bda342745d7b34a3ccb98fd7108723ba83643d9d09bf693900`,
matching the public submission claim. The local packaged compressor is
`459,989` bytes with SHA-256
`eee69c879f4bbd58015efd4d34f55c6dc986ec818fa68c2f32a9ee5ab5568f68`;
the required head blob is `23,002` bytes with SHA-256
`35cd24fed87c3409994abf5573b5697be19ea03b5ece0928b69b1cdc4f3b6078`.
Their arithmetic total is the claimed `108,492,825` bytes.

This advances artifact availability and provenance only. No completed local
full decode, repeat encode, strict-memory qualification, runtime qualification,
or Gamma score credit exists. The root filesystem has only about `15 GB` free,
but the later RAM-backed qualification entry records the safe `/dev/shm`
workspace used by the active decode. No unrelated workspace data was removed
to manufacture capacity.

This register tracks strategy and algorithm research separately from measured
candidate proof. It is a map from idea to local implementation, not a scoreboard.

Claim rule:

```text
Research status is not compression proof.
Promotion requires exact receipts: result JSON, shadow-coder receipt, or guard
receipt depending on the lane.
```

Current proof boundary: the active target is `105,000,000` counted bytes
(`10.5000000%`). The best source-bound forecast is
`endpoint428_gate_dot_fuse_output_update_loop_v1` at `109,389,323` bytes, a
signed target distance of `+4,389,323` bytes before any successor's additional
program, model, table, metadata, or framing cost. The verified exact full-1G
score remains unknown. The current official one-percent prize ceiling is
`109,685,196`; it is an eligibility boundary, while `105,000,000` remains the
research stopping condition. Older `108M`, `109.5M`, `10.95%`, `109,498,879`,
and `109,452,151` targets or forecasts are historical evidence only and do not
control new promotion decisions.

The mature negative record closes fixed mixer blends, width/cell adjustments,
simple residual calibration, explicit phrase-copy commands, and metadata-heavy
semantic partitions as primary routes. Current work therefore requires a new
decoder-visible information source or reversible representation with
million-byte leverage, plus an open self-contained CPU realization. NNCP
midpoint receipts remain causal teacher evidence but are not prize-facing
while they depend on closed LibNC and an ineligible runtime. Native promotion
still requires exact same-object replay, complete package accounting,
determinism, raw reconstruction, decimal-memory compliance, and eventually an
official full-1G receipt at or below the active target.


## Archived entries

Older entries are stored by complete H2 record in [research_register/archive/](research_register/archive/README.md).

- [part-001.md: Novelty Portfolio Contract through 2026-07-26 VULCAN V0 event-control result](research_register/archive/part-001.md)
- [part-002.md: 2026-07-26 D02 TWINSTREAM opening-1M terminal decision through 2026-07-26: official NNCP v3.3 CPU eligibility control](research_register/archive/part-002.md)
- [part-003.md: 2026-07-26: delayed raw, heading, AUTOPSY-rule, and compact-neural closure through 2026-07-27: PCMF-1 paid context-two multinomials are terminal negative](research_register/archive/part-003.md)
- [part-004.md: 2026-07-27: CBM-1 label-free causal block mixture theorem through 2026-07-28 - CHIRON frozen causal residual Q0 - REJECTED](research_register/archive/part-004.md)
- [part-005.md: 2026-07-28 - ROCm batched causal teacher - REJECTED through 2026-08-01: MOBIUS-2 NOEMA binary-carry hierarchy is terminal negative](research_register/archive/part-005.md)
- [part-006.md: 2026-08-01: Typed Event Sleeping Bayes Envelope and parent recovery through 2026-08-02: MÖBIUS-2 frontier-teacher WRT event alphabet QH0 frozen](research_register/archive/part-006.md)
- [part-007.md: 2026-08-02: MÖBIUS-2 frontier-teacher WRT event alphabet is terminal negative through 2026-08-02: LibNC FF2 output adjoint localizes the missing gradient upstream](research_register/archive/part-007.md)
- [part-008.md: 2026-08-02: LibNC FF2 residual-adjoint replay frozen through 2026-08-02: MÖBIUS-2 JANUS parity token-fill ceiling frozen](research_register/archive/part-008.md)
- [part-009.md: 2026-08-02: MÖBIUS-2 JANUS parity token-fill ceiling is terminal negative through 2026-08-02: endpoint428 runtime-eligibility boundary re-audited](research_register/archive/part-009.md)
- [part-010.md: 2026-08-02: WIKIFORWARD prior-destination lexical ceiling proposed through 2026-08-03: corrected WIKISECTION exact-heading ceiling rejected](research_register/archive/part-010.md)
- [part-011.md: 2026-08-03: WIKIFORWARD prior-destination lexicon QM1 materialized through 2026-08-08 - HELICAL direct-WRT far-history QM3 closure](research_register/archive/part-011.md)
- [part-012.md: 2026-08-08 - NNCP/Endpoint common-raw-block routing closure through 2026-08-08 - NNCP midpoint persistence replicated at 262,144 symbols](research_register/archive/part-012.md)
- [part-013.md: 2026-08-08 - Exact native 65,536-symbol raw-proof guard corrected through 2026-08-09 - Exact output-head attribution maps to LibNC optimizer semantics](research_register/archive/part-013.md)
- [part-014.md: 2026-08-09 - Mature train-length retry crosses first block boundary through 2026-08-09 - Shared research-register partition is lint-enforced](research_register/archive/part-014.md)
- [part-015.md: 2026-08-09 - Exact decision-ID coverage reconciled across the shared register through 2026-08-09 - Exact KAIROS opening retires the final-head dyadic realization](research_register/archive/part-015.md)
- [part-016.md: 2026-08-09 - GGML output-head gradient and update parity proposed through 2026-08-09 - GGML head q1 exposes the direct-optimizer API boundary](research_register/archive/part-016.md)
- [part-017.md: 2026-08-10 - Full-score accounting q0 isolates one fixture-size error through 2026-08-10 - Conservative cmix-obias package boundaries are certified](research_register/archive/part-017.md)
- [part-018.md: 2026-08-09 - Branch-residual-weighted cache-32 proposed through 2026-08-09 - Historical FRACTAL-8 survival-hazard result recovered and retired](research_register/archive/part-018.md)
- [part-019.md: 2026-08-10 - Production output-head attribution is dependency-frozen through 2026-08-09 - cmix-obias technical source/runtime closure frozen](research_register/archive/part-019.md)

## Current entries

## 2026-08-10 - Production-alphabet midpoint bridge passes exactly

Candidate `nncp_libnc_full_dictionary_midsegment32_65536_qm0_v1` terminated
successfully on `65,536` symbols from the real `16,392`-symbol dictionary and
the corresponding `322,978` raw bytes. The faithful parent archive is
`148,140` bytes and the midpoint archive is `143,414` bytes, for an actual
gain of `4,726` bytes against the frozen `3,000`-byte gate. Exact
original-coordinate third gains are `1,593`, `1,775`, and `1,359` bytes; every
third is positive.

Clean and traced parent archives are byte-identical with SHA-256
`e4f1b99393bee047d5ee809182d0f0ace2fb5391b37d960d26ab0df878c2842b`.
Clean and traced midpoint archives are byte-identical with SHA-256
`85208cda0ab962d7f8ce61367e0902c0bb864de05e57e733534f782b54736134`.
Both decodes reproduce the same exact `322,978`-byte raw population with
SHA-256 `a5daeae040c2575ae1c2fd5f3284d73caafa0fcd48c3f546e199ab7c5f1ab7e9`.
The serialized schedule is valid: segment `64`, midpoint enabled, batch `32`,
seed `123`, BF16 enabled, CUDA disabled, vocabulary `16,392`. There are no
failed conditions.

The terminal guard reports return code `0`, peak single-process RSS
`6,380,124 KiB`, peak process-tree RSS `6,419,324 KiB`, and zero excess over
the decimal `10 GB` limit. This authorizes production `P/K/O/OK/F/S`
attribution scientifically but remains a four-thread closed-LibNC teacher
result with zero score credit, no single-core eligibility, no full-corpus
transfer, and no verified score. Under the frozen Gamma One order, proposal
`nncp_ggml_profile_forward_parity_64_qm0_v1` was activated and developed next;
attribution remains blocked until that parity candidate itself passes.

## 2026-08-10 - Gamma One compiles MIDAS into GRAM and ORBIT

The post-bridge Gamma path is now frozen as `Gamma One`: the reversible NNCP
symbol transform feeds a Gamma-authored, deterministic, single-thread CPU
predictor, a branch-local `GRAM-MIDAS-32` fast-weight correction, one integer
arithmetic stream, and the exact inverse. The 20-layer LibNC/GGML NNCP model is
an oracle and parity reference, not the intended submission codec. No teacher
archive, hidden trace, probability, or package normalization transfers to the
student.

The exact sequence is dependency-bound: terminal production bridge, open
one-segment profile parity, production `P/K/O/OK/F/S` attribution,
`nncp_gram_midas_full_hidden_65536_qm0_v1`, then
`gamma_orbit192_gram_midas_65536_qm0_v1`. Attribution cannot activate from the
bridge alone; it now also requires the parity receipt. GRAM cannot activate
without an attribution verdict explicitly authorizing it, and ORBIT cannot
activate without a GRAM verdict explicitly authorizing it. Both new proposals
have `operational_status=blocked_dependency` and zero score credit.

GRAM replaces a dense `16,392 x 1,024` midpoint mutation with sparse ephemeral
branch state. For each first-half truth-path branch, it accumulates the decoded
truth residual times a causal feature vector plus an intercept residual. It
then corrects only queried second-half branch logits using frozen counted
depth scales. The full-hidden gate requires an actual terminated arithmetic
gain of at least `ceil(0.90*G_O)`, positive original-coordinate thirds, a
shifted-truth margin of at least `ceil(0.10*G_O)`, exact symbol and raw inverse,
byte-identical replay, no deep midpoint rebuild, source no larger than `32,768`
bytes, and decimal-memory compliance. Any miss retires this formulation rather
than opening a rank, optimizer, tree, scale, or coefficient sweep.

ORBIT is one frozen `192`-dimensional causal feature engine: decoded dictionary
symbol, decoder-rebuilt structural mode, short hashed symbol contexts, compact
recurrent state, and bounded gated-delta memory. It optimizes the
residual-weighted first-half/second-half Gram geometry that affects truth-path
arithmetic bytes, not generic hidden-state error. Promotion requires its own
exact archive to retain at least `max(ceil(0.60*G_F), paid scope requirement)`,
positive thirds, failing shifted/permuted controls, exact deterministic inverse,
one runnable CPU thread at at least `1,500` transformed symbols/second,
incremental compressed source and parameters no larger than `131,072` bytes,
and decimal-memory compliance. A miss retires the fixed ORBIT-192 profile.

The counted targets remain distinct: prize lock below `109,685,197`, primary
Gamma objective at most `105,000,000`, and stretch `101,101,101` only after a
certified record exists. The official site currently identifies the eighth
winners, record `110,793,128`, an ongoing contest, and the single-core,
memory, disk, and self-containment boundary. Any eventual public claim must be
about a transparently AI-led new record after official verification, never the
first solution of a contest with prior winners. External theory motivating
test-time learning remains zero-credit context: `https://arxiv.org/abs/2407.04620`.

## 2026-08-10 - External cmix full-corpus jobs intentionally cancelled

The three live `cmix-obias` full-corpus jobs were intentionally terminated at
the user's direction after the authorship boundary was corrected. The external
bare decode had reached `16.38%`; source-built encodes A and B had each reached
`9.03%` with identical emitted-byte progress. These jobs tested David
Freelan's external candidate and supplied zero Gamma score or authorship
credit; they are no longer on the Gamma prize path.

Exact driver process groups were sent `SIGTERM`. The adaptive guards closed
with process return code `-15` and the worker registry records `241`; neither
value is a codec, roundtrip, compression, or memory verdict. Two independently
sessioned `cmix` children survived their drivers and were then terminated by
their exact process groups. No `cmix`, `archive9`, or external-candidate worker
remains. The NNCP production midpoint bridge was not targeted and remains the
sole active job.

The killed drivers could not execute normal temporary-directory cleanup.
Three exact incomplete regenerable `/dev/shm` scratch directories totaling
about `12.9 GB` were deleted after process verification; durable logs, guard
receipts, source/build certificates, and accounting receipts remain. This
operator cancellation does not retire the external codec scientifically and
does not create a full-1G result. It removes external qualification work from
the active resource budget so the Gamma-authored MIDAS/open-predictor route
can proceed without its CPU, memory, or memory-bandwidth contention.

## 2026-08-10 - Open GGML production-profile forward parity is dependency-frozen

Proposal `nncp_ggml_profile_forward_parity_64_qm0_v1` closes the explicit
decoder-eligibility step after the already passed GGML kernel and output-head
update parity gates. Direct inspection of the production `enwik9` profile
binds the specialized transformer to `20` layers, model width `1,024`, `8`
heads, key width `128`, inner width `3,072`, memory `256`, and segment length
`64`. This is a deliberate profile rewrite, not a generic shim for the roughly
`71` reachable closed LibNC calls.

The proposal is machine-blocked on a passing full-dictionary native midpoint
bridge. Once activated, it compares one receipt-bound LibNC segment with an
MIT GGML CPU implementation loaded from the same parameters and
decoder-visible memory. It requires deterministic finite hidden, key/value,
logit, tree, and branch outputs; at most `1e-5` matched tensor error; at most
one integer probability count of branch error with no truth-path disagreement;
a static source closure no larger than `2,000,000` bytes; and decimal-memory
compliance. A pass authorizes one full open forward archive screen only.

This is zero-credit source-eligibility infrastructure. It cannot inherit the
teacher archive, midpoint gain, or package normalization, and it cannot run
before the bridge verdict
`authorize_production_P_K_O_OK_F_S_attribution`. A miss retires the exact
profile port without tolerance, layer, dtype, or kernel sweeps. Evidence: the
proposal, archived part 019, GGML kernel q1, GGML head-parity q2, and the LibNC
source-eligibility audit q3.

## 2026-08-10 - Production bridge passes and fixed-shape parity is materialized

The production bridge is terminal PASS: parent `148,140` bytes, full midpoint
`143,414` bytes, and actual gain `4,726` bytes against the frozen `3,000`-byte
gate. Independently terminated original-coordinate thirds save `1,593`,
`1,775`, and `1,359` bytes; their one-byte nonadditivity against the whole
archive is termination overhead, not an additive archive decomposition. Clean,
traced, and repeated archives are identical, all `65,536` symbols decode, the
`322,978`-byte raw inverse is exact, the schedule matches, and strict decimal
memory passes. This is decisive zero-credit teacher evidence on the real
`16,392`-symbol representation, not a submission score.

The inherited `32 x 256` output-head scaffold has been removed from
`nncp_ggml_profile_forward_parity_64_qm0_v1`. Its replacement freezes stream
zero at original truth coordinates `[256,320)`, the earliest 64-symbol segment
whose complete 256-symbol memory is decoder-visible. A patched LibNC oracle
exports ordered, hashed parameters, selected-stream memory and input, causal
mask, relative tensors, every layer checkpoint, final logits/probabilities,
and the exact balanced-tree branch path. The fixture is explicitly zero-credit
and forbidden as a runtime dependency.

The open side is now a static CPU-only profile implementation: 20 layers,
width 1,024, eight 128-wide heads, GEGLU inner width 3,072, memory 256,
segment 64, relative span 320, and vocabulary 16,392. GGML performs fixed BF16
matrix products; the candidate explicitly implements the frozen BF16
conversion points, RMSNorm, relative shift, causal mask, attention softmax,
residual order, tanh GELU, output softmax, numerical symbol tree, and integer
probability quantization. Both the oracle extractor and open source closure
compile; the compressed open source closure is about 1.174 MB, below the
2.000 MB ceiling. No teacher or open forward has yet been executed under this
candidate, so it still has zero parity or score credit.

The first qm0 launch stopped after the frozen-input audit and before model
initialization. Its handwritten expected identity table contained incorrectly
transcribed digests; the actual pristine source is unchanged since July 26 and hashes to
`9a44757c4837607b0be9abc0bb2780dbe006b381728549481eedc339599a138a`.
An independent preflight then rebound the unchanged LibNC library,
preprocessed symbol stream, dictionary, and terminal bridge decision to their
complete measured SHA-256 values before qm1 could launch. The donor tarball,
source size, and all bound artifact bytes remain unchanged.
Peak sampled RSS was only `1,332 KiB`; therefore qm0 supplies no forward,
parity, compression, or memory evidence. Correction-only successor
`nncp_ggml_profile_forward_parity_64_qm1_v1` changes only those expected
identity constants and candidate/result names while preserving every
scientific parameter and gate.

Qm1 passed every corrected artifact identity and initialized the full teacher,
but terminalized before fixture export because its source patch instrumented
the `--encode_only` batch branch while the passing bridge and decodable archive
use the true sequential branch. It consumed `2,226.996` seconds, peaked at
`6,380,244 KiB` single-process and `6,417,024 KiB` process-tree RSS, and stayed
under the decimal limit. No fixture marker, open forward, tensor comparison, or
parity verdict exists, so this is an infrastructure rejection with zero
scientific or score credit.

Correction-only qm2 moves capture to the decoder-compatible sequence of 64
one-symbol evaluations at block position 256. It freezes parameters and memory
before position zero, records stream-zero truth paths as each symbol is coded,
captures the persistent key/value state after each append, and binds ordered
per-position hidden, attention, relative, logit, and probability tensors. The
open fixed-profile program reconstructs its 64 causal input symbols from the
decoder-visible predecessor plus the preceding 63 truths. Sequential oracle
tensors are aggregated in original position order; final K/V and invariant
relative tensors use their exact matched terminal/initial states. Geometry,
`1e-5` tolerance, one-count branch limit, source ceiling, and verdict are
otherwise unchanged.

Qm2 reached the intended block-256 boundary, wrote the complete
`659,578,911`-byte parameter snapshot, `10,507,510`-byte decoder state, exact
target symbols/tree stream, and exactly `15,616 = 244 x 64` selected-stream
checkpoint tensors. It peaked at `6,380,220 KiB` single-process and
`6,417,340 KiB` tree RSS with no violation. Validation then stopped before the
open build because the declared per-layer manifest order placed persistent K/V
before relative tensors, while LibNC constructs/dumps the relative tensors
before entering the sequential append branch. Qm2 therefore proves that the
sequential capture boundary and population are correct but provides no open
parity verdict. Qm3 changes only this ordered manifest contract; no tensor,
model, arithmetic path, tolerance, or promotion threshold changes.

Qm3 accepted the corrected manifest and bound all `15,616` checkpoint tensors,
then produced a deterministic `2,543,298,652`-byte compressed oracle fixture.
The open executable built within its `1,173,776`-byte compressed source ceiling,
but stopped before its first calculation: its loader incorrectly required the
64 sequential occurrences of each internal checkpoint label to be globally
unique. A direct replay against the preserved fixture reported `duplicate
tensor name: embedding_input`. Parameters and initial state remain unique;
the repeated internal tensors are ordered comparison evidence. Qm3 therefore
has no parity verdict and zero score credit.

Correction-only qm4 retains strict parameter/state uniqueness while validating
internal tensors by their already bound category index and payload. It also
preserves a failed open subprocess's stdout/stderr in the adaptive log. The
fixture selection, tensor values, profile implementation, `1e-5` tolerance,
branch conditions, package ceiling, and authorization verdict are unchanged.

## 2026-08-10 - Production forward numerical correction chain reaches local parity

Qm4 through qm8 repaired only representation and operation-order defects found
at the first mismatching checkpoint: sequential tensor addressing, matrix
layout, RMSNorm scalar order, the observed reduction lanes, and explicit BF16
node boundaries. Qm9 then tested a sequential AVX/FMA dot product and exposed
that LibNC's default four-thread kernel does not use one 1,024-wide reduction.
Qm10 and qm11 tested non-fused variants and were worse. Qm12 tested an inferred
BF8 boundary and was also worse; all three are diagnostic rejections with zero
score credit.

An exact dispatch probe and kernel trace established the missing rule: LibNC's
default kernel splits each 1,024-wide dot into eight 128-input AVX/FMA chunks,
resets the partial accumulator at each chunk, then adds chunk results. Qm13
implemented that rule. Its durable receipt has exact layer-zero attention
input, key state, value state, relative weight, and relative bias. The first
mismatch moved to attention probability (`3.0517578125e-05` maximum); the full
forward still missed by `0.078125`, and the branch-count error fell to `106`.
The repeated open outputs are byte-identical, source closure is `1,174,284`
bytes, fixture package is `2,543,303,900` bytes, and the run stayed below the
decimal memory guard. Qm13 therefore remains a zero-credit parity rejection.

Qm14 applied the same proved reduction to transposed content and relative
attention products. A manifest-bound replay showed that its pre-softmax scores
are exact: passing all `163,840` layer-zero scores through LibNC reproduces the
oracle attention probabilities bit-for-bit. Qm15 replaced `std::exp` with an
open AVX2 implementation of LibNC's BF16 exponential polynomial, fixed 64-item
sum tree, binary block accumulation, and BF16 normalization. Layer-zero
attention probability then became exact. Qm16 applied the 128-input reduction
to the 320-wide attention-value product; every checkpoint in layers zero and
one became exact.

Qm17 corrected the remaining softmax boundary from elementwise division to
LibNC's single reciprocal followed by multiplication. Exactness then extended
through layer three. A direct open-versus-LibNC replay isolated the next defect
to the feed-forward RMS normalization after an exact layer-four attention
residual. Qm18 replaced the approximate 16-lane squared-sum with LibNC's exact
64-item AVX2 square-reduction and binary block tree.

Qm18 is terminal PASS on both the preserved fixture and an independently
regenerated guarded fixture. Maximum tensor error is exactly zero; repeated
open outputs are byte-identical; all 896 branch rows preserve tree topology,
symbol order, and truth path; maximum integer probability difference is one
count, exactly at the frozen allowance. The compressed source closure is
`1,175,720` bytes with no forbidden dynamic dependency. Peak sampled RSS was
`6,380,224 KiB` single-process and `6,417,168 KiB` process-tree, below the
decimal guard. Its zero-credit verdict is
`authorize_production_P_K_O_OK_F_S_attribution`, so the dependency-frozen
six-arm production attribution may now materialize without changing its gates.

## 2026-08-10 - Production output-head attribution implementation reaches exact smoke parity

Candidate `nncp_libnc_output_head_midpoint_attribution_65536_qm0_v1` now
materializes one serialized `P/F/K/O/OK/S` decoder contract over the exact
production NNCP source. `O`, `OK`, and `S` retain LibNC's proved 64-state
backward geometry but filter midpoint optimizer writes to the existing
`embed_out` and `out_bias` variables. `S` cyclically shifts first-half truths
within each stream. `K` discards and rebuilds without a midpoint update; `OK`
adds an extra discard/rebuild cycle after the identical head-only update.

The one-segment, `2,048`-symbol smoke is infrastructure evidence only. Every
arm decoded the same `9,965`-byte raw population. `P` and `K` were both
`55,635` bytes and differed only at serialized schedule offset 18. `O` and
`OK` were both `55,628` bytes and likewise differed only at offset 18; their
head-gradient, updated-head, complete-parameter, persistent-memory, and
optimizer-step witnesses were exact. Shifted `S` was `55,633` bytes, preserved
the target-multiset bias update, and changed the aligned weight update as
intended. No allocator leak remained.

The indexed observer rebuilt successfully and reproduced O's clean archive
byte-for-byte. The complete compressed incremental source package is `10,432`
bytes against the frozen `65,536`-byte ceiling. This authorizes the already
frozen guarded `65,536`-symbol run; it supplies no compression promotion or
score credit. The scientific thresholds remain O gain at least `3,781` bytes,
O over S at least `473` bytes, and original-coordinate third floors
`[1,275, 1,420, 1,088]`.

The first guarded qm0 launch failed before extraction because the driver
created its temporary source directory and then called the bridge helper that
also requires creating it. It ran no arm, returned `1`, sampled only `1,284`
KiB RSS, and provides zero scientific evidence. Correction-only qm1 extracts
into the already-created directory and retains every scientific input, arm,
threshold, observer, and guard unchanged.
