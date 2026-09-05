# Research Register Archive 023

[Register index](../README.md) | [Current register](../../research_register.md)

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
[`100M gate`](../../../operations/planning/cmix_filebacked_fxcm_100m_identity_resource_q0_v1.json).
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

### Midpoint persistence attribution v1 is superseded; correction-only v2 is frozen

A pre-execution authority audit found that the original
`cmix_obias_midpoint_persistence_attribution64_q0_v1` cannot validly execute.
It names `cmix_obias_full_midpoint_oracle64_q0_v1`, which was already
superseded before execution because the donor CMIX update horizon is 128
events and therefore cannot be invoked unchanged at a 32-event midpoint. The
v1 attribution also allowed its persistent branch to name a compact
curvature/tangent successor without first binding functional-JVP evidence. No
v1 proposal, source candidate, archive, or scientific result exists. Its
immutable supersession receipt records zero score credit.

Correction-only
`cmix_obias_midpoint_persistence_attribution64_q0_v2` now binds the actual
source-defined 32-event truncated-BPTT oracle v2 and the exact q1 qualification
policy v4. Its P/F/J/S comparison preserves the original scientific question
and the preregistered `0.80` threshold. J must reproduce F's aligned update and
adapted probability/state trajectory through byte 63 while a simultaneously
advanced untouched branch reproduces P. At the join, every adapted
probability-affecting write is discarded, the untouched parent state is
retained, and the arithmetic coder interval is neither forked nor rewound.
Truth-only storage may be shared only after a source and writable-alias audit;
copy-on-write, sparse journals, or recomputation are implementation choices,
not weaker state semantics.

The execution ladder begins with a 250KB exactness/rejoin gate; a pass
authorizes only 1MB calibration, and a target-scale causal 1MB pass authorizes
only the 10MB attribution. The decisive test is exact integer arithmetic on a
fresh 10MB P/F/J/S joint archive: `F_gain = archive(P)-archive(F)`,
`J_gain = archive(P)-archive(J)`, and local retention passes exactly when
`5*J_gain >= 4*F_gain`. F must still save at least `40,793` bytes and beat its
frozen shifted S control. A retention pass authorizes only SAFE-FORK source
materialization. A retention miss authorizes only functional-JVP persistence
attribution; it cannot directly authorize a persistent codec.

The planning contract, current structured experiment, oracle authority
interface, receipt and verification schemas, and independent arithmetic/hash
verifier are frozen. Adaptive proposal
`cmix_obias_midpoint_persistence_attribution64_q0_v2` is explicitly
`dormant_dependency`: it cannot be claimed until q1 has a positive terminal
policy-v4 qualification decision and the shadow midpoint oracle v2 has a
positive terminal 10MB decision. No execution, source candidate, archive gain,
compression credit, or score credit is claimed.

The historical mutation router and SAFE-FORK v1 contract also named the
superseded attribution. Router v2 now binds the corrected oracle, attribution,
sealed SAFE-MIX v2 wrapper, and one-successor ladder. SAFE-FORK v1 is
explicitly superseded before execution; only a positive 10MB attribution-v2
receipt may authorize materializing one new SAFE-FORK v2 source candidate.

### Source-level closure supersedes midpoint oracle v2 and its attribution dependency

A direct audit of the sealed q1 C++ source found that shadow midpoint oracle
v2 was still not implementable as written. `Predict(x_t)` writes the
distribution for `x_(t+1)`, and the corresponding target is installed only by
the later `Perceive(x_(t+1))`. Therefore the recurrent forward rows for a
nominal first half `x_s..x_(s+31)` do not have 32 decoder-visible losses until
`x_(s+32)` has already been coded. The old contract incorrectly treated byte
32 as both unavailable future truth and an adapted prediction.

The source exposes four additional blocking ownership facts. Native recurrent
`BackwardPass` keys its accumulator reset, complete dense-gradient sweep, Adam
step, and shadow refresh to epochs 127 and 0, so it cannot become a local-32
pass by changing one loop bound. Native `ForwardPass` writes the 128-event
history tape later consumed by the ordinary update, so rebuilding through that
entry point would silently replace already coded evidence. `HHistRow(epoch_)`
must retain the pre-replay hidden feature that actually predicted the closure
byte; recording rebuilt hidden state there would pair the ordinary pending
error with the wrong feature. Finally, a live mid-burst parameter update means
the later ordinary boundary sees histories from multiple parameter versions,
which v2 never interpreted.

The complete read-only finding is bound to q1 source closure
`e2aaf037...f628f`, program lock `edd1252e...f5787`, and release binary
`610edd6a...8808`. No v2 program, build, arm, archive, inverse, or scientific
result exists. Oracle v2 is now superseded before execution rather than
silently completed. Because persistence-attribution v2 defined F/J/S by exact
identity to that obsolete trajectory, it is also superseded before execution;
its exact `5*J_gain >= 4*F_gain` scientific question remains unmeasured.

Correction-only `cmix_obias_shadow_midpoint_oracle64_q0_v3` freezes the first
source-complete realization. Sixty-four-event segments align with native
128-event phases: snapshots occur at phases 0 or 64 after any ordinary
phase-zero update, and closure hooks occur at phases 32 or 96. At entry to
`Perceive(x_(s+32))`, byte 32 remains parent-coded, the exact 32-loss target
vector is `x_(s+1)..x_(s+32)`, and the first adapted probability is emitted by
the subsequent normal `Predict(x_(s+32))` for byte 33. This honestly leaves 31
affected bytes per complete segment.

