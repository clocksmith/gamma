# Research Register Archive 022

[Register index](../README.md) | [Current register](../../research_register.md)

## 2026-08-24 - midpoint v5 receives a canonical observability ABI

The observability-only successor reserved by the v4 audit now has a frozen
binary evidence contract and two direct-bound Draft 2020-12 receipt schemas.
This remains design infrastructure: no v5 source, parser, build, fixture, or
archive exists, and the P/K/F/S midpoint arithmetic has not changed.

`gamma-midpoint-observability-abi-v1` defines four independently parsed
streams for every encoder and decoder run: tensor layout, every final uint16
coder probability, rolling checkpoints, and midpoint updates. A 160-byte
header binds the exact candidate source tree, ABI artifact, raw population,
modeled stream, arm, replicate, and direction. A 56-byte footer binds body
bytes, record count, body SHA-256, and clean EOF. Checkpoints have an exact
332-byte representation at start, every 64 modeled events, terminal pre-flush,
and finalization. Updates have an exact 328-byte representation and preserve
all nine aggregate witnesses before detached buffers are cleared.

The six state partitions now have a reproducible current-state definition.
Every named initialized logical tensor is split into 4,096-byte leaves and
hashed through a domain-separated pair-or-lone SHA-256 tree. Dirty leaves and
only their ancestors are refreshed after semantic writes, avoiding v4's
infeasible repeated scan of all large FXCM ranges. Start builds read every
leaf in bounded chunks; terminal control independently rebuilds all six trees
from zero. A tree with N leaves stores fewer than 2N digest nodes, and the
future build must reject if its exact layout makes observer storage and
scratch exceed `268,435,456` bytes.

The update aggregate ABI fixes type tags, tensor metadata, logical lengths,
content digests, observation timing, canonical empty groups, and source-order
population for targets, capture, errors/adjoints, recurrent gradient plus
Adam result, output gradient plus result, pre-restore state, post-replay
state, complete detached values, and post-clear scratch. F and S retain the
same target vector; the record's frozen rotation field remains their only
association difference.

The parse schema requires exactly the dynamic, parameter, optimizer,
ordinary-tape, external-predictor, and midpoint partitions. The joint receipt
requires P, K, F-A, F-B, S-A, and S-B, with encoder/decode observations,
roundtrips, resources, package accounting, matched comparisons, and zero
Gamma credit. In-memory positive controls validate both schemas; duplicate
partition and wrong-repeat negatives are rejected.

