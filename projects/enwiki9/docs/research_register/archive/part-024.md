# Research Register Archive 024

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-24 - FOSSIL-MATCH targets exact history beyond FXCM's 16 MiB ring

`fxcm_fossil_match_q0_v1` is a new zero-credit information-source design, not
a checkpoint or optimizer variant. The frozen FXCM match model stores absolute
32-bit candidate positions, but `bufr(position)` always resolves through
`buffer[position & 0x00ffffff]`. Once a position is more than `16,777,216`
transformed bytes old, the model reads the current ring alias rather than the
original decoded byte. This proves an information gap in the implementation;
it does not prove that enwik9 contains useful far repetitions.

FOSSIL-MATCH keeps the exact already-decoded transformed prefix in an
append-only file-backed history and a fixed `2^24` table of 8-byte records.
Before byte `i`, it hashes and exactly verifies the preceding 16 decoded bytes,
requires a continuation distance above 16 MiB, and predicts only the byte at a
strictly earlier verified continuation. It scores before inserting the current
truth. Encoder and decoder therefore have identical information and update
order without transmitting offsets or commands.

The first eventual scan freezes K/D/R/S/N. K performs all bookkeeping with
prediction disabled. D reads exact far history. S reads D's identical absolute
position through the parent's 16 MiB alias, isolating exact addressability.
R supplies deterministic random bytes and N negates D. The full transformed
population must repeat exactly, every chronological third and multiple distance
buckets must be positive, D must beat every matched control, and incremental
process-tree memory is capped at `262,144 KiB`. The target-scale impossibility
screen requires at least `254,953` active bytes because one active byte has at
most 16 bytes of optimistic leverage under the parent's count floor.

Passing would authorize only exact retained-parent surprisal tracing at the
sealed opportunities. A native P/K/D finite archive, exact inverse, package,
memory, runtime, and distant transfer remain mandatory. A prospectively frozen
[`adaptive experiment`](../../../operations/adaptive/experiments/fxcm_fossil_match_q0_v1.json)
and dependency-gated proposal now bind the design to Gamma's workflow. The
proposal was rejected before implementation after an independent static audit
found that its resource and transition proof surface was underfrozen. No
scanner, source, candidate revision, scan, or receipt exists, so v1 has zero
compression and score credit. See the
[`design contract`](../../../operations/planning/fxcm_fossil_match_q0_v1.json).

Correction-only `fxcm_fossil_match_q0_v2` retains the same information source
but closes those static defects before source exists. It freezes a modulo-
`2^64` 16-byte polynomial hash, the exact `2^24` record layout and sentinel,
unconditional post-score replacement, no continuation state, the parent's
pre-insertion ring-alias control, SplitMix and negated controls, and six
inclusive distance buckets. The scanner must route every nonsequential byte
read through an `index < current_position` accessor.

v2 also replaces a weak global transfer check. D must now beat the maximum of
S/R/N separately in every chronological third and in at least two distance
buckets. Its resource gate includes process-tree RSS, fresh cgroup-v2 peak,
sampled file-cache residency, max/OOM/OOM-kill events, and scratch; even a
standalone pass can authorize only donor-surprise tracing. Native integration
still requires a fresh joint parent-plus-specialist cgroup, process-tree,
archive, inverse, runtime, and package replay. The v2
[`design`](../../../operations/planning/fxcm_fossil_match_q0_v2.json),
[`experiment`](../../../operations/adaptive/experiments/fxcm_fossil_match_q0_v2.json),
and dependency-gated proposal receive zero credit. Candidate development found
a real provenance defect before source materialization: the proposal's frozen
superseded-v1 qualification-policy digest does not match the retained v1 file.
Claim/develop therefore failed closed. The rejection transition then exposed a
workflow atomicity defect: it wrote `state=rejected` before recursive evidence
validation failed, leaving the quarantined exact bytes under the `proposed/`
path. v2 remains unclaimable and unexecuted; its path is retained because v3
hash-binds the failure artifact. The shared adaptive controller is active for
qm8, so its transition implementation is not edited under that process.