The v3 gradient copies the native window into detached storage, reconstructs
each event-time output matrix from the burst base and all absolute-phase
pending rank-one factors, and runs a new local-32 backward path with temporal
adjoints zero outside the window. F/S commit one donor-order recurrent Adam
step followed by one output SGD step and refresh the exact fp16 shadows; K
performs the same update arithmetic on detached copies. Replay restores only
the segment-start hidden/cell state and uses a new state-only forward primitive
that cannot write native tape, epochs, loss, optimizer, mixer, SSE, context, or
coder state. The ordinary pending output feature for the already coded closure
byte is explicitly preserved from before replay.

The later native 128-event update keeps its source call site and cadence. v3
defines it transparently as the existing current-boundary approximation over
mixed-version history; it does not claim an unchanged or exact
historical-weight graph. The P/K/F/S Mechanism IR and current structured
experiment are frozen, and the adaptive proposal is `dormant_dependency` on a
positive independently verified q1 policy-v4 qualification. The first gate is
250KB exactness and strict F-over-P/F-over-S ordering; 1MB requires `4,080`
bytes, and 10MB requires `40,793` bytes plus positive original-coordinate
thirds. No source candidate, compile, execution, archive gain, compression
credit, or score credit exists. Router v3 permits a corrected persistence
attribution identity only after a valid positive 10MB v3 oracle.

### Live qm8 residency attribution and corrected bounded-to-full routing

A read-only live snapshot at `2026-08-24T03:14:27Z`, with the encode progress
log at `9.07%`, resolves the main q1 residency ambiguity without modifying the
running process. The guard still reported no hard-cap, OOM, or OOM-kill event;
its retained peaks were `8,534,408 KiB` process-tree RSS,
`8,518,220 KiB` CMIX `VmHWM`, and `9,002,086,400` cgroup bytes. The snapshot
itself is diagnostic and non-terminal: completion, inverse, cleanup, and the
soft-high verifier remain required.

The 26 file-backed FXCM mappings can be identified exactly from constructor
order and allocation geometry. Ordinal 0 is the match-position hash;
ordinals 1--3 are the three at-least-64-MiB `DirectStateMap::CxtState`
arrays; ordinals 4--7 are the four at-least-64-MiB mixer weight arrays; and
ordinals 8--25 are the eighteen at-least-64-MiB `ContextMap3` bucket arrays.
At the snapshot their aggregate `smaps` values were:

| Semantic group | Mappings | Size KiB | RSS KiB | Referenced KiB | Private-dirty KiB |
|---|---:|---:|---:|---:|---:|
| match-position hash | 1 | 65,540 | 65,536 | 65,536 | 36,288 |
| direct-state arrays | 3 | 589,824 | 589,824 | 589,824 | 107,068 |
| mixer weights | 4 | 419,856 | 238,436 | 170,604 | 27,148 |
| context-map buckets | 18 | 4,850,024 | 4,849,664 | 4,847,636 | 942,292 |
| total | 26 | 5,925,244 | 5,743,460 | 5,673,600 | 1,112,796 |

The separate `14,336,000 KiB` PPM virtual mapping held only `75,956 KiB`
RSS. CMIX anonymous RSS was about `2,456,736 KiB`. Thus the live pressure is
not a runaway PPM residency bug: it is predominantly the deliberately broad
FXCM context-table working set plus persistent anonymous model state. Only
the mixer group was materially nonresident. Targeting those already-reclaimed
pages has an observed ceiling of roughly `181,420 KiB`; it cannot by itself
produce a large memory reduction.

This evidence rejects connecting q1's dead blanket cadence as the default
successor. `PageOutAll()` would scan every mapping each modeled MiB and evict
tables whose pages are almost all being referenced, converting the same
semantic working set into refault and writeback churn. If qm8 terminalizes
with insufficient headroom, the single correction must instead target the
actual high-water mechanism: either one source-attributed allocation or an
exact bounded semantic-page arena that preserves table bytes while controlling
its resident cache. That is a prospective direction, not an authorized
candidate and not compression credit.

Planning revision 2 also closes a routing error. An opening-100M pass can no
longer blindly authorize an unchanged full-1G q1 run. It must be joined to
qm8's terminal class: exact and engineering-clean qm8 permits one independent
unchanged repeat; exact but headroom-failing qm8 permits one attributed
residency successor; infrastructure-incomplete qm8 permits only a retry after
the exact infrastructure cause is corrected. Bounded evidence may not erase
contrary full-corpus evidence.

### Mechanism IR managed-lane audit finds a two-sided ownership defect

Mechanism IR v3 had a pre-execution activation contradiction. All five v3
entry points required `exclusive_full1g.json` to be a regular JSON file with
`active=false`, but the canonical managed lease has no `active` field and
represents release by removing both the lease and `.lock` paths. Thus v3
rejected the live lane correctly but could never execute after a clean managed
release. No compiler arm or archive had run.

Candidate `gamma_mechanism_ir_v3_managed_lane_q0_v1` implemented the smallest
prospective correction: exact `O_EXCL|O_NOFOLLOW` ownership of the canonical
`.lock` namespace, retained directory/lock descriptors and random token,
inherited ownership witnesses for compiler-verifier children, all inherited
v3 causal controls, and a truthful wrapper-to-upstream compiler provenance
projection. Before execution, a harder competitor audit refuted the exact
wrapper. The bound `c3cedd46...` `ManagedExclusiveLease.acquire()` catches an
`O_EXCL` collision in a broad exception handler and unconditionally unlinks
the `.lock` path without proving that this call created it. A competing
full-1G acquisition can therefore delete the wrapper's foreign lock. This is a
source-level transaction bug, not an environment condition and not a
compression result.