The global schema registry was deliberately left byte-identical because qm8's
live terminal dispatcher binds it by SHA-256. V5 schemas remain directly bound
until qm8 terminal dispatch; any later registry revision must rebind all
active dependents. Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v5_observability_abi_q0_v1.json`
and its adjacent review artifact.

## 2026-08-24 - midpoint oracle v4 has an observability-only pre-archive gap

A source-level audit separated the midpoint algorithm from the proof harness
that would be required to interpret it. The frozen v4 overlay implements the
P/K/F/S arm selection, local-32 capture and backward path, detached K update,
F/S parameter commits, state-only replay, and canonical scratch clear. It does
not emit any successful-path trace, state digest, update count, or update
manifest. Its only output calls are fatal diagnostics, and each closure clears
the detached witnesses that the evidence contract requires the future archive
receipt to preserve.

The existing q1 full-identity observer is reusable but insufficient by itself.
It hashes every post-head integer probability, coder checkpoints, and the 26
large FXCM semantic allocations affected by q1. That is a valid, deliberately
allocation-specific completeness argument; it does not register the complete
Byte-LSTM dynamic, parameter, optimizer, ordinary-tape, external-predictor,
and midpoint partitions required at every 64-event checkpoint by the v4
evidence contract. Retained `KH_TRACE` likewise covers arithmetic probability
and residual evidence, not those partitions.

Literal reuse would also be computationally invalid. The q1 observer is
encoder-only, omits payload-prefix digests, and rereads then pages out all 26
large ranges at each state checkpoint. Applying that operation every 64 events
would read at least 6.8 TB on the 250KB gate alone. The existing midpoint
receipt schema is bound to the obsolete v2 candidate and cannot represent the
v4 six-partition or update-row evidence.

The contract also names hashes without freezing their canonical preimages.
It does not define field tags, traversal order, integer byte order,
floating-point object encoding, tensor geometry rows, checkpoint hook order,
or payload-prefix digest semantics. Consequently, adding ad hoc print calls
would still not yield independently comparable evidence.

The exact v4 overlay is therefore classified
`dormant_prearchive_observability_incomplete`, not scientifically rejected.
No build or run exists, and no compression conclusion follows. One
observability-only derived successor is reserved as
`cmix_obias_shadow_midpoint_oracle64_q0_v5`: it must preserve all P/K/F/S
arithmetic, populations, controls, thresholds, reset/join behavior, and
resource ceilings while adding fail-closed partition hashes, complete update
manifests, and receipt plumbing under a versioned binary observability ABI.
Because its source changes, it receives a new candidate identity rather than
editing v4 in place.

The correction must compose the calibrated q1 observer for every-bit
probability and coder primitives, not its repeated full-range pageout path.
V5 needs matched encoder/decoder hooks, payload-prefix hashes, complete LSTM
and midpoint visitors, and an incremental canonical mutation transcript for
large external state with bounded snapshots. It must pass a one-byte mutation
control for every new partition, freeze an independently parsed canonical
serialization and receipt schema, and prove
instrumented/uninstrumented probability and payload neutrality
before F/S results are interpretable. This audit is dormant while qm8 owns the
full-1G lane and while q1-v3 qualification receipts are absent. It grants no
source execution, archive, compression, package-score, or objective credit.
Evidence:
`operations/planning/cmix_obias_shadow_midpoint_oracle64_q0_v4_observability_audit_q0_v1.json`.

## 2026-08-24 - midpoint oracle v4 receives a dormant source overlay

The authority-only v4 midpoint proposal now has concrete, reviewable
implementation text without violating its q1 qualification dependency. The
new artifact is not a candidate tree: it is an inert integration patch plus
four detached declaration/implementation fragments bound to the exact sealed
q1 makefile and Byte-LSTM source hashes. A read-only verifier rehashes those
five parent files, the four authority artifacts, itself, and every overlay
file; checks that the patch touches only the makefile and four LSTM files; and
runs only `git apply --check --whitespace=error-all`. All static checks pass. No patch was
applied, no source tree was materialized, and no build or codec arm ran.

The implementation is not whole-compressor checkpointing. It preallocates
separate 32-row recurrent histories, output errors and adjoints, gate
transposes, dense/symbol/gamma/beta gradients, detached control rows, and
dynamic-state snapshots. At causal closure it reconstructs each historical
output matrix from the absolute native pending factors, runs local reverse
BPTT without calling the ordinary 128-row backward path, applies recurrent
Adam before output SGD, restores only Byte-LSTM hidden/cell state, and replays
with a history-free numerical clone of the recurrent forward pass. The
closure byte keeps the feature that actually predicted it. K performs the
same update arithmetic on detached copies and aborts unless replay reproduces
the closure dynamic state bit-for-bit; F commits aligned targets; S changes
only the frozen 16-position target rotation.

The review text totals `44,862` bytes. For the sealed `V<=256`, `C=256`,
one-layer geometry, the rounded buffer and vector payload formula is
`4,096,192` bytes and the design records a conservative `5,000,000`-byte
live-allocation bound, far
below the frozen `268,435,456`-byte incremental ceiling. Neither number is an
official package or memory measurement. Compilation, P/q1 identity, K/P
complete identity, F/S synchronization, resource compliance, inversion, and
all compression effects remain unproved. The overlay is dormant and receives
zero archive, compression, package-score, or objective credit.

A separate dormant evidence contract now prevents the future harness from
weakening that boundary. It freezes the P/K/F/F-repeat/S/S-repeat output tree,
64-event rolling hashes for coder and six state partitions, the exact
midpoint-update row contents, the closure-count formula, complete inverses and
resources, P/q1 and K/P cross-arm equality, F/S repeat equality, package cost,
and fail-closed decision equations. It grants no execution authority.

During this static work, qm8 remained the sole substantial process. Its Arm A
encode advanced to `23.80%`; the process tree is live, its guard reports no
cgroup `max`, `oom`, or `oom_kill` event, and no full-roundtrip receipt exists.
The process was not signaled, modified, or treated as q1 qualification.

## 2026-08-24 - midpoint oracle rebound to exact q1 v3 authority

The post-q1 CMIX midpoint route was not executable despite its corrected v3
causal semantics. `cmix_obias_shadow_midpoint_oracle64_q0_v3` still required
the policy-v4 q1 decision and v2 verification surface that policy v6 has
mechanically revoked. The dormant persistence-attribution v2 compounded that
defect by depending on both the revoked q1 route and the superseded midpoint
oracle v2. Neither proposal had candidate source or archive evidence, so this
is a prospective authority correction, not a reinterpretation of a run.

The new
`cmix_obias_shadow_midpoint_oracle64_q0_v4` proposal preserves the exact v3
scientific mechanism: `P/K/F/S`, 64-event segmentation, closure only after
decoded `x_(s+32)`, first adapted prediction `x_(s+33)`, detached local-32
backward arithmetic, native-tape-isolated state replay, persistent donor-order
updates in `F/S`, the 16-event target-rotation control, and the frozen 250KB,
1MB, and 10MB gates. It changes only qualification authority. V3 is now
superseded; persistence-attribution v2 is also superseded, with v3 reserved
only after a valid target-scale causal oracle-v4 pass.

The adaptive proposal activator now recognizes one new fail-closed dependency
kind, `terminal_parent_qualification_v3`. Activation requires both canonical
q1 v3 artifacts, the exact bound verification schema and verifier digests, a
revision-7-or-later active policy, all positive verification and evidence
checks, zero Gamma credit, and `memory_safe_external_parent_only` authority.
It rehashes the authority policy and activated full-identity plan, then calls
the exact v3 verifier again against the qualification router and absent
canonical lease namespace. The stored verification must equal that fresh
replay byte-for-byte as a JSON value; a narrative verdict cannot activate the
proposal.

Even after that dependency passes, activation authorizes only a new
content-addressed source materialization from the sealed q1 tree. The midpoint
implementation, Mechanism IR compilation, arm-difference manifest, synthetic
phase and negative controls, two clean builds, package closure, and guarded
finite-coder arms remain unproved and must be produced before scientific
execution. The v4 contract is dormant, unexecuted, and worth zero archive,
compression, package-score, or objective credit. Static schema, reference,
source-closure, and rank derivations pass; the ranker returns `selected: null`.
V4 names v3 as its direct proposal parent and is the exact successor in v3's
`superseded_by` field, so a future receipt-backed activation can escape the
inherited v3 block without reviving any other descendant.

The next source-only boundary is now frozen without crossing that activation
gate. `cmix_obias_shadow_midpoint_oracle64_q0_v4_materialize.py` names one
canonical output and accepts no caller-selected source or destination. Before
creating a lock or temporary tree it must reopen the actionable proposal,
require exactly the two canonical q1-v3 activation artifacts, reproduce the
activator's single verified requirement through the bound v3 verifier, require
the full-1G lease namespace absent, reserve its lock against a new run, and
revalidate the sealed 119-file q1 source and program lock. It then copies every
parent file, adds the four
reviewed midpoint files, proves the complete 123-file pre-patch closure,
applies the bound patch, and permits only five modified files, four additions,
zero removals, and 114 byte-identical parent files. The complete difference
and materialization receipts are bound to two new Draft 2020-12 schemas and
publish only through `renameat2(RENAME_NOREPLACE)` under an inode-owned sibling
lock.

The proposal may remain in `proposed` after activation or undergo the normal
single `claim` transition. The materializer normalizes only the exact
owner/state/claimed-at fields added by that transition before comparing the
original semantic digest; any other proposal mutation fails closed.

This materializer has not been invoked. Its AST, two schemas, and fourteen
planning bindings pass read-only checks, but the proposal is still dormant,
the q1-v3 qualification artifacts do not exist, the qm8 lease exists, and the
canonical output is absent. Therefore these artifacts prove only that a
fail-closed post-qualification source route is reviewable. No candidate tree,
build, fixture, codec arm, archive, scientific verdict, or Gamma byte credit
exists.

An independent adversarial audit correctly found that the legacy
`cmix_memory_safe_parent_qualification_verify.py` v1 surface trusts supplied
full-stream hashes and a supplied persistent-state boolean. That surface is
already revoked and is not the v4 dependency. The current v3 route reopens the
zero-authority v2 evidence verifier; v2 reruns the full-identity verifier over
the raw probability, coder, and state manifests and separately reruns the
Geekbench-bound runtime verifier. V3 then requires the exact activated
phase-11 plan and active policy. No authority rewrite is therefore warranted.
The remaining proof boundary stays explicit: probability identity covers every
modeled bit, persistent-state identity covers seven frozen checkpoints, and
runtime remains an unmet independent qualification artifact until measured.

At the authority-correction point, qm8 remained the sole substantial lane. Its
Arm A encode was live at `23.02%` with a `30,375,959`-byte progress payload;
the recorded maxima were `8,978,032 KiB` single-process RSS and
`8,998,152 KiB` process-tree RSS, and cgroup `max`, `oom`, and `oom_kill`
events remained zero.
No q1 full-corpus payload identity, inverse, terminal memory result, or parent
qualification exists yet, and no new proof experiment was launched.

During the later source-materializer review, the same untouched qm8 Arm A
encode advanced to `24.39%`. Its guard remained `running`; peak sampled tree
RSS was still `8,998,152 KiB`, peak cgroup memory was `9,002,086,400` bytes,
and cgroup `max`, `oom`, and `oom_kill` deltas were still zero. No encode-stage
or full-roundtrip receipt existed, so this observation changes no q1 authority.

## 2026-08-24 - Named-gradient lineage removed from the actionable scheduler

A read-only audit of the proposal selected after the q1 scheduler quarantine
found that `delta_midas_named_midpoint_gradient_65536_q0_v1` was not pending
science. Q0 and q1 ended in invalid implementation failures, q2 completed only
as a non-authoritative numeric diagnostic, and q3 then completed the exact
direct-F32 experiment with a valid terminal reflection. That reflection
refuted the prospectively frozen single-stable-deep-group hypothesis and
retired squared-gradient-energy localization on the production F population.

The proposal router had not projected that descendant result back onto the
four developed proposal records. Because absent `operational_status` defaults
to `actionable`, the ranker could select q0 even though its exact successor
lineage was already terminal. The records now encode the actual lifecycle:
q0 is superseded by q1, q1 by q2, q2 by q3, and q3 is retired with the exact
terminal-reflection digest. This is scheduling repair only. It changes no
candidate, source, experiment, receipt, archive, scientific conclusion, or
objective credit, and it authorizes no proof execution while qm8 is live.

The corrected rank then exposed the same metadata mismatch in
`gamma_safe_mix_v2`. Its interface, source contract, and revision-1 execution
plan all say `dormant_dependency`, `execution_authorized=false`, and require a
future activation revision binding qm8 terminal evidence, owned-lease
migration, process and namespace closure, and an exact toolchain. The developed
proposal omitted that operational state, so the ranker selected it as
actionable. The proposal now carries the exact dormant plan digest and blocker.
SAFE-MIX remains source-complete proof infrastructure with zero execution,
archive, inverse, compression, package-score, or objective authority.

The next rank exposed a different successor-routing defect. The unexecuted
bit-head DELTA-MIDAS v2 leaves CMIX's original memory policy intact, while the
already frozen v3 composes the identical `P/K/O/R/D/S` science with the sealed
PPM0 residency policy. V2 is now explicitly superseded by v3; v3 is dormant
until qm8 terminalizes and releases the proof lane. Neither has measured gain,
and the `4,013,707`-byte net figure is a forecast only.

The ranker previously propagated every non-actionable parent state into all
descendants, which also suppressed the exact child named by a parent's
`superseded_by` field. It now exempts only that explicitly designated direct
successor. Retired, dormant, or otherwise non-actionable successors remain
non-actionable themselves, and all other descendants still inherit the block.
This preserves lineage while allowing a future activated v3 to become
selectable without resurrecting v2. No proof process or candidate source was
changed.

The original `cmix_obias_ppm_always_purge_q0_v1` proposal is also not the
runnable resource gate. It binds the pre-disk experiment and declares a joint
output for which no matching adaptive job or result exists. The later frozen
`cmix_obias_ppm_disk_joint_q0_v3` contract instead binds separate clean and
PPM0 disk-backed runners, direct durable payload comparison, allocated-scratch
accounting, and a fail-closed joint evaluator. It has no proposal/candidate
materialization and no result. The original proposal is therefore superseded
by that correction identity rather than selected for execution. A future
materialization must remain dormant until qm8 releases the lane and must not
inherit any compression credit from this zero-savings infrastructure policy.

After these corrections, a fresh full proposal/reference derivation returns
`selected: null`. That is the intended fail-closed scheduler state while qm8
is the only live gate: no stale ancestor, retired oracle, dormant proof
envelope, or unmaterialized correction can be launched by ranking alone.