Correction-only `fxcm_fossil_match_q0_v3` changes no scientific transition,
control, bucket, threshold, or resource ceiling. It replaces only the stale
activation binding with source-bound q1 qualification policy v4 and adds the
missing executable proof closure. The native candidate now contains an exact
C++ scanner, zero-credit interface, and strict local scan schema. Its semantic
state is exactly `150,994,944` bytes: `2^24` eight-byte table records plus the
parent-equivalent `2^24`-byte ring. Every random historical read goes through
one `PastBytes(begin,size,current)` guard, whose requested terminal offset must
not exceed `current`; prediction and all D/S/R/N scoring precede table, ring,
and rolling-hash mutation.

The scanner emits chronological-third and six-distance-bucket control tables,
terminal table/ring hashes, an exact opportunity digest, a terminal rolling-
hash recomputation, and duplicate treatment/K transition digests constructed
without any control outcome. The sealed native candidate tree is
`bff0b35e7ce18439839bf7291d096f602908d455018bd6643122d7bbc899ed39`.
Clang syntax validation initially exposed a toolchain environment failure:
the sealed driver could not find `libLLVM-17.so.1`. The execution plan now
binds the regular resolved Clang binary, canonical `--driver-mode=g++`, the
exact loader library and `LD_LIBRARY_PATH`, rather than treating that failure
as an algorithm result.

The source-bound runner and independent verifier re-open a positive v2-format
q1 receipt under exact policy v4, rerun the policy-bound parent verifier before
lease acquisition, hash the complete transformed population, compile from the
sealed candidate, and launch two fresh scanner processes. Each process is
single-CPU and bounded at `196,608 KiB` process-tree RSS, `760,000,000` bytes
cgroup memory including file cache, and `100,000,000` scratch bytes. The runner
samples cgroup file residency independently, requires zero max/OOM/OOM-kill
events and cleanup, and emits an exact output manifest. The verifier
reconstructs compiler, guard, taskset, cgroup, scan, lease, measurements,
gates, and verdict from retained artifacts.

Only static JSON-schema validation, Python AST parsing, policy/hash closure,
candidate-revision sealing, and C++ syntax compilation have run. No transformed
population scan or finite archive has run because qm8 still owns the exclusive
full-1G lease and q1 is not qualified. v3 therefore has zero compression,
authorship-score, and objective credit. See the
[`scientific design`](../../../operations/planning/fxcm_fossil_match_q0_v3.json),
[`execution plan`](../../../operations/planning/fxcm_fossil_match_q0_v3_execution.json),
and [`experiment`](../../../operations/adaptive/experiments/fxcm_fossil_match_q0_v3.json).

An independent post-materialization audit was reconciled against the current
revisions rather than the superseded drafts it inspected. Its q1 objection
applies to the authority-revoked v1 qualification receipt and verifier, which
accepted caller-supplied full-stream digests and a persistent-state boolean.
Policy v4 instead binds the v2 artifact router and verifier: the verifier
reopens every retained artifact, reruns both soft-pressure arm verifiers, the
full probability/state verifier, and the Geekbench-5-bound runtime verifier,
and requires the recomputed objects to equal the supplied verifications. Thus
the old v1 weakness is real historical evidence but is not a present v4 proof
path. Runtime remains a required future measured artifact, not an inferred qm8
property.

The same audit's FOSSIL-MATCH objections were already the reason v1 was
rejected and are explicit v3 predicates: cgroup peak includes file cache and
must stay at or below `760,000,000` bytes with zero max/OOM/OOM-kill events; D
must beat S/R/N in every chronological third; and the hash constants,
index/tag split, sentinel, replacement order, no-continuation rule, alias
off-by-one, and distance buckets are frozen in the interface and sealed source.
This reconciliation adds no run evidence. It confirms only that v3 tests the
intended causal mechanism under the corrected proof surface.