The counterexample is frozen in
[`static rejection`](../../../operations/planning/gamma_mechanism_ir_v3_managed_lane_q0_v1.static-rejection.json).
The rejected implementation is preserved at candidate tree
`6d020fb1d3d2e04ec937c1117c3f56cabb98e11e4c91f491e04e912edc8211b7`;
it was not executed and receives zero infrastructure promotion, compression,
or score credit. This rejects only wrapper-only ownership against the current
manager, not Mechanism IR's P/K/D/M/R/S causal semantics.

Exactly one successor is authorized:
`gamma_managed_exclusive_lease_owned_cleanup_q0_v1`. Its prospectively frozen
transaction changes only acquisition/release ownership. An `O_EXCL` collision
closes local descriptors without touching the existing name; successful
creation retains directory and lock descriptors, device, inode, single-link
count, PID, and a random 256-bit token; terminal release removes the exact
owned lease while the lock still excludes competitors, then removes only the
reproved owned lock. Ambiguous post-publication failures remain occupied for
audit. Lease fields, transitions, descendant/signal rules, verifier semantics,
and public API remain unchanged.

The separate successor source is sealed at tree
`eb9c5f669cf05cbe1b361065ff4faefbe70fcea905c14e2483e6e97427ad1a44`.
It includes unexecuted normal/reacquire, foreign-lock, second-manager,
symlink, post-acquire appearance, inode, hardlink, token, partial-publication,
schema, and normalized replay controls. The current
`tools/managed_exclusive_lease.py` remains byte-identical because qm8 is live.
No control, canonical migration, Mechanism IR operation, or substantial gate
may run until qm8 terminalizes and releases both namespace paths. Static AST,
JSON, schema, source-set, candidate-budget, and adaptive-contract validation
pass; those checks are not execution evidence.

A later read-only qm8 snapshot at `16.80%` remains non-terminal. CMIX
`VmHWM` is `8,986,384 KiB`, current RSS was `8,366,460 KiB`, and cgroup peak
is `9,002,086,400` bytes. `memory.events` records `166,799` high-pressure
events but zero `max`, OOM, or OOM-kill events. Progress continued while the
process alternated runnable and disk-wait states. Combined with the previously
measured direct reclaim, file-cache refaults, and 26 mapping residency, this is
implementation-level working-set and page-reclaim pressure from file-backed
CMIX, not the old `/dev/shm` placement error recurring. Exact payload,
inverse, cleanup, runtime, and qualification remain unknown until terminal
receipts exist.

The ownership successor now also has a frozen post-qm8 execution closure,
without executing the candidate. The coordinator requires the exact qm8 Arm-A
terminal-receipt path, independently rejects any remaining qm8 or
exclusive-lane controller process, and requires both canonical namespace names
to be absent. A guarded worker then
loads the sealed candidate manager by exact path, acquires the canonical lane,
runs all 13 local controls in a child with a fixed environment, preserves a
complete scratch-tree manifest, freezes terminal lease evidence, and releases
the lane. The outer coordinator rederives the nine registered measurements and
promotion gates from the controls and guard-v3 receipt. A separately bound
verifier reopens the candidate revision and immutable blobs, every plan source,
the dynamic qm8 terminal receipt, the scratch tree, phase-marker sequence,
outer transition hash chain, exact result manifest, resource peaks, and
zero-credit authority boundary. A harder static audit found that revision 1's
`execution_authorized=false` declaration was not enforced by the coordinator
and was incorrectly required by the worker. The closure now fails closed: the
current revision-1 plan cannot launch, and every entry point requires a future
revision-2 activation with `execution_authorized=true`, the activated status,
and the actual qm8 terminal-receipt SHA-256. No result directory or control
receipt exists while qm8 owns the host.

At the latest read-only sample the encode had advanced to `17.40%`. Cgroup
current use was `8,999,227,392` bytes with the same `9,002,086,400`-byte peak;
`memory.events.high` had reached `180,490`, while `max`, OOM, and OOM-kill
remained zero. The split was about `2.55 GB` anonymous and `6.23 GB` file,
including about `6.01 GB` mapped file state. This strengthens the same
non-terminal attribution and does not qualify q1.

The terminal proof route is now symmetric for success and failure. The
existing soft-high verifier accepts only a terminally passing qm8 arm; the
older failure verifier was specific to qm7's exact hard-cap event. A new
prospective qm8 failure verifier can classify any schema-valid terminal Arm-A
failure through one ordered branch: hard-cap/OOM, RSS/decimal memory, other
resource limit, payload identity, decode/inverse, cleanup/lease, encode/stage,
or otherwise unclassified infrastructure. Exactly one correction route is
selected, and every branch retains zero promotion, parent-qualification,
archive, compression, and score authority.

Revision 1 is deliberately dormant. The verifier itself refuses to run until
a future revision at least 2 binds the actual failed terminal-receipt SHA-256,
sets the activated status and execution authority, and observes no remaining
qm8 process. The preflight occurs outside the receipt-writing exception path,
so an early invocation cannot poison the canonical output name with a
verification-failure file. The verifier reopens exact antecedent contracts,
package concatenation, stage and guard commands, result/scratch ownership,
soft-high state, outputs, managed-lease transitions, cleanup state, and its own
strict output schema. The plan validates against the campaign static-contract
schema and binds the Python runtime plus all source and schema files by byte
count and SHA-256. The new output schema is self-validated but is not yet added
to `research_contracts.py`, because qm8 imported that file before launch and
live source integrity takes precedence. No verifier execution or output
receipt exists. At the sealing snapshot encode progress was `18.02%`, cgroup
current use was `8,999,391,232` bytes, peak was `9,002,086,400` bytes, and
`memory.events.high` was `192,968`; hard-cap and OOM counters remained zero.

