# Item52 proposed synthetic timing specification

2026-10-24. **No benchmark has run.** The synthetic harness is implemented for
final pinned-script review; root must review before measurement. No corpus inputs,
scientific loader/binder, real dictionary, item46 continuation or budget extension.

## Fixed comparison and supplied fixtures

Compare unchanged inherited41 `banned()` against this sequential persistent
client. There are no source, parser-result or trie caches. Both paths retain both
parser passes. Both invoke unchanged46 menu/apply for the engine portion; only
the test process's inherited41 `core.banned` binding is temporarily substituted.

Use four isolated comparison blocks in this fixed order:
`old-A, persistent-A, persistent-B, old-B`. A and B use identical fixtures and
request order. Each block has a fresh Python worker and, for the persistent
path, one fresh Node service. All blocks run sequentially on core4. Do not tune
fixture size, repeats, timeouts or ordering after seeing results.

Each block performs these exact operations:

1. Scalar requests i=0..31, in order. Define
   `name = ['a','b','c','d'][i % 4]`,
   `text = 'function solve(' + name + '){/*scalar' + str(i) + '*/return ' + name + '+' + name + '}'`.
   The input dictionary is the single insertion `(str(i), text)`.
2. Repeat the identical32 requests in the identical order. Neither implementation
   may cache them. Compare the ordered sequence of returned sorted ban sets.
3. Build an insertion-ordered engine input with keys `'10'`, then `'2'`:
   `'function solve(a){return a+a}'` and
   `'function solve(b){return b+b}'`, respectively. The vocabulary is reversed
   inherited41 `ALPHABET`, followed by `'aa'`, `'ab'`. Invoke unchanged46
   `engine.menu(texts,vocab)`, then unchanged `engine.apply(texts,vocab,menu)`
   with its original two-pass semantics and proposal cap153600. Keep all returned
   menus, traces, ledger events, variants, source bytes and scores for exact
   untimed comparison. Sources are invented and need no behavioral execution.
4. Close/reap the service if present; restore the monkeypatched module binding.

All scalar requests must succeed; a parser/transport failure fails that block
and the comparison. Do not substitute a smaller fixture or omit a failing block.
Failure equivalence is covered separately by the focused tests; this benchmark
does not time retries, malformed sources or cap-triggering requests.

Before measurement, compute and retain an input-spec digest and exact code/
runtime inventory hashes: this directory's implementation and benchmark code,
unchanged46 engine/common, inherited41 helpers and transitive parser/scorer
dependencies, Node executable, Acorn/eslint-scope packages, and the pinned Python
runtime. No code or input mutation follows the pinning step. A mismatch fails
before timed work. This file alone is not a binder or activation artifact.

## Clock, processes and resources

Use one external120-second hard deadline for the entire four-block measurement,
including fixture construction, imports, instrumentation, service startup, every
request, parsing, response handling, engine work, comparison and cleanup. No
per-block refresh or extension. Preserve partial receipts and fail the benchmark
if any block is missing. The outer guard kills its owned process group; the
service and legacy children inherit that group and core4 affinity. Normal cleanup
is inside120 seconds. Failure gets at most ten additional seconds for group kill,
reaping and incomplete-receipt publication, never more measurement. The supervisor
uses process-local Linux subreaping to reap orphaned descendants; it does not
change host configuration. Timed-out publication withdraws both success markers.
The clock is captured before the supervisor's other imports. Root's independent
external guard must allow130 seconds for the internal120-second acceptance cap
plus bounded failure cleanup, rather than sending a120-second TERM that bypasses
that cleanup. The external guard must also kill the owned descendant group if
the internal supervisor cannot finish its cleanup; it grants no accepted overrun.

Every process inherits8 GiB RLIMIT_AS; the new service also retains its256 MiB
V8 old-space ceiling. This is a narrower new service resource envelope, explicitly
part of the comparison. There is **no aggregate8 GiB cap claim**, no cgroup change
and no uncharged background service. Client request timeout remains ten seconds,
but is clamped to the remaining whole deadline. Request/response limits remain
4/16 MiB and the lexical stdout limit32 MiB. Stop on any failure; no rerun.

Use a monotonic wall clock. Report worker total and scalar/menu/apply/cleanup
subintervals, but treat end-to-end time including imports/startup/cleanup as the
primary comparison. Record service process-spawn time separately without
subtracting it; Node/module initialization after Popen returns is included in
the first scalar request, not mislabeled as fully captured by spawn time.
The old path includes every fresh helper startup and nested lexical child.
Do not compare a warm persistent service to old subprocess startup while hiding
the service's own startup. There are exactly two observed blocks per path;
report both individually and their sum, without a significance claim.

Measure each worker's own peak RSS and child-resource high-water receipts.
If sampling descendants, apply identical instrumentation to both paths: record
observed parent, service and legacy helper RSS, plus sampled concurrent sums.
Label sampling interval and missed/exited-process limitations. A sum of separate
peaks is not a measured simultaneous aggregate peak; a child `ru_maxrss` maximum
is not the sum across children. Report those quantities separately and disclose
that persistence changes which process holds parser memory. Instrumentation
costs remain inside the overall clock. Do not claim total RSS equals V8 old-space.

## Acceptance and interpretation

Remove only the engine result's top-level `seconds` field for untimed equality;
do not strip proposal counts, trace/ledger fields, failure state or source bytes.
Each pair must have identical scalar results, menu, selected sources, complete
trace and ledger, and both pair outcomes must agree. All four blocks must finish
within the single cap with every child reaped. Any mismatch/failure gives no
accepted speed ratio. Report completed work and the failure without adjustment.

A successful synthetic comparison measures process persistence on these exact
invented requests. It does not predict item46 throughput, establish scientific
completion under1800 seconds, authorize a retry or qualify any spelling result.
No engineering or corpus-runtime timeline is proposed.

## Implemented harness and review gate

`fixtures.py` constructs only the exact invented inputs above. `pin_timing.py`
verifies inherited public pins and writes `timing-pins.json` without invoking any
measurement. `timing.py` owns the isolated process group and deadline, starts a
coordinator, samples only its owned worker descendants, and publishes success
only after cleanup. `timing_worker.py` uses fresh workers and the supplied-input
client. Output contains only semantic hashes/counts and timing/resource metadata.

Seven focused `test_timing.py` tests passed in0.838 seconds using invented stub
workers, not the timing fixtures. They include real child/grandchild termination
and reaping on timeout/worker failure, partial-output rejection, post-success-write
deadline withdrawal, failure-I/O faults, bounded failure-publication timeout and
non-debug rejection. These tests are fault checks, not benchmark observations.

Root's final review must identify the exact `timing-pins.json` SHA256. The later
approved command must supply that digest via `--pin-sha256`; runtime/code/fixture
drift fails before spawning measured workers. There is no automatic launch,
scientific activation or retry.