## 2026-08-24 - WIKI-PDA v1 is causally rejected and v2 closes the proof surface

The dormant `wiki_pda_structural_replay_q0_v1` scanner was rejected by static
inspection before any transformed-population run. Its transition-table lookup
is selected only after the current opening `L` truth has entered parser state,
but its offline scoring loop then credits transition target offset zero. That
position predicts the already observed `L`, so v1 can receive one free correct
byte per predicted event. The source also initializes its declared FNV-1a
digest with `1469598103934665603` rather than the standard 64-bit FNV-1a offset
`14695981039346656037`. Its ad hoc runner does not source-bind the compiler,
candidate, q1 authority, resource guard, managed lease, result file set, or an
independent decision verifier. These are proof defects, not measured negative
compression evidence. v1 remains unexecuted and has zero credit.

Correction-only `wiki_pda_structural_replay_ceiling_q0_v2` changes causal
scoring and proof closure while retaining the scientific mechanism and frozen
scale: 16-byte names, depth 16, 1,024 direct-mapped unanimous transition
records, poisoned conflicts, exact closing-name replay, and the `4,079,243`
correct-byte threshold. The scanner consumes `L` before lookup but forbids T
credit until relative offset one. C cannot activate until decoded `L/slash`
and relative offset two. For each current byte, D/R/S/N are selected and
scored from state through the previous byte before truth changes parser,
table, stack, or digests. R, cyclically rotated S, and negated N use every and
only D's active positions; T has deterministic overlap priority over C.

The scanner emits C/T attribution, D/R/S/N counts in three exact transformed
coordinate thirds, dedicated forbidden-early counters, standard FNV-1a input,
opportunity, table, stack, and terminal-state digests, and duplicate K/D
transition digests. The prospective gate requires two byte-identical complete
receipts, D correct bytes at least `4,079,243`, D strictly above max(R,S,N) in
every third, zero early-credit counters, causal identity, and both resource
guards passing at `65,536 KiB` process-tree and VmHWM, `256,000,000` cgroup
bytes including cache, `100,000,000` scratch bytes, one CPU, and zero
max/OOM/OOM-kill events.

The native candidate is sealed at tree
`8f674767ceb8f452f24f2167460f89519957652624340ef3ecdcd1dfa2302419`.
Its five counted candidate files total `30,596` bytes, below the prospective
`65,536`-byte ceiling. The execution plan binds that revision, scanner,
interface, local receipt schema, runner, independent verifier, shared
content-addressed proof helper, five result schemas, q1 policy-v4 verifier,
managed lease, v3 resource guard, resolved Clang toolchain and loader, taskset,
and exact `587,138,826`-byte transformed population. Static schema, AST,
candidate-revision, plan-binding, and C++ syntax checks pass.

No corpus hash, scanner process, executable link, result root, or receipt was
created. qm8 still owns the exclusive full-1G lane and q1 has not produced the
required positive v2 qualification. This candidate is therefore a frozen
zero-credit causal ceiling only. A future pass authorizes retained-parent
donor-surprise tracing; it cannot authorize a WIKI-PDA archive, package,
inverse, prize score, or Gamma score credit without a fresh native replay. See
the [`design`](../../../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2.json),
[`experiment`](../../../operations/adaptive/experiments/wiki_pda_structural_replay_ceiling_q0_v2.json),
and [`execution plan`](../../../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_execution.json).

### 2026-08-24 - WIKI-PDA v2 receives a correction-only q1-v3 authority successor

The frozen WIKI-PDA v2 scanner did not change, but its first execution plan
became stale when q1 policy v6 revoked all policy-v4/v2-verifier successor
paths. `wiki_pda_structural_replay_ceiling_q0_v2_execution_v2` corrects only
that parent-authority axis. It retains candidate tree
`8f674767ceb8f452f24f2167460f89519957652624340ef3ecdcd1dfa2302419`,
scanner
`3e9aebfa0b32aa57fc23eb41b91bfc6dde737ff0428fbe28a7fa1ac52af4b82f`,
the exact `587,138,826`-byte population, all D/R/S/N definitions, the
`4,079,243`-correct-byte threshold, chronological-third predicates, and every
resource ceiling.

