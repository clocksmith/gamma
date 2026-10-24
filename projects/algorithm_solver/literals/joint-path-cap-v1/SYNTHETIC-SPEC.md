# Item 60 supplied-input complexity protocol

2026-10-24. Draft for root review. This document authorizes no pin generation,
measurement, private access or corpus run. The new harness and focused tests
leave the accepted 50/53/57 files unchanged. Root separately approves public
pins and a single bounded measurement after code/spec review.

## Fixed inputs and historical authority

Use the same two public invented fixtures, in their original order:
`paired_prefix_75k` (300 sources, 250 characters each, seed 50065), then
`repeated_one_owner_12k` (12 sources, 1000 characters each, seed 50112).
Reuse item 50's exact generator, all 96 alphabet entries, bans, complete shared
pool constructor, sorted pool, original integer q generator, D=1000000 and
B=256. The unchanged input-spec SHA256 is
`a7d7843c947ccf0d8c691086614379cd5ddaa5f918bc50602e7947847f446f25`.
There is no adaptive fixture resizing, q optimization, source execution,
qualification, witness search or validation/protected input.

The builder uses public invented strings/metadata only. It verifies accepted
57 result/spec/supervisor identities, strict integer zero exit, both complete
receipts, finite bounded times, all independent comparison flags and inherited
code/runtime hashes. It adds the explicit eleven new measurement dependencies:
DRAFT, DRAFT-NEXT, proof, proof tests, caps, caps tests, independent checker,
checker tests, harness, harness tests and this spec. Future README/REVIEW or
corpus wrappers are excluded. It never constructs the pool or q or invokes a
kernel. Building a spec is not measurement authorization.

## Whole-worker checks and retained evidence

The same absolute deadline covers research imports, public preflight, all 22
supplied-input oracle tests (6 proof, 8 production, 8 checker), construction of
both fixtures, pool/q generation, both kernels, comparison, serialization,
normal process cleanup and final publication. Oracle tests run before fixture
phases and have a separately reported time; they are not outside the whole
budget. Historical total timings have different work/boundaries: no time ratio,
speedup or corpus ETA is registered.

First reconcile realized source/ban metadata, pool count/bytes/hash, original
q/occurrence hashes and generator transition counts against accepted 57. The
production kernel reconstructs the full unchanged 57 baseline and a separate
unchanged 53 potential context; this duplicated work is charged. The checker
reconstructs its full unchanged independent 57 baseline, then fresh original
AC occurrences, suffix potentials, local shared weights and bans. Shared
structural index dependencies remain explicit, not independent evidence.

Compare every common 60 scientific field exactly, including local shared top
entry identities/weights, counts/prefixes, all-arc caps, each split baseline,
joint/prior57/min charge, owner marginal allocation choices, all 257 rows and
raw/integer deltas. Compare every common digest. The checker calculates its
all-arc schedule backward and independently verifies every production forward
recurrence. It also verifies every inherited 57 forward recurrence. Compare
the complete 57 scientific fields and complete paired 53 scientific fields
between kernels, without equating directional schedules or work counters.

Reconcile unchanged 57 against its accepted public receipt: all rows50/53/57,
owner caps/counts, deltas, geometry, L/D, old charge/numerator/count/order,
class counts and every production/independent digest. Those digests bind the
historical owner tops, prefixes, capped prefixes, choices, shared prefix and
directional schedules that its public receipt did not store in full. The
immutable 57 comparison helper additionally reconciles its unchanged 50/53
baseline with accepted 53 saved fields. No missing historical full vector is
invented or claimed directly compared; the current two kernels compare full
values before matching their historical commitments.

Results retain all four curves, raw and integer gain per k, exact new local
shared tops/counts/prefixes, all-arc caps, per-split rows/choices, source/ban/
pool/q/occurrence identities, inherited/new scientific digests, work counters,
phase times and peak RSS. Large schedule vectors are committed and completely
replayed, rather than copied into results. A missing fixture, any mismatch or
partial recurrence cannot yield accepted results. A strict positive delta is
a stronger bound on invented supplied inputs, not proof of original-fit gain.

## Resource and failure envelope

One 180-second absolute supervisor deadline, core 6, one numerical thread and
8 GiB address space per process. The clock starts immediately after initial
`import time`; a bootstrap alarm precedes the remaining imports. The worker
receives that original absolute deadline, not a fresh phase allowance. Worker
and supervisor peaks are separate measurements. Per-fixture worker peaks are
cumulative, not incremental; there is no aggregate 8 GiB memory claim.

The supervisor creates one isolated worker process group and kills its remaining
descendants on success and failure. Normal cleanup is limited to the original
deadline and ten seconds from cleanup start. Failure uses one absolute bound,
at most first-failure+10 and original-deadline+10. A failure during normal cleanup
uses that cleanup's existing start; it cannot obtain another ten seconds.
Kill precedes potentially blocked marker removal, waits, log close or failure
publication. Every later operation checks remaining time. The external root
190-second guard is backup, not an extension of successful computation.

Fresh output is mandatory. The harness never withdraws or overwrites a prior
accepted directory rejected by the fresh-output check. For a directory created
by this attempt, failure withdraws complete markers before fallible failure
writes; an expired emergency budget cannot resume later I/O. Normal success
publishes prose then supervisor receipt then complete results last, only after
cleanup. Both complete receipts, absence of failure and exact reviewed spec
identity are required. Normal Python assertions are mandatory.

Focused development tests use tiny invented inputs and process stubs only:
full tiny worker/comparison, corrupt old/new fields, actual descendant cleanup,
timeout, blocked close/unlink/failure write, partial publication and prior-output
preservation. The two fixed measurement fixtures are not executed during this
development validation. After review only, root may authorize `--pin`, inspect
and push its exact public hashes, then separately authorize one `--run` with
a fresh output and reviewed spec SHA256. No retry is implied by failure.