A symmetric audit then found the same dormant-output hazard in the older
passing-arm verifier. Its planning file named the campaign static-contract
schema without conforming to it and declared immediate execution authority;
its caught missing-source path could write `full-soft-high-verification.json`
before qm8 terminalized. That route is now fail-closed as well. The corrected
revision 1 is dormant and schema-valid, and preflight requires a future
revision at least 2 with the exact passing terminal-receipt hash, explicit
activation, Arm A `terminal_pass=true`, and process closure before the output
path can be opened. The verifier also reconstructs both guarded stage commands,
binds exact result and scratch ownership, rederives aggregate resource and
accounting fields, verifies managed-lease transition semantics, and validates
its output against the registered schema. No success-verification output or
Arm B authority exists while qm8 is live.

The post-audit read-only qm8 sample remains non-terminal at `18.57%` of the
encode. The codec, stage, nested guards, coordinator, and adaptive owner remain
live. Cgroup current use is `8,998,580,224` bytes and the peak remains
`9,002,086,400` bytes; `memory.events.high` has reached `205,484`, while
`max`, OOM, and OOM-kill remain zero. The codec is still alternating runnable
and disk-wait states under a one-CPU guard. This is continued pressure evidence
only: payload identity, inverse, cleanup, runtime, and q1 qualification remain
unknown until the terminal receipt and the matching independent verifier exist.

### qm8 terminal dispatch now has an independently closed authority boundary

The first receipt-to-verifier dispatcher draft was rejected before execution.
Its process scan excluded ancestors and could miss an orphan native `./cmix`;
branch and digest evidence came from separate receipt reads; its planning lock
did not reserve the canonical full-1G namespace; and it supplied neither a
durable intent nor a reconstructive predecessor after plan publication. A
second audit also found that the verifiers trusted too little of the dispatch
chain and wrote their canonical outputs before releasing the full-1G lock.

The corrected shared closure keeps one no-follow terminal-receipt descriptor
from schema validation through branch selection and verifier output. Verifiers
consume that parsed value rather than rereading the receipt pathname. It checks
every available recorded PID/start identity and scans all processes for the
candidate, result, scratch, and cgroup tokens, scratch cwd, and cgroup
membership. Only a shell-launcher ancestor whose sole match is its embedded
command is ignored. Native codec closure therefore does not depend on the
terminal lease recording an optional codec PID.

The dispatcher now holds both an exact planning lock and the canonical
full-1G acquisition lock. It checks both verifier outputs before locking,
after both locks, and before activation-receipt publication. One durable intent
binds the descriptor-witnessed receipt, both branch templates, both locks, and
the pre-publication closure. `RENAME_EXCHANGE` changes only the selected plan
and retains the exact displaced dormant inode at a deterministic recovery
path. Independent verification reverses `revision`, activation status,
execution authority, and terminal-receipt SHA-256 from the activated JSON and
requires the exact frozen dormant bytes and digest. The non-selected plan must
remain identical.

Canonical verifier authority is also ordered correctly. Each verifier prepares
and fsyncs its complete schema-valid receipt while holding the full-1G lock,
releases that lock, and only then publishes the canonical pathname with
`RENAME_NOREPLACE`. A release failure cannot leave a passing receipt that could
authorize Arm B. Both verifier paths require the exact frozen Python runtime
and argv. The dispatcher itself imports no subprocess or signal facility and
cannot execute a verifier or Arm B.

Static AST, schema-meta, plan-schema, serialization, recursive binding, branch
hash, and diff checks pass. The independent audit found no remaining route to
premature verification or Arm-B authority. The remaining non-authority gap at
that snapshot was an executable post-intent recovery transaction; it is closed
by the separately frozen recovery source below. Six directly validated
dispatch/recovery schemas are not yet in the shared `research_contracts.py`
registry because that module is part of the live qm8 closure.

No dispatcher, verifier, recovery path, test, Arm B, or new proof workload ran.
At the frozen review snapshot qm8 Arm A was still encoding at `25.64%`; peak
process-tree RSS was `8,998,152 KiB`, cgroup peak was `9,002,086,400` bytes,
and max, OOM, and OOM-kill events remained zero. No live process, candidate,
lease, cgroup, result tree, or scratch tree was modified or signaled. The
corrected audit and review remain zero-credit infrastructure evidence.

### qm8 terminal dispatch now has an inode-bound crash-recovery transaction

`cmix_filebacked_fxcm_full_qm8_terminal_dispatch_recover.py` is frozen for the
only two legitimate interrupted-dispatch outcomes. With no activation receipt,
it accepts only the exact dormant/absent, activated/dormant, or
dormant/activated selected/displaced plan state and rolls back to both frozen
dormant plans. With a valid activation receipt, it independently revalidates
the complete activation chain and leaves every authority-bearing artifact
unchanged. The action is rederived on every resume; a preparation cannot label
a committed activation as rollback.

The transaction ID is the SHA-256 of the immutable dispatch intent. Before any
rename it publishes a preparation, verifies that the original owner PID is
dead, and rescans recorded identities, all process argv/cwd/cgroup bindings,
cgroup occupants, and lease ownership under the surviving full-1G lock. It
rescans again immediately before completion. Rollback requires both exact
locks. Committed recovery additionally recognizes the dispatcher-ordered crash
state where the planning lock was already released but the exact full-1G lock
survives.

