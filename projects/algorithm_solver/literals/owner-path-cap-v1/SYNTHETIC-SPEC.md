# Item 57 supplied-input complexity protocol

2026-10-24. Draft harness only. No pins, measurement, private access or corpus
launch are authorized by this document. Root reviews the stable kernels,
checker and harness before separately authorizing public pin preparation and
one bounded invented measurement. Item 50/53 files remain unchanged.

## Inputs and authority

Reuse the exact two invented fixtures, in order, from item 50 and accepted item
53: paired_prefix_75k (300 sources of 250 characters, seed 50065), then
repeated_one_owner_12k (12 sources of 1000 characters, seed 50112). Reuse all 96
paid alphabet entries, original bans, complete shared pool constructor, sorted
pool order and integer q generation. D=1000000, B=256, every k=0,...,256. No q
optimization, source execution, validation, cases or qualification.

The builder creates only invented strings and metadata. It verifies accepted
item 53 spec/results/supervisor hashes, strict integer zero exit, completion,
source/ban identities and inherited code/runtime pins. It adds explicit item 57
proof, production, checker, test, harness and this protocol files. README and
future corpus execution/report files are not measurement dependencies. It never
constructs a pool, q or certificate, and never opens private files. Preparing a
spec is separate from executing it; no final spec is written before root approval.

## Exact checks in the worker

Run all 15 kernel/oracle tests (5 mathematical, 4 production and 6 independent)
before the fixture phases, under the same whole deadline. Fixture construction,
pool, q, both kernels, comparison and serialization are charged. Check exact
source/ban metadata, pool bytes/count/hash, old occurrence and q hashes, and q
construction transition counts against accepted item 53's public receipt.

Production shares unchanged item 53 reconstruction and paired proof, but builds
new per-owner tops, shared ownership thresholds and forward scheduling vectors.
The isolated checker reconstructs the paired proof with AC/end-order paths,
owner-run groups and every allowed group depth; it never uses production caps,
per-owner tops, q, or potentials to select or calculate its own results. Both
share item 33's Index and accepted structural/suffix/ban verifier. The checker
uses bounded sorted owner lists, fresh old-pool AC ownership, a separate fresh
banned-string matcher, backward interval scheduling and sorted marginals.

Require exact equality of all paired 50/53 scientific fields, every owner top
identity/count/prefix/capped prefix/cap, marginal choice, shared prefix and all
257 item 57 rows/deltas. Compare every common digest. Also match both historic
50/53 curves, base digests/reductions and geometry to item 53's accepted receipt.
The independent checker receives production's forward vectors only as claimed
outputs: it strictly checks keys, integer types, lengths and zero starts, then
recalculates **every forward recurrence** from its own reconstructed d and AC
ownership/bans. It compares each end value and the final backward cap. The
backward vector is independently calculated first; forward/backward vectors are
not expected to be equal. Both scheduling scans inspect every potential endpoint
and never truncate to top entries. Required position/endpoint counters and the
forward-vector commitment prove the complete claimed replay scope.

Public invented results retain source/ban/pool/q/occurrence commitments,
geometry, all three curves, per-k raw and integer gains, per-owner caps/counts,
paired and new top/potential/weight/schedule commitments, kernel work counters
and separately labeled phase times. They omit large top/schedule/source/q
vectors. Exact top agreement happens before sanitization. A failed comparison,
missing fixture or partial vector cannot produce accepted results.

## Budgets and cleanup

One 180-second whole supervisor deadline on core 6, one numerical thread and
8 GiB address space per process. Time begins immediately after the initial
`import time`, before research imports and preflight. The bootstrap alarm starts
before subsequent harness imports; the worker inherits the original absolute
deadline without refreshing it. This cap includes tests, all input/proof work,
serialization, successful process-group cleanup, log close and publication.
There is no separate phase allowance and no automatic retry or smaller fixture.
The isolated worker and supervisor peaks are reported separately; fixture peaks
are cumulative worker peaks, not incremental or summed memory.

Fresh output is mandatory. The supervisor owns one separate worker process
group and kills descendants on both success and failure. Normal cleanup is
inside the original deadline and limited to 10 seconds. Failure uses one
absolute emergency deadline at most first-failure+10 and original-deadline+10;
a normal-cleanup failure retains that cleanup's original start. Kill and marker
withdrawal precede waits/log close/failure writes. Each later operation checks
remaining time; hard deadlines stop subsequent I/O. Success is published only
after cleanup, prose and supervisor receipt first, complete results last. Both
complete receipts and reviewed spec identity are necessary for acceptance.
A root-owned external 190-second process guard is backup, not an extension of
the 180-second acceptance limit. Normal assertions are required, including -O
rejection. No failed receipt write can confer acceptance.

This is one invented complexity observation, not a corpus estimate, optimized
q result, feasible dictionary witness or M1 result. Historical timing boundaries
and work differ; no matched total-time ratio or speed claim is registered.
After review only, `synthetic.py --pin` writes public pins without pool/q work.
Root then reviews/pushes those pins and separately authorizes `--run --output
<fresh-directory> --spec-sha256 <reviewed>`. The internal --worker mode is solely
the bounded supervisor child. Corpus execution needs a separate freeze/review.
