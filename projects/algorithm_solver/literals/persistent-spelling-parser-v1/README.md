# Sequential parser persistence: equivalent invented work, lower elapsed time

2026-10-24. The single pre-pinned [timing comparison](TIMING-SPEC.md) completed
in 24.279 seconds. All four blocks matched on their exact semantic hashes and
counts: 64 scalar calls, fit-derived menu, 480 proposals, two local acceptances,
complete traces, 18 variants and 17 ledger encounters per block. No source
execution or private input was involved.

| Fixed block | End-to-end seconds | Scalar seconds | Engine apply seconds | Sampled concurrent RSS, KiB |
| --- | ---: | ---: | ---: | ---: |
| Old A | 11.599398 | 8.821195 | 2.661028 | 147,048 |
| Persistent A | 0.538465 | 0.081942 | 0.318785 | 156,216 |
| Persistent B | 0.541408 | 0.082620 | 0.316161 | 155,384 |
| Old B | 11.497619 | 8.729884 | 2.626769 | 146,968 |

The old end-to-end sum divided by the persistent sum is 21.388646. There are
only two observations per path, under this exact invented workload; no
significance, corpus-throughput or item46-completion prediction follows.
Menu derivation, imports, service startup, output handling and cleanup remain
charged. Service initialization occurs in the first scalar request; the separate
spawn metric is not presented as total startup cost. Both parsing passes remain.
There is no source, parser-result, dictionary or path cache.

RSS was sampled every 20 ms for each owned worker and its descendants. Samples
can miss peaks and exited processes. Concurrent sampled sums, separate process
peaks and child-resource maxima are distinguished in [the full result](evidence/results.json).
The persistent path's observed concurrent RSS is higher on these fixtures.
Each process had an 8 GiB address-space limit; no aggregate cap is claimed.
The persistent service also has a 256 MiB V8 old-space limit and narrower
4/16 MiB request/response limits. Equivalence applies inside that stated
resource envelope, with failures outside it retained.

The [supervisor receipt](evidence/supervisor.json) confirms successful completion
and cleanup under the 120-second acceptance cap, with a separate maximum
10-second emergency cleanup allowance. All 151 code and 56 runtime pins remain
unchanged from [the reviewed inventory](timing-pins.json). There was one measured
run and no retry or fixture adjustment.

Twelve parser/equivalence/failure tests and seven supervisor fault tests passed
before measurement. They check inherited scalar bans, chunking, original key
shapes, both parser passes, complete untimed engine results, duplicate encounters,
collision/failure prefixes, deadline propagation and actual child/grandchild
termination and reaping. [Design](DRAFT.md) explains shared authority and limits.

Item46 remains an incomplete deadline-limited run. This measurement does not
repair its evidence or authorize a scientific retry. A separate follow-up must
freeze this implementation, preserve all original scientific comparisons and
gates, and pass Claude's cross-review before opening its permitted inputs.
Algorithm-solver component intent and production boundaries are unchanged.