The successor requires a future active q1 policy revision at least 7, a
schema-valid q1-v3 authority router, an exact stored v3 verification, a fresh
independent v3 re-verification, and an absent full-1G lease and lock. Its
decision and independent verifier bind both the active policy and the v6
design policy. The old policy-v4 execution plan remains stale and has no
execution authority.

AST, Draft 2020-12 schema, exact 32-artifact plan-binding, candidate-tree,
scanner-hash, and diff checks pass. No population scan, compilation, result
root, or receipt was created because qm8 owns the live full-1G namespace and
q1-v3 authority does not yet exist. This remains the same zero-credit causal
ceiling, not a new algorithm and not Hutter evidence. See the
[`authority review`](../../../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_authority_v3_review.md)
and [`execution successor`](../../../operations/planning/wiki_pda_structural_replay_ceiling_q0_v2_execution_v2.json).

## 2026-08-24 - WIKI-LOOM freezes semantic virtual time as a dormant new source

An exclusion audit rejected three superficially creative routes before any new
source was written. Whole-page semantic permutation repeats exact negative
article-order, geometry, revision-order, and GEPA evidence. Entity/template
retrieval repeats terminal WIKIBACK, WIKIFORWARD, WIKIGRAPH, TESSERA, SRSTC,
typed Skip-CTS, and FRACTAL slot-trie neighborhoods. Explicit far-history
macros repeat paid copy/ledger failures. Those mechanisms remain retired at
their measured boundaries.

`wiki_loom_shared_state_lstm_q0_v1` instead changes the time coordinate of an
auxiliary recurrent expert. The raw byte stream and authoritative q1 parent
remain untouched. Once the opaque post-WRT parser has completely decoded a
template name and explicit field key or positional index, it selects one of
`4,096` direct-mapped hidden/cell slots. The selected state advances only on
bytes in that template-field value. When the same descriptor returns later,
the expert therefore resumes a virtual field-local trajectory even though
unrelated bytes and pages were interleaved in the real stream.

The auxiliary transition reads the current parent ByteMixer recurrent
parameters but is no-train: it cannot write parent weights, optimizer,
deferred updates, recurrent state, mixers, contexts, SSE, preprocessing, or
coder state. It is not a full-CMIX checkpoint, fork, rejoin, page permutation,
copy command, or new model asset. Its new information is the decoder-derived
projection of history onto a structural subsequence. A fingerprint miss sleeps
for the entire field, then initializes the slot; a hit must have `128` prior
bytes at field entry. One global SAFE-MIX posterior combines the awake expert
with P and neither updates nor resets while sleeping.

The prospective native arms are P/K/D/M/G/S/R/N. K must be byte-identical to
P while exercising all mechanism bookkeeping. G uses one unpartitioned
auxiliary state; S uses the previous completed field descriptor; R uses causal
ordinal-random routing; N complements the aligned byte distribution. The
opening-10M gate requires exact finite archives and inverses, deterministic M
repeat, positive M gain in every third, at least `50,000` net bytes after
incremental source/framing, and at least `10,000` byte-equivalent raw-D margin
over every matched control. One miss retires the frozen slot, warmth, route,
state, and mixture realization without a sweep.

The [`design`](../../../operations/planning/wiki_loom_shared_state_lstm_q0_v1.json),
[`Mechanism IR`](../../../operations/planning/wiki_loom_shared_state_lstm_q0_v1.mechanism-ir.json),
[`experiment`](../../../operations/adaptive/experiments/wiki_loom_shared_state_lstm_q0_v1.json),
and dependency-dormant proposal are schema-valid and hash-bound. No source,
compiled causal closure, run, probability, archive, inverse, saving, or score
exists. Router revision 4 authorizes a source audit only after q1 qualifies,
CMIX adaptation/open NNCP/WIKI-PDA terminalize subscale, and the already-frozen
WIKI-SCHEMA and FOSSIL-MATCH routes are terminally classified. WIKI-LOOM
therefore has zero credit and does not delay the current q1, WIKI-PDA,
WIKI-SCHEMA, FOSSIL-MATCH, or MIDAS order.

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

