# Item 58: historical item 51 comparison resolves with no successor

2026-10-24 UTC. The separately reviewed [carrier replay](FREEZE.md) resolves
item 54's historical comparison against **fixed item 51 flat, commit
`5389ce575`**. No item 54 spelling candidate passes the complete successor rules
under either policy. This is a historical comparison, not a claim about today's
current best or permission to promote a candidate.

Item 58's R1 (complete comparator resolution) and R2 (no historical successor)
are true. Restated item 54 P1–P4 are true; P4 means no candidate passes. **The
original item 54 report-v2 remains preserved with P4=null.** Its unresolved
record was not patched or overwritten. The new result is in
[evidence/results.json](evidence/results.json), with a compact generated
[report](evidence/REPORT.md) and [review](REVIEW.md).

## Fixed comparator and candidate effects

On the 100 consumed-validation sources, item 51 has 8,183 selections and 8,283
actions under both policies. Canonical minimizes `(N, complete IDs)`; min-C
minimizes `(N, C, complete IDs)`, preserving actual dictionary order. N excludes
Finish, actions=N+1 per source, and character fraction is C/N.

| Fixed item 51 policy | C | C/N | Median / p90 / p95 N | Raw / decoder-inclusive package bytes |
| --- | ---: | ---: | --- | ---: |
| Canonical | 4,051 | 49.5051% | 61.5 / 154 / 195 | 14,979 / 27,989 |
| Min-C | 3,991 | 48.7718% | 61.5 / 154 / 195 | 14,979 / 27,989 |

All six candidate-policy comparisons are shown below. Paired counts are
validation action counts, better/same/worse against the fixed comparator.
Package deltas are raw bytes; decoder-inclusive deltas are identical.

| Candidate | Policy | Actions / delta vs 51 | C / C/N | Paired better/same/worse | Package delta | Failed gates vs 51 |
| --- | --- | ---: | ---: | --- | ---: | --- |
| 24-S | Canonical | 8,336 / +53 | 3,998 / 48.5430% | 0 / 79 / 21 | +19 | Strict actions |
| 24-S | Min-C | 8,336 / +53 | 3,938 / 47.8145% | 0 / 79 / 21 | +19 | Strict actions |
| 43N-S | Canonical | 8,285 / +2 | 3,968 / 48.4789% | 0 / 98 / 2 | -2 | Strict actions |
| 43N-S | Min-C | 8,285 / +2 | 3,908 / 47.7459% | 0 / 98 / 2 | -2 | Strict actions |
| 43W-S | Canonical | 8,301 / +18 | 4,011 / 48.9087% | 5 / 74 / 21 | +219 | Strict actions, median |
| 43W-S | Min-C | 8,301 / +18 | 3,951 / 48.1771% | 5 / 74 / 21 | +219 | Strict actions, median |

Character fractions fall against item 51 by 0.9621/0.9574 percentage points for
24-S, 1.0261/1.0260 for 43N-S, and 0.5964/0.5948 for 43W-S (canonical/min-C).
Those fraction gains do not satisfy the required strict action improvement.
43N-S passes all other standing comparisons and misses the historical item 51
action gate by two actions; this does not justify changing the gate afterward.

All own-U transfer predicates still pass under both policies, as do all R
readiness comparisons. Other unchanged failures are: 24-S versus best24
(actions) and NCP (breadth); 43W-S versus seed13, N and best24 (median), and NCP
(median and breadth). All 12 accepted U/S policy views retain full 400-source
coverage, qualification and legality, but no M1 admission or independent
confirmation is established. The full gate tables and per-ID metadata remain
in the evidence, including the controls.

## What was replayed and charged

Item 58 reconstructs and decodes **800 item 51 packets**: 400 sources under each
policy. It performs zero new candidate packet decodes; the **4,800 item 54 views**,
proposal/ban replay and qualification remain inherited accepted authority.
There are zero fresh qualification jobs, source executions, dictionary/source
searches, model bytes or training steps.

The correction distinguishes three identities for the original item 43N seed:
original JSON bytes, item 54's rewritten JSON bytes, and the ordered dictionary
binary. It verifies the original bytes, reproduces the pinned writer format,
and reconciles exact order and binary identity. It does not substitute set
identity or equal costs for dictionary order. All 400 source hashes match the
original qualification and item 51 source authority. The item 51 dictionary is
checked against original-source/body bans in 25 old-parser batches of 16 inputs.

The [supervisor](evidence/supervisor.json) completed in **4.546927202 seconds**
with actual integer exit 0, completed cleanup and no timeout. Worker time was
4.398508135 seconds, including 3.986011953 seconds of parser work; peak worker
RSS was 74,380 KiB. The frozen caps were 600 seconds per worker, 1,200 whole,
cores 0–3, 8 GiB per process and one bounded 10-second emergency allowance.
All **194 code and 56 runtime pins** were rehashed unchanged.

Item 51 uses 256 paid entries, including 92 singletons, with a 2,696-byte
dictionary. Packets charge 41 framing bytes plus eight-bit IDs with zero padding;
the shared decoder inventory adds 13,010 bytes per cohort. Offline implementation
source totals 822,842 bytes; installed runtime size is unmeasured. Earlier item
54 production and both report costs remain charged in their own record.

Only finalized metadata was copied for this record. The result SHA256 is
`faf7e095700c1aeb74beb964ece77bc4ec75aa08b75a63c9ad4af94ac386684d`.
No private carriers were reopened during recording. Original item 46's timeout,
item 54's unresolved comparator record and all original thresholds are preserved.
