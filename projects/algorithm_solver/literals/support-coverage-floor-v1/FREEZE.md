# Item 56 prelaunch draft: shared-only coverage floor

2026-10-24 UTC. Draft, inactive and not pinned. No private input or launch is
authorized by this document. Root reviews implementation and invented checks;
Claude reviews the final pushed freeze before exact activation and a separately
queued launch. Item 53's run queue on cores 6/7 takes precedence; no overlap.

## Target and theorem

For each original R/naming 300 fit-source cohort, S is the complete set of allowed
exact substrings occurring in at least two distinct source IDs, including shared
single characters. Let r be the number of sources with no complete segmentation
using S. Allow all of S simultaneously; relax the 256-entry capacity.

Every covering dictionary needs at least r one-owner entries: each failing source
requires an entry outside S, and a one-owner entry cannot serve another source.
Therefore k<r is coverage-infeasible before fraction or capacity is considered.
This is a necessary floor, not the smallest achievable k. No k>=r coverage,
256-entry feasibility or 10% character-share claim follows. A separate subsidiary
floor counts sources containing a character whose distinct-owner set has size 1;
in the general supplied-input theorem it cannot exceed r. On these accepted
item 50 inputs it equals r exactly: all 96 paid alphabet singletons are in the
pool, and no pool entry is banned. Every source without a private character is
therefore coverable by shared singletons. Binding and both replay paths check
this alphabet/no-ban authority and exact equality. Independent reachability
cannot produce a stronger floor on this population. The general banned-singleton
test remains valid outside this accepted population.

The [design](DRAFT.md) and the mathematics of the [coverage kernels](coverage.py)
and [tiny exhaustive tests](test_coverage.py) are preserved. A prelaunch correctness
fix explicitly rejects optimized Python in both supplied-input entry points; a
subprocess regression verifies this guard survives `-O`. No scientific parameter,
source, ban, ownership rule, target threshold or promotion authority changes.

## Four-file authority and shared completeness

The only private files are the two original fit-source JSON files and their
original item 28 ordered pool JSON files: exactly two files per cohort, four
files total. The public-only binder derives their hashes from item 50's accepted
active contract and independently accepted evidence. It opens no private file.
No q, seed dictionary, 400-source carrier, case, validation, protected file,
held-out file or recursive directory inventory is authorized.

Original source hashes, bans through pinned structure.cjs/lexical.cjs (including
primitive arrow bodies), pool order/count, occurrence count/order digest and
shared-entry count must match accepted item 50. Source text is parsed, never executed.
Absent entries have no owners. Repeated occurrences within one source remain
one-owner. All shared entries are known to be present because accepted item 50 already
reconstructed the complete full-substring universe for these exact source/pool/
ban hashes; this diagnostic explicitly inherits that completeness authority.
It does not independently re-prove the suffix index or infer completeness from
matching counts alone. Source/pool hash or public-parent drift fails closed.

## Execution and independent replay

Production runs the unchanged trie/forward boolean reachability kernel. Private
artifacts retain every source's success flag, prefix vector, forced source sets,
owner classes/shared entry IDs and occurrence identity. No dictionary is chosen,
source rewritten, multiplier loaded, optimizer run or packet encoded.

Reporting requires the complete production result, both actual integer zero
worker exits, completed supervisor cleanup and no failure receipt before opening
any of the four authorized inputs. It reloads the same two files for each cohort
and derives bans again. The unchanged replay kernel uses fresh Aho-Corasick
occurrences from item 50's Matcher, fresh distinct-owner sets, and backward suffix
reachability. That matcher and the accepted item 50 completeness/parser lineage are
explicit shared dependencies, not a claim of entirely independent parsing.

The reporter compares every source-success flag, shared entry ID, owner class,
forced-source set, private-character count and occurrence digest exactly. A
separate fresh AC traversal checks every production prefix and replay suffix
boolean recurrence at every source position; intermediate prefix/suffix vectors
are not expected to be equal. A private checked-proof receipt binds the replay
vectors; combine rechecks its hash, shape, all common values and public aggregates.
No source IDs, characters, strings, pool IDs or reachability vectors enter public
results. Missing or corrupted cohorts never produce partial predictions.

## Budgets and bounded failure publication

Production and independent reporting are separately invoked phases, each with
600 seconds per cohort and 1200 seconds whole phase. R uses core 6 and naming core 7,
each 8 GiB RLIMIT_AS, OMP/OpenBLAS/MKL threads 1. This is per-process memory, not a
summed 8 GiB claim. Literal signal guards begin before local imports and contract
preflight. Input hashing, parser children, ownership/path checks, serialization,
normal process-group cleanup, log closing and success publication count.

Workers inherit separate process groups; the supervisor kills/reaps those groups,
including parser descendants, before accepted publication. Normal cleanup has
at most 10 seconds inside the original phase deadline. Failure has one absolute
emergency deadline, bounded by first failure+10 and original phase deadline+10;
a normal-cleanup failure anchors it to that cleanup's start. Later unlink/write/
wait/log operations check and rearm only remaining time. Hard BaseException
deadlines cannot trigger a subsequent unarmed finally-write. A publication
handler skips local I/O after an expired owner alarm and yields immediately to
supervisor withdrawal under the shared absolute emergency bound. Ordinary direct
write errors still withdraw success. No reset, retry, silent truncation, partial
promotion or success after the phase cap is allowed.

## Output, predictions and limits

Public output is allowlisted: r, subsidiary private-character source floor and
character count, shared-only coverable count, pool/support/occurrence counts,
source/pool/ban/proof commitments, phase/worker times and separate peak RSS,
all accepted item 50 positive budgets below r, and positive budgets not ruled out by
this floor. The latter means only k>=r, never sufficient feasibility.

P1: exact identity and independent reachability agreement, required true.
P2: r exceeds item 50's largest positive k in both cohorts, uncertain.
Publish both cohort floors and all budget classifications regardless of P2.
Item50's fraction result and item 53's tightening are neither revised nor erased.

Reuse only the exact original item 13 qualification identity; zero fresh jobs,
zero witness packets. Item 23's later unchanged-source exit 137 remains separate.
No semantic reuse, minimum achievable support, M1/400-of-500 admission, canonical
or package optimum, independent confirmation, current-best or promotion claim.

## Pending and development checks

The binder writes inactive pending only after review. Activation rebuilds exact
public equality and flips only active=false to true; root then separately commits,
pushes and authorizes launch. README/REVIEW/evidence are outside execution pins.
The original coverage design/kernels/tests, new execution/report/test files,
this freeze, parent authority and required runtime are pinned before any launch.

Focused invented checks cover exact two-file loader exposure, inactive rejection,
source/pool/public-parent corruption, owner/support/order mismatch, every-position
recurrence corruption, failed production before private reads, proof/public
sanitization, full two-cohort replay, and bounded failure publication. These are
implementation checks, not a corpus measurement or broad repository campaign.