An uncommitted exchange is reversed with `RENAME_EXCHANGE`; any aborted
activated inode and the original intent move to transaction-addressed archive
paths. A durable completion is published while descriptors for every surviving
lock remain valid. Only then may the exact path/device/inode/link-count/payload
identity be unlinked, followed by a finalization after both lock paths are
absent. The preparation/completion split also permits resumption after a crash
inside recovery itself.

The [`recovery contract`](../../../operations/planning/cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_recovery_q0_v1.json),
three strict receipt schemas, source, and
[`static review`](../../../operations/planning/cmix_filebacked_fxcm_full_a_qm8_terminal_dispatch_recovery_review_q0_v1.json)
are hash-bound. AST, schema-meta, rollback/committed/partial-lock instance,
campaign-plan, artifact-binding, and diff checks pass. No recovery, dispatcher,
verifier, Arm B, or proof workload ran. At the review snapshot qm8 was still
encoding at `26.17%`; peak tree RSS remained `8,998,152 KiB`, cgroup peak
`9,002,086,400` bytes, and max/OOM/OOM-kill events remained zero. This closes
a liveness/provenance gap only and receives zero compression and score credit.

### q1 qualification authority is artifact-derived, not self-reported

An independent adversarial audit found a fatal consolidation weakness before
any q1 qualification receipt existed. The v1 verifier compared hashes and
booleans supplied inside one summary receipt, but did not reopen the full A/B,
phase-11, runtime, and dependency artifacts that those values purported to
summarize. In particular, `persistent_state_identity_pass` and runtime
eligibility could be asserted without a mechanically bound phase-11 or
Geekbench receipt. Downstream dormant tools treated `verified=true` plus
`qualified=true` as sufficient even though v1 declared no promotion authority.

The v1 consolidator and both v1 receipt schemas are now fail-closed: they can
only represent `qualified=false`, and the planning policy is superseded. The
replacement v2 input is only a router
to nine immutable artifacts: A receipt/verification, B receipt/verification,
full identity receipt/verification, runtime receipt/verification, and complete
dependency closure. It contains no qualification decision fields. The v2
verifier reopens those files, checks each router reference's declared byte
count and SHA-256 without symlink or hard-link aliases, validates schemas, and
rederives A/B package, payload, archive, inverse, resource, package-accounting,
and license conclusions. It reruns the A/B, phase-11, and runtime verifiers and
requires their recomputed outputs to equal the supplied verification receipts
exactly. It requires at most `9,000,000 KiB` A/B process-tree
RSS, strictly less than `10,000,000,000` cgroup bytes, and exact package
identity across the diagnostic, runtime, and counted dependency artifacts.

Runtime now has a separate proof shape. Its verifier parses exactly one
single-core score from retained raw output identifying Geekbench 5, requires
the compression and decompression guard commands to name the exact packaged
compressor/head/archive, recomputes each wall limit as `252000000 / score`, and
requires complete guard-v3 memory, disk, affinity, cgroup, phase, and elapsed
measurements. Diagnostic qm8 timing cannot satisfy this contract.

Phase 11 now states its narrower legitimate claim. It can prove continuous
byte-zero post-head integer-probability identity and exact coder checkpoints.
For q1-mutated persistent storage it freezes state digests at modeled-stream
indices `0`, `16,777,216`, `33,554,432`, `50,331,648`, `100,000,000`,
`500,000,000`, and the dynamically observed terminal modeled byte. These are
checkpoint identity, not continuously observed state-trajectory identity. The
raw corpus remains exactly `1,000,000,000` bytes but is a different coordinate;
retained full preprocessing currently yields `934,220,701` modeled bytes. The
independent verifier also requires retained
opening/distant 10M calibration equality, observer-off/on payload identity,
a differing pre-head negative control, a detected single-byte state mutation,
and rejected checkpoint omission/reordering controls.

SAFE-FORK memory admission and the frozen WIKI-SCHEMA-VM runner now accept only
a positive v2 verification with
`claim_authority=memory_safe_external_parent_only` and
`promotion_authority=true`. No v2 router, phase-11 arm, runtime receipt, or
qualification verification has been executed. This closure changes no archive
measurement and grants zero Gamma compression or score credit.

### Source-bound runtime producer and corpus-independent decode closure

A further pre-execution audit found that the dormant runtime design still did
not implement the proof it described. It had receipt schemas and an independent
verifier, but no producer, no exact executable plan, no managed-lease binding,
and no transitive source closure. More importantly, the generic full-stage
wrapper accepted the canonical enwik9 path in both modes. Its decode subprocess
ran only the self-extracting archive, but the timed wrapper itself first read
and hashed the original corpus. That is conservative for elapsed time but is
not a clean proof that decompression receives only the archive.

Runtime contract revision 2 closes those gaps before any execution. The
dedicated coordinator requires two independently verified, byte-identical q1
full roundtrips; an exact Arm-A package; one retained raw Geekbench 5 report;
the current host fingerprint; absent result, scratch, cgroup, and lease paths;
and the plan-bound working directory and command vector. It acquires the
managed exclusive full-1G lease, runs compression and decompression under the
v3 process-tree/cgroup/disk/affinity guard, and derives each phase limit as
`252000000 / single_core_score`. Compression must reproduce the A/B payload
and self-extracting archive before decode can begin.

The new runtime stage has an asymmetric information contract. Encode receives
the canonical corpus, packaged compressor, and head. Decode receives only the
newly generated archive and runs exactly `./archive9`; no original-corpus path
appears in its stage argv or codec argv. The restored output is then checked
against the fixed `1,000,000,000`-byte identity and canonical SHA-256. Hashing,
copying, wrapper startup, codec execution, output validation, and receipt
creation all remain inside the guarded elapsed interval, making the runtime
measurement conservative without giving the decoder forbidden information.

