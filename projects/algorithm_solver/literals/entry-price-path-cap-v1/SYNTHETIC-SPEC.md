# Item 63 supplied-input complexity protocol

2026-10-24. Draft for root and Claude review. This document authorizes no pin
generation, measurement, private access or corpus run. The harness leaves all
accepted ancestor files and item 63 kernels unchanged. After reviewing this
code and protocol, root must separately approve public pins and the single
bounded measurement; a successful development test is not that approval.

## Fixed inputs and historical authority

Use the same two public invented fixtures in their original order:
`paired_prefix_75k` (300 sources, 250 characters each, seed 50065), then
`repeated_one_owner_12k` (12 sources, 1000 characters each, seed 50112).
Reuse item 50's exact generator, all 96 alphabet entries, bans, complete shared
pool constructor, sorted pool, original integer q generator, D=1000000 and
B=256. The unchanged input-spec SHA256 is
`a7d7843c947ccf0d8c691086614379cd5ddaa5f918bc50602e7947847f446f25`.
There is no adaptive resizing, q optimization, source execution, qualification,
witness search, validation or protected input.

Every source uses exactly the fifteen prices
`[0] + [D * 2**r for r in range(14)]`, in that order. No price is selected,
added or dropped after inspecting the inputs or results. All allowed one-owner
occurrences, including zero-q occurrences, contribute to the entry denominator.
All residual schedules retain every allowed one-owner arc, including zero
residuals and low-ranked entries. This is the item 63 price refinement of 57;
it does not insert the joint or mandatory-owner constraints of 60/61/62.

The builder constructs public invented strings/metadata only, not their pool
or q, and invokes no kernel. It verifies accepted 57 spec/result/supervisor
identities, strict integer zero exit, both complete receipts, finite bounded
historical times, independent-comparison flags and inherited code/runtime
hashes. The historical 57 acceptance cap remains 180 seconds; the new proposed
cap below is 600. The explicit eleven new measurement dependencies are DRAFT,
DRAFT-NEXT, proof, proof tests, caps, caps tests, independent checker, checker
tests, harness, harness tests and this spec. Future records and corpus wrappers
are excluded. Building a spec is not measurement authorization.

## Charged checks and retained evidence

The same absolute deadline covers imports, public preflight, all **19** registered
supplied-input oracle tests (6 proof, 8 production, 5 checker), fixture
construction, pool/q generation, both kernels, all comparisons, serialization,
normal process cleanup and final publication. The harness verifies the actual
oracle count; tests run before measured fixture phases with a separate reported
time, but remain inside the whole budget. Historical total timings have different
work and boundaries: no time ratio, speedup or corpus ETA is registered.

Reconcile realized source/ban metadata, pool count/bytes/hash, original q and
occurrence hashes, and generator transition counts against accepted 57.
Production reconstructs the full unchanged 57 baseline and a separate 53
potential/index context. The checker reconstructs unchanged independent 57,
then fresh original AC occurrences, suffix potentials, support and bans, and
per-start numeric Z counts. Every duplicate context and all new work is charged;
the common structural index remains an explicitly shared dependency.

Pass the complete production 57 forward vectors and all fifteen new price
forward vectors to the checker, alongside expected count streams and caps.
Require both checked flags and exact production-vector commitments. The checker
constructs backward price schedules and verifies every supplied forward
recurrence, not only final maxima. The production lambda-zero vector must equal
its full 57 vector. For K=15, N total characters and A allowed one-owner arcs,
require exactly K*N checked new forward positions, K*A backward candidates,
K*A forward-audit candidates, K*A production forward-arc candidates and K*A
residual evaluations in each implementation. Require A count records and q
evaluations, K*N production skips and K times the distinct cached multiplicities
in quotient calculations. The kernels retain their additional structural and
support checks and counters.

Compare every common 63 field exactly: fixed prices, all per-start count hashes
and counts, all price caps, finite affine envelopes/priced prefixes, marginal
choices, shared prefixes, all 257 rows and raw/integer deltas. Compare all common
digests. Compare complete common 57 scientific fields and complete paired 53
scientific fields between kernels. Do not equate directional schedules or work
counters. New field/digest comparison normalizes integer dictionary keys and
tuples into their JSON representation before sorting, preserving scalar type
checks and rejecting key collisions. Actual JSON roundtrip is a development
regression, including inherited numeric-key maps.

Reconcile unchanged 57 against its accepted public receipt: all rows50/53/57,
owner caps/counts, deltas, geometry, L/D, original charge/numerator/occurrence
count/order, class counts and every production/independent digest. Historical
digests bind owner tops, prefixes, capped prefixes, marginal choices, shared
prefixes and directional schedules not retained in full in that public receipt.
The harness restates the unchanged 57 historical comparison with JSON-safe
normalization, including its original 50/53 saved-field checks; it does not
modify that helper. No missing historical full vector is invented. Both current
kernels compare full values before matching historical commitments.

Results retain all four curves (50/53/57/63), every raw and integer gain, price
family, per-start count commitments, price caps, affine/priced prefixes,
marginal choices, shared prefix, source/ban/pool/q/occurrence identities,
scientific and schedule digests, separate baseline/new work counters, phase
times and peak RSS. Large schedule vectors are completely checked and hashed,
not copied into the public result. These inputs are invented: exposing their
numeric tables does not authorize exposing owner tables in a later corpus run.
A missing fixture, mismatch or incomplete recurrence yields no accepted result.
A stronger invented bound is not evidence of original-fit gain.

## Resource and failure envelope

Adapt the accepted item 60 lifecycle: one **600-second** absolute supervisor
clock, core 6, one numerical thread and 8 GiB address space **per process**.
The clock starts immediately after initial `import time`; a bootstrap alarm
precedes the remaining imports. The worker inherits the original absolute
deadline, not a fresh phase allowance. Worker and supervisor peak RSS are
reported separately; per-fixture worker peaks are cumulative, not incremental.
There is no aggregate 8 GiB claim and no uncharged background worker.

The supervisor creates one isolated worker process group and kills remaining
descendants on success and failure. Normal cleanup uses the original deadline
and at most ten seconds from cleanup start. Failure gets one absolute bound,
at most first-failure+10 and original-deadline+10. Failure during normal cleanup
uses that cleanup's existing start, without a new ten seconds. Kill precedes
possibly blocked marker removal, wait, log close and failure publication. Each
later operation checks remaining time. A root external **610-second** guard is
backup only, not an extension of successful work.

Fresh output is mandatory. An existing accepted folder rejected by preflight
is preserved. For a folder created by this attempt, failure removes complete
markers before fallible failure writes; expired emergency handling cannot
continue later I/O. Success publishes prose, supervisor receipt, then complete
results last, after cleanup. Acceptance requires both complete receipts, no
failure, and the exact reviewed spec identity. Normal assertions are required.

Focused harness development tests use tiny invented strings and child-process
stubs only: complete worker/comparison, actual JSON transport, old/new field and
counter corruption, oracle inventory, actual descendant termination, timeout,
blocked close/unlink/failure writes, partial publication and existing-output
preservation. The two fixed large fixtures are not executed during development.
After code/spec review, root may authorize public pinning and inspect/push
exact hashes. Claude protocol review and separate root authorization precede
the single measured run. A failure
does not authorize a retry, budget extension, fixture change or corpus run.