The initial sealed candidate tree was `3d110ac4...680c5`; strict C++17 syntax
validation and all registered JSON schemas passed. Its prospective rule was
`4,079,243` correct D bytes, with every chronological third positive and D
strictly above R and S. That number was a hypothesis, not a result. No scan or
decision receipt exists. The runner fails closed unless it receives a
fully positive, independently verified q1 qualification with runtime and
package closure, process-tree peak at most `9,000,000 KiB`, and a released
full-1G lease. See the
[`execution contract`](../../../operations/planning/wiki_schema_vm_ceiling_q0_v1.json),
[`experiment`](../../../operations/adaptive/experiments/wiki_schema_vm_ceiling_q0_v1.json),
and
[`interface`](../../../programs/wiki_schema_vm_ceiling_q0_v1/interface-contract.json).

A later read-only proof audit confirmed the byte-order causality: each active
prediction is scored before the current byte mutates parser or table state,
programs are close-committed from earlier invocations, and a mismatch terminates
the opportunity before any successor byte is counted. It also found that the
first runner merely observed a free `exclusive_full1g` lease and therefore had
a check-to-launch race. Planning revision 2 corrects only that execution
boundary: the unchanged candidate tree now runs under an atomically acquired
managed lease whose evidence and transition chain are required outputs. The
output manifest additionally compares the complete pre-manifest directory to
the frozen filename set, so unlisted files prevent closure. The same audit
found that the plan's former generic `$schema` label did not validate its actual
shape. Revision 2 replaces it with a dedicated strict schema, and the runner
now validates that plan plus every transitive source, schema, compiler, lease,
population, command, and output binding before acquisition. This is static
harness evidence only; the scanner remains unexecuted and receives zero credit.

The same audit rejected the initial correct-byte rule as futility authority.
CMIX discretizes every bit probability to at least `1/65,536`; consequently an
active byte has up to `8 * 16 = 128` bits, or 16 bytes, of optimistic parent
log-loss leverage. A byte that misses D can also share a correct leading-bit
prefix. Therefore `4,079,243` correct bytes are neither a necessary condition
for target-scale gain nor an arithmetic-code ceiling. The corrected unmeasured
revision `0e08910e...ba958a` preserves the scanner implementation and instead
requires at least `ceil(4,079,243 / 16) = 254,953` active opportunity bytes,
positive correct bytes in every third, and strict wins over R and S. It reports
the old one-byte-per-correct screen only as a diagnostic. Passing authorizes an
exact retained-parent donor-surprise trace; only that trace can determine the
available parent log-loss, and only a native finite archive can establish gain.

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
[`Arm A`](../../../results/cmix_obias_source_full1g_roundtrip_a_qm0_v1/decision.json),
[`Arm B terminal receipt`](../../../results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-receipt.json),
[`independent verification`](../../../results/cmix_obias_source_full1g_roundtrip_b_qm0_v1/oom-terminal-verification.json),
and [`A/B audit`](../../../results/cmix_obias_source_full1g_ab_terminal_audit_v2/decision.json).

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
[`scope receipt`](../../../results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/06_scope_identity/fixed-reset-scopes/scope-identity-receipt.json).