The independent verifier now reconstructs every stage and guard argv, the
coordinator argv, and their NUL-delimited hashes from the sealed plan. It
reopens both full arms and their verifications, rederives A/B/package/output
identity, reparses the Geekbench report, re-fingerprints the host, validates
the managed-lease transition hash chain and cleanup, and rejects any corpus
path in the decode command. The producer records pre-run source bindings and
terminally rejects source, plan, antecedent, package, population, or report
drift. Success removes scratch and releases the lease; failure preserves
scratch and emits a false receipt when execution has begun.

The exact runtime execution surface is a 145-member Python/research-schema
closure rooted at the coordinator, independent verifier, corpus-independent
stage, and v3 resource guard. The opening-100M and phase-11 closures, now 150
and 148 members respectively, were mechanically resealed because the shared
contract registry reaches the revised runtime schemas. Qualification policy v4
supersedes v3 for future authority and binds this producer, stage, plan,
schemas, verifier, lease semantics, and source closure. No Geekbench run,
runtime stage, full q1 arm, qualification receipt,
compression improvement, authorship credit, or score credit is created by this
static closure.

### Phase-11 modeled-coordinate repair and executable observer closure

A pre-execution audit found that the old full-identity schemas could never
correctly describe the intended run. They required the terminal arithmetic
checkpoint to be coded byte `1,000,000,000`, but the observer counts bytes only
after CMIX preprocessing. Retained full q1 scratch proves the coordinates
differ: the canonical raw corpus is `1,000,000,000` bytes and `.ready4cmix` is
`934,220,701` bytes. Opening 10M calibration is `5,766,051` modeled bytes.
This was a contract error, not predictor evidence.

The repaired observer binary now carries fixed modeled checkpoints at
`16,777,216`, `33,554,432`, `50,331,648`, `100,000,000`, and `500,000,000`.
The last two are enabled only by
`GAMMA_FULL_IDENTITY_EXTENDED_CHECKPOINTS=1`. Calibration and opening-100M
omit it, so their geometry remains start, the first three fixed points, and
terminal regardless of transformed length. Full arms set it and produce seven
records: start, five fixed points, and a terminal point required to equal the
bound transformed-stream artifact. This is the same calibrated binary, so no
second observer build or compiler-equivalence assumption is needed.

The opening-100M harness now has its own exact transitive Python
and research-schema closure rooted at its coordinator, identity arm,
independent verifier, release stage, observer build, calibration runner, and
calibration verifier. This is deliberately separate from the retained q1
`source_closure`, which binds the candidate implementation rather than the
orchestration code. The observer build and calibration each validate and record
the closure before creating their output roots; calibration requires the build
to carry the same closure. The coordinator rejects a path/hash, stale-stage, or
closure mismatch before creating its result root, the joint receipt records the
harness closure as an antecedent, and both independent verifiers rederive the
same ordered closure.

The full arm runner, sequential parent/q1 coordinator, strict plan schema, arm
and joint schemas, and independent verifier are now source-complete and
content-addressed. Each arm is single-CPU, owns disjoint result, scratch, and
backing roots, requires descent from the coordinator's exact owned full-1G
lease, retains its transformed stream and raw observer manifests, and is
bounded by an `11,500,000 KiB` diagnostic
guard. That higher guard is deliberately non-authoritative: the external parent
is already known to violate prize memory, and hashing semantic ranges faults
pages. qm8 A/B remain the only resource authority.

The independent verifier does not trust arm summaries. It reparses every
probability, coder, and 26-range state record; reconstructs ordered aggregate
digests; reopens the observer build and calibration; reruns the opening-100M
and full A/B verifiers; and independently rejects omitted, duplicated,
reordered, wrong-count, and wrong-terminal checkpoint controls. Full execution
remains disabled until qm8 A, an independent B, observer calibration, and the
opening-100M gate all terminalize as passes.

The prospective phase-11 Python execution surface is also frozen as an exact
transitive closure rooted at the coordinator, arm runner, and
independent verifier. It includes every recursively imported project-local
Python helper and, because the contract registry is reachable, every research
contract schema the registry can resolve. Both execution and independent
verification recompute the ordered path/digest rows. Any omitted, added,
reordered, or hash-divergent row rejects the evidence before identity authority
is interpreted; direct top-level script hashes alone are no longer accepted as
complete implementation provenance.

Qualification policy v2 is preserved byte-for-byte because the dormant
WIKI-LOOM proposal already hash-binds it. New policy v3 supersedes v2 only for
future qualification authority and binds the corrected seven-checkpoint plan
and implementation. None of these static repairs is a run, archive saving,
Gamma authorship credit, or score credit.

### Phase-11 full identity now owns its serialized lane

A harder audit rejected phase-11 revision 5 before execution. The coordinator
and each full arm called only `require_released_lease()`: all three observed an
absent path, but none acquired it. A competing full-1G workload could claim the
lane after any check, so sequential parent/q1 probability and state equality
would not have been produced under an exclusive execution contract. The plan
also required `execution_authorized=false`, making dormancy an execution
precondition instead of a barrier. This was an algorithm-harness ownership
error, not a host environment failure and not compression evidence.

Revision 6 replaces that path with a source-bound owned transaction. It is
still dormant and the coordinator refuses it: only a future revision at least
7 with `execution_authorized=true`, the activated status, and an exact passing
verification for `gamma_managed_exclusive_lease_owned_cleanup_q0_v1` can
execute. The activated coordinator atomically acquires the canonical full-1G
namespace once, retains the lease across both arms, heartbeats while each child
runs, and releases only after both terminate. Each arm now requires the exact
lease ID, owner PID/start tick, coordinator result/scratch roots, a live owner,
an owned lock path, and its own process descent from that owner. Both arm
receipts freeze the same witness.

Terminal authority is independently rederived. The joint receipt binds the
managed-lease activation verification, terminal lease evidence, and transition
chain. The independent verifier reruns the generic transition verifier, checks
the coordinator source and command bindings, compares both child witnesses,
requires the evidence and transition files inside the result root, and rejects
residual canonical lease, lock, or scratch paths. `exclusive_lane_pass` is now
a required conjunct of full identity.

The contract changes rebound the opening-100M, full-identity, and runtime
Python/schema closures to `154`, `153`, and `149` members. Qualification policy
v5 supersedes v4, explicitly revokes v4 future authority, and marks every
downstream candidate still binding v4 as stale until it receives a separately
identified activation successor. No manager control, parent arm, q1 arm,
verifier, codec, or proof experiment ran; qm8 still owns the host lane. All
Gamma compression and score credit remain zero.

### q1 qualification revocation is now enforced by the verifier

A follow-on call-graph audit found that policy v5's revocation was descriptive
but not executable. `cmix_memory_safe_parent_qualification_verify_v2.py`
accepted only the evidence router, lease namespace, and output path. It neither
accepted nor emitted a policy binding. The dormant FOSSIL-MATCH and WIKI-PDA
v2 runners invoked that exact verifier independently while separately
requiring policy v4. Consequently, a future complete evidence router could
have produced `qualified=true` through the v2 executable and then satisfied a
v4-bound successor even though v5 declared that route stale. No such router or
positive qualification receipt exists; this was a prospective authority bug,
not fabricated evidence and not a codec failure.

The v2 verifier now remains a complete artifact reopener but always appends
the exact failure `qualification authority revoked: v2 does not bind the
superseding qualification policy or its exact activated phase-11 plan`. It can
emit only `qualified=false`, `claim_authority=none`, and
`promotion_authority=false`. Its source SHA-256 is
`63d98e7b...d2fa8`; every known v4-bound runner freezes the prior
`c2b5b298...5139b` digest and therefore fails its own source-binding check
before execution.

The registered v2 verification schema is retired at the representation layer
as well. It now requires `qualified=false`, at least one qualification failure,
`claim_authority=none`, and `promotion_authority=false`; its SHA-256 is
`a935e041...11490`. Thus a handwritten or legacy positive v2 object cannot
pass current schema validation even in a consumer that does not rerun the
verifier. Known v4 consumers bind the older `3bcf4748...8a74d` schema digest,
so they also fail their frozen schema-closure check.

Policy v6 freezes the replacement authority shape without activating it. A v3
router binds exactly one v2 evidence router and one future active policy. The
v3 verifier reopens every v2 evidence predicate, requires the sole remaining
v2 failure to be the explicit revocation above, and then separately requires
that an active policy v7 or later bind the exact evidence router, the activated
revision-at-least-7 phase-11 plan embedded in the full-identity receipt, both
v3 schemas, both verifier generations, the canonical absent lease namespace,
and a recomputed transitive Python/schema closure. The future active-policy
schema also requires explicit revocation of every v1-v6 authority path.
The v3 CLI rejects an occupied lease namespace before verification and creates
the canonical output only for a fully qualified result, so an early or false
invocation cannot consume the authority receipt path.

The rebound closures contain `156` members for opening-100M, `155` for
phase 11, `151` for runtime, and `154` for the v3 qualification authority.
Static AST, JSON Schema, plan-schema, ordered closure, objective-hash, policy
hash-graph, and stale-runner hash checks pass. No test suite, verifier, codec,
or proof experiment ran. Qm8 remains live and untouched; q1 full-1G payload,
inverse, cleanup, runtime, and qualification remain unknown. This change has
zero Gamma compression, authorship, archive, or score credit.

The v3 schemas are intentionally direct-validator contracts rather than new
entries in the global `research_contracts.py` registry. A trial registration
changed that shared source digest and made unrelated sealed NNCP experiments
appear invalid. The registration was removed before any run; the global
registry is restored byte-for-byte to SHA-256 `744d3cc2...fa5b`, while the v3
verifier and its 154-member closure still bind and validate both v3 schemas
directly. This preserves unrelated historical evidence instead of forcing a
campaign-wide migration for a dormant authority format.

The same audit reached the adaptive scheduler. Before correction,
`next-experiment` labeled the already-retried qm7 proposal, the dormant owned
lease manager, the statically rejected Mechanism-IR wrapper, WIKI-PDA v2,
WIKI-SCHEMA-VM v1, and FOSSIL-MATCH v3 as eligible at ranks `2`, `4`, `5`,
`6`, `7`, and `8`. Their executable entry points would still have failed, but
the scheduler could select them and waste the serialized lane. Their canonical
proposal records now encode the evidence already established: qm7 is
superseded by live qm8; the wrapper is superseded by its static rejection; the
owned-cleanup manager is dormant until qm8 terminalizes and releases the
namespace; and all three q1 mechanisms are superseded pending new candidate
identities bound to a positive v3 qualification.

A fresh rank derivation marks all six rows `eligible=false` at ranks `8`, `9`,
`10`, `13`, `14`, and `15`; the selected unrelated proposal remains
`delta_midas_named_midpoint_gradient_65536_q0_v1`. This is scheduling
quarantine, not scientific retirement of the WIKI-PDA, schema-VM, or FOSSIL
mechanisms. No candidate, control, archive, or proof run occurred.