The cumulative opening-1M successor also passes. Both arms emit the same
`172,605`-byte payload (`a723ca62...d70db7`), the same exact probability stream
(`d34a8d4b...5458d`), and byte-identical complete traces; both restore the
canonical 1,000,000-byte prefix with SHA-256 `369b6889...52cad`. Its four
guards pass at worst sampled tree RSS `8,388,568 KiB`, worst sampled scratch
`20,991,792,710` bytes, and one allowed CPU. See the
[`cumulative receipt`](../../../results/cmix_obias_memory_safe_parent_filebacked_q1_qualification_qm7_v1/07_cumulative_identity_1m/cumulative-identity-receipt.json).

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
[`terminal receipt`](../../../results/cmix_filebacked_fxcm_full_a_qm7_v2/full-roundtrip-receipt.json),
[`verification`](../../../results/cmix_filebacked_fxcm_full_a_qm7_v2/full-failure-verification.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260823T213424Z_653b446c89.json).

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
[`cmix_filebacked_fxcm_full_probability_state_identity_q0_v1`](../../../operations/planning/cmix_filebacked_fxcm_full_probability_state_identity_q0_v1.json).
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
[`decision`](../../../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../../../results/nncp_libnc_top_w_o_input_adjoint_64_q0_retry_v1/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T162351Z_97a6519638.json).

The open matrix-gradient attribution first reproduced a prospectively fixed
128-row slice, then expanded the same chronological kernel across all
1,048,576 `w_o_19` weights. Each state accumulates its 32-stream dot from
zero with sequential AVX2 FMAs, adds the decoded prior BF16 gradient after the
dot, and rounds once to BF16. The full treatment is exact; its sign-negated
control differs everywhere. See the full
[`decision`](../../../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_w_o_gradient_full_post_add_64_q0_v1/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T163533Z_7a29124cd9.json).

The complete transpose then transferred the independently attributed
128-feature panel schedule to `w_o_19`. Eight ordered panels reproduce every
one of the 2,097,152 source input-adjoint words exactly across two replays. A
single unblocked 1,024-feature chain differs in 285 words and the sign-negated
control differs everywhere. The evaluator has no LibNC, GGML, CUDA, OpenMP,
BLAS, or other forbidden dynamic dependency. See the
[`decision`](../../../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_w_o_input_adjoint_block128_64_q0_v1/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T164348Z_ff5718724e.json).

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
[`decision`](../../../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/decision.json),
[`execution receipt`](../../../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/execution.json),
[`guard`](../../../results/nncp_open_top_w_o_input_forward_64_q0_retry_v2/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T171305Z_fdae41e74c.json).

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
[`decision`](../../../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/decision.json),
[`execution receipt`](../../../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/execution.json),
[`guard`](../../../results/nncp_libnc_pre_ff_same_run_contributions_64_q0_retry_v3/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T155008Z_4831e25438.json).

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
[`decision`](../../../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../../../results/nncp_open_top_pre_ff_total_adjoint_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T155508Z_53d5388d2c.json).

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
[`decision`](../../../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_libnc_ff1_weight_slice_schedule_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T114029Z_4b8fd50e01.json).

The first open arithmetic grid then refuted its frozen prior-initialized FMA
hypothesis: that cell and the nonfused cell each missed 43 of 131,072 words.
The prospectively declared post-dot cell was exact. Its immutable successor
confirmed the localized contract over the entire slice and two replays:
accumulate each 32-stream dot from zero with sequential AVX2 FMAs, add the
decoded prior BF16 gradient after the dot, then round-to-nearest-even BF16
once per state. It also reproduced the independent reverse-state and
sign-negated oracles exactly while retaining both 43-word failures. See the
grid
[`decision`](../../../results/nncp_open_ff1_weight_slice_kernel_grid_64_q0_v1/decision.json)
and
[`reflection`](../../../operations/adaptive/reflections/20260816T115801Z_99a2e7695e.json),
then the immutable successor
[`decision`](../../../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_ff1_weight_slice_post_add_64_q0_v1/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T120602Z_ec1474d292.json).