### SAFE-MIX static closure audit

`gamma_safe_mix_v1` remains unexecuted and zero-credit. Its Q63 native
implementation, arbitrary-precision reference, transactional controls, build
capture, and five-population oracle suite are materialized, but the planning
document was not actually valid under the generic schema named in its
`$schema` field. The generic schema rejected its extra `role` and
`theory_sources` fields and also required an absent dependency list. The
pending program lock separately omitted the integer-reference receipt schema
and the final SAFE-MIX receipt schema, so a future lock could have appeared
complete while leaving two authority-bearing shapes outside its closure.

Planning revision 2 closes those static gaps with the dedicated
`gamma-safe-mix-plan.schema.json`, explicit parent/treatment/lock
dependencies, and `execution_authorized=false`. The pending lock now includes
the plan, its schema, the arbitrary-precision receipt schema, and the final
receipt schema. The interface requires dedicated-plan validation before any
execution.

The non-circular program lock is now materialized. It binds all `31` declared
source, contract, build, control, plan, and receipt-schema files. The lock
SHA-256 is `0234709a...6f41c`; an independently executed verifier rehashed the
same ordered manifest to `88fcb5e6...a9895`, bound the exact Python executable,
and emitted terminal-pass verification `8ff09542...3ad65`. Direct schema
validation and a second manifest/hash reconstruction also pass. See the
[`program lock`](../../../programs/gamma_safe_mix_v1/program-lock.json) and
[`verification`](../../../results/gamma_safe_mix_v1/01_program_lock/program-lock-verification.json).
The locked plan deliberately remains `execution_authorized=false`, so this
proves source closure only. No compiler build, transactional control, integer
oracle population, finite coder, or mixture archive was run, and all
compression and score credit remain zero.

The proof boundary is unchanged but now explicit. The ideal two-expert
Bayesian inequality supplies at most a one-bit ideal log-loss penalty. It does
not prove a bound for Q63 posterior rounding, probability-count rounding, the
finite CMIX range state, archive termination, package bytes, or runtime. Native
versus arbitrary-precision identity can prove only that the frozen integer law
was implemented; fresh P/K/D/M arithmetic archives remain the sole compression
authority.

A subsequent activation audit found that the source closure is not yet a safe
execution closure. All four proof entry points that inspect the exclusive lane
still require an obsolete `active=true` field before treating a lease as live.
The canonical managed-lease schema has no `active` property, and the current
schema-valid qm8 lease therefore passes those functions as apparently absent
even while its owner PID and descendants are live. Separately, the frozen build
contract requires `clang++` plus `ld.lld`, neither of which exists on the
selected host. These are an execution-control contract-drift error and an
environment dependency absence, respectively; neither is evidence against the
Q63 mixture law.

The exact v1 files remain immutable and their program-lock verification remains
valid. Direct v1 execution is now quarantined. The only authorized mutation is
a separately identified `gamma_safe_mix_v2` proof envelope that preserves the
v1 arithmetic and populations, requires receipt-bound activation, rejects any
extant lease or acquisition-lock path under no-follow inspection, proves qm8
process closure, and binds a compiler/linker pair that actually exists. No
dependency installation, compiler substitution, proof execution, archive, or
score claim was authorized. See the
[`activation audit`](../../../operations/planning/gamma_safe_mix_v1_activation_audit_q0_v1.json).

`gamma_safe_mix_v2` now materializes that correction as a sealed, still-dormant
proof envelope. Candidate tree `f316e4a9...afe9d` contains the revisioned
activation plan, no-follow source and namespace validation, an exact-token
atomic acquisition lock, synthetic collision/replacement/token/hardlink and
process controls, guarded dispatch to the immutable v1 phases, receipt
schemas, and an independent verifier that reopens the terminal, source,
toolchain, child, guard, and managed-lease migration evidence. The plan binds
all `13` authority-bearing source artifacts, including the verifier and its
schema. Static AST, Draft 2020-12 schema, dormant-plan, proposal/experiment,
source-binding, and candidate-file closure checks pass. Counted candidate
source is `65,236` bytes under the frozen `65,536`-byte ceiling.

This is source-complete infrastructure, not executed SAFE-MIX evidence. Plan
revision 1 has `execution_authorized=false`, null activation dependencies, and
no phases. Activation still requires qm8 to terminalize and receive a matching
independent classification, the owned-cleanup lease candidate to pass and
migrate exactly into the canonical manager, and content-addressed `clang++`
and `ld.lld` executables to exist. No v2 control, build, oracle, finite coder,
archive, or inverse has run; Gamma compression and score credit remain zero.

A deeper off-PATH search supersedes only the earlier tool-availability
observation. It found a single-link regular Clang 17 driver at
`/home/x/enwiki9-nonproof/cmix-obias-donor/cmix-obias/tools/llvm17-local/bin/clang-17`
and a single-link regular AMD LLD 23 driver inside the retained ROCm SDK. Under
the exact v2 scrubbed environment, both `--version` probes return zero and
contain the required `clang` and `lld` family markers. Their SHA-256 values are
`d8e99328...a414` and `da235ec5...74b2`. This removes the shallow
"no suitable binary exists" conclusion; it does not prove that the mixed
Clang/LLD pair accepts the frozen build, produces byte-identical independent
builds, or passes any SAFE-MIX population. Those remain guarded activation
phases after qm8 and managed-lease closure. See the zero-authority
[`toolchain availability audit`](../../../operations/planning/gamma_safe_mix_v2_toolchain_availability_q0_v1.json).