Finally,
`nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1` expanded that uniform
kernel to the complete 1,024-input by 6,144-output matrix without changing
arithmetic. Both full 6,291,456-word projections replayed byte-for-byte. Every
one of 48 prospectively fixed 128-row partitions, the inherited parent slice,
and the retained production gradient matched exactly. The generated gradient
also reproduces the retained artifact SHA-256. The executable has no LibNC,
GGML, BLAS, OpenMP, or CUDA dependency and passed the decimal-memory,
temporary-disk, source-closure, and cleanup guards. See the
[`decision`](../../../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_profile_top_ff1_gradient_post_add_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T121133Z_b2c70f9ec5.json).

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
[`decision`](../../../results/nncp_libnc_top_ff1_input_adjoint_64_q0_v1/decision.json)
and
[`reflection`](../../../operations/adaptive/reflections/20260816T121911Z_d066eaf1cf.json),
then the corrected
[`decision`](../../../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/execution.json),
[`guard`](../../../results/nncp_libnc_top_ff1_input_adjoint_64_q0_retry_v1/guard.json),
and
[`reflection`](../../../operations/adaptive/reflections/20260816T123446Z_5cbfc56c6d.json).

Finally, `nncp_open_top_ff1_input_adjoint_block128_64_q0_v1` transferred the
already attributed LibNC matmul-driver schedule from FF2 to the wider FF1
transpose. Forty-eight ordered 128-feature panels reproduced every source
input-adjoint word exactly across two full replays. A one-panel unbroken
6,144-feature reduction differed in 1,256 words, proving that the panel
boundary remains operationally live. The generated open artifact reproduces
the source-oracle digest and the executable has no LibNC, GGML, BLAS, OpenMP,
or CUDA dependency. See the
[`decision`](../../../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_top_ff1_input_adjoint_block128_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T123635Z_f1f6615808.json).

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
[`decision`](../../../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/execution.json),
and
[`guard`](../../../results/nncp_open_profile_top_ff1_bias_gradient_avx2_64_q0_v1/guard.json).

Static `nc_backward` attribution showed that each broadcast-bias parameter
node invokes `nc_reduce_sum(existing_gradient, state_gradient, 1)`. Candidate
`nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1` therefore replayed the 64
chronological `[6144, 32]` state panels instead of flattening all 2,048
samples. The source operation reproduced every retained word exactly; the
flat control retained 4,708 mismatches and the reverse-state control retained
5,099. See its
[`decision`](../../../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/execution.json),
[`guard`](../../../results/nncp_libnc_ff1_bias_state_reduce_64_q0_retry_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T111831Z_64dcc1173e.json).

The immutable LibNC-free successor
`nncp_open_ff1_bias_state_reduce_64_q0_v1` then implemented the attributed
contract directly: decode the prior BF16 gradient, add streams 0 through 31
sequentially in float32, and round-to-nearest-even BF16 once after each state.
Two complete executions were byte-identical and matched all 6,144 independent
LibNC oracle words with zero error. The flat, reverse-order, and sign-negated
controls remained live; the executable had no LibNC, GGML, BLAS, or OpenMP
dependency. See the
[`decision`](../../../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_open_ff1_bias_state_reduce_64_q0_v1/guard.json), and
terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T112548Z_7841e2cc5b.json).

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
[`decision`](../../../results/nncp_libnc_ff2_transpose_lane_order_64_q0_v1/decision.json)
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T093214Z_c6950a77d0.json).

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
[`decision`](../../../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/decision.json),
[`execution receipt`](../../../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/execution.json),
[`guard`](../../../results/nncp_libnc_ff2_transpose_block128_64_q0_v1/guard.json),
and terminal
[`reflection`](../../../operations/adaptive/reflections/20260816T093907Z_7f51e2d346.json).

This authorizes one uniform open FF2-transpose implementation: adjacent
output-feature SIMD lanes, ordered 128-feature reduction panels, one panel
combination before the next panel, and one final BF16 conversion. It remains
zero-credit teacher-removal evidence and proves no GEGLU, FF1, recursive
update, compression improvement, transfer, package, or Hutter result.
