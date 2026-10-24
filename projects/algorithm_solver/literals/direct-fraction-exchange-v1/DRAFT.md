# 44: Direct coverage-preserving fraction exchange, design draft

2026-10-23. Original design and supplied-input synthetic evidence; the subsequent
inactive implementation is governed by [FREEZE.md](FREEZE.md). No private
source, candidate pool, seed, q, case, or result file has been opened for this
item. A loader, public-only pending binder, runner and independent reporter are
being prepared for review; there is no activated launch contract.
The intended component boundary and all existing frozen records are preserved.

## Concrete question and public motivation

Can exact direct dictionary additions and exchanges improve the minimum-F
covering seed inside **the same bounded pool used by item 40**, when its global
MILP exhausted each 600-second solve budget without a reported search node?
This tests a different incumbent-improvement mechanism, not a larger pool or a
claim that MILP, or any other optimizer, cannot solve the problem.

Item 40 publicly recorded the following independently replayed minimum-F
encodings on separate fixed 300-program fit populations:

| Cohort | Seed/warm F | Cold F | Seed C | Seed N | Seed median/p95 N | Pool words / arcs |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| R | 110156 | 192792 | 13871 | 28554 | 74.5 / 199 | 2004 / 179677 |
| naming | 94121 | 173398 | 12122 | 27099 | 71 / 193 | 1779 / 175023 |

Both seeds contain 249 entries, leaving seven slots under capacity 256. Both
warm outputs tie their seeds; cold outputs cover but have worse F and N.
These facts motivate a protected incumbent and direct exact rescoring. They
do not establish a defect in the candidate pool or imply that a 10% fraction
is attainable. References: item40 [report](../fraction-primal-repair-v1/README.md),
[pool definition](../fraction-primal-repair-v1/DRAFT.md), and
[metadata](../fraction-primal-repair-v1/evidence/results.json).

## Population, representation, and comparisons

Keep R and naming as separate fixed-300-fit questions. Reuse item40's *exact*
ordered candidate pool and measured seed, with independently reconstructed
pool equality and public parent hashes in a future reviewed binding. Do not
re-mine, expand, replace, or silently prune the pool. Inherit complete-source
and solve-definition/body bans, the 2048-entry candidate limit, two million
candidate characters, twenty million trie transitions and one million arcs.
The future loader must verify actual seed size/coverage and remaining capacity;
seven free slots is a public observation, not permission to assume a shape.

Every singleton consumes a dictionary slot. No character fallback exists.
Dictionary capacity is at most 256; packets retain the fixed eight-bit selection
format even with 249 or fewer entries. N counts selections excluding Finish;
actions=N+1 per program. F=10C-N is a threshold-feasibility objective:
F<=0 is equivalent to aggregate C/N<=10%, but minimizing F does not globally
minimize C/N. For example, C=1,N=100,F=-90 has a lower character fraction than
C=30,N=400,F=-100. Both F and C/N must be reported without claiming that
improvement in one implies improvement in the other.
Min-F encodings are not min-N encodings: a lower F can buy more selections and
worse quantiles. No validation or protected population, source rewriting,
source execution, training, or independent-description work is included.

Compare the retained seed and every retained direct incumbent against item40's
seed, warm and cold dictionaries under the identical canonical min-F policy.
Report F, C, N, fraction, actions, selection median/p90/p95, full dictionary and
packet bytes, decoder cost, one-owner entries, near-whole entries and overlap.
One-owner means occurrence in exactly one source. Near-whole means length at
least 90% of any containing source, preserving item40's descriptive definition.
Use all dictionary entries in share denominators. Exact whole-source/body bans
remain mandatory; these support/size statistics do not prove semantic reuse.
This is a relaxation witness study, not an M1 candidate or acceptance test.

## Exact scorer and cache proof

Build the unchanged item40 trie occurrence graph once. Each arc advances in
one source, carries its word and stable pool ID, and has cost 9 for a singleton
or -1 otherwise. For a selected dictionary, a backward DAG dynamic program
minimizes `(F,N,entry-ID sequence)`. Unique words and sorted dictionary order
make the first differing entry ID equivalent to the first differing word in
lexicographic order. Thus stable sorted pool IDs and renumbered sorted subset
IDs choose the same path. Cache actual **word strings**, never subset IDs.
Reconstruction follows cached words and checks exact source concatenation.
Use sorted literal order consistently for the seed, matched references and
direct outputs after verifying the original parent dictionary identity. The
parent's original dictionary/packet hashes stay recorded; sorted reserialization
is separately identified. Sorting changes ID ties, not per-program minimum F
or its minimum-N tie, C=(F+N)/10, or package byte lengths. No original packet hash
is claimed for a reserialized dictionary.

For a move adding words A and deleting words R, invalidate the union of:

- sources containing any word in A; and
- sources whose current canonical optimal path uses any word in R.

Recompute the entire source DP for each invalidated source, including cases
that become unreachable. Other sources have no added occurrence and retain
their previous canonical path. Deleting other edges cannot improve the optimum
or remove that path, so their prior `(F,N,lexical path)` remains optimal. This
proves exactness of the incremental evaluation, including simultaneous
multi-entry moves. A coverage failure rejects the proposal. In particular,
**an infeasible standalone deletion is not grounds to skip its swap**: the
added word may repair the same source. Tests include such an improving swap.

Keep only the incumbent cache, current trial, and best evaluated eligible
neighbor; do not memoize a growing dictionary-to-plan history. Scalar scores
for the candidate shortlist may be retained, but full proposal plans may not.
For P source characters and E occurrence arcs, a full score is O(P+E); a move
scores only affected programs, plus O(number of programs) aggregation. The
graph and a constant number of plan caches use O(P+E+pool characters) memory.
Early coverage failures can reduce actual work; count them rather than treating
them as zero-cost completed feasible evaluations.

## Proposed direct search for subsequent review

Only retain a fully covering dictionary of at most 256 entries. Rank eligible
incumbents lexicographically by `(F,total N,full package bytes)`, with sorted
word/pool-ID order breaking exact proposal ties. Accept only strict improvement
in the first three quantities; ID changes alone do not justify a move. This
makes best F nonincreasing. The package term includes dictionary framing and
UTF-8 entry bytes, all eight-bit packets and Finish/framing, plus the fixed
decoder inventory. It is a tie rule, not the character-fraction acceptance gate.

Phase A: while capacity remains, for at most the verified initial number of
free slots, score every inactive pool entry as a single addition and accept
the best improving complete proposal. Stop this phase if none improves.
The 249-entry parent seeds permit at most seven such accepted additions.

Phase B: at most twelve epochs. At each current dictionary:

1. Score all inactive entries as additions. At capacity 256, the temporary
   257-entry state is **only a ranking relaxation**; it is never serialized,
   accepted, published as a witness, or used for readiness. Its path score and
   algebraic eight-bit package surrogate only order the proposals. A 257-entry
   dictionary has no serializable eight-bit packet in this representation.
2. Score every single removal, retaining coverage failures in the counters.
3. Select the four best added words by their exact addition ranking and stable
   pool ID. Evaluate **every currently selected removal against each shortlisted
   addition jointly**, including removals that failed alone. This is at most
   1024 swaps per complete epoch. It is not an exhaustive all-pool swap search.
4. Accept the best strict eligible improvement among available single additions,
   removals and joint swaps. Rebuild or independently recheck its exact aggregate
   before retaining it. Stop after a completed epoch with no improvement.

No two-entry block search is proposed for the first execution. The supplied
mechanism supports such moves for correctness tests, but enabling them later
would require a different declared opportunity set and budget.

Proposed search limits per cohort: 600 seconds total search time, 50,000 exact
move evaluations **including ranking and removal probes**, the Phase-A bound,
and twelve Phase-B epochs, whichever is reached first. One core and 8 GiB per
process; actual production cores remain for root scheduling. Propose 1200 seconds
for the entire production job including pool replay, graph construction, search,
checkpointing and output, plus a separate 1200-second independent reporter cap.
These are proposed resource limits, not a predicted runtime.

Check time before each proposal and each per-source recomputation. An interrupted
trial is not an evaluated candidate. Stop at the search limit, retain the last
fully checked best state, and record the exact partial sweep opportunity count.
A strictly improving fully evaluated best-so-far neighbor from an incomplete
sweep may be accepted as the final state, explicitly marked partial-sweep
selection. It establishes no local optimum. A full-job timeout or independent
replay failure yields no accepted overall result. Retain seeds intentionally
as initial incumbents; do not disguise a lost/invalid incumbent as a fallback.

Log attempted and completed additions/removals/swaps, ranking-only calls,
coverage failures, affected-program recomputations, shortlist size, sweeps
completed/partial, acceptance reason and exact F/N/package deltas, elapsed time,
peak memory, and the first unmet budget. Completed all-removals-times-shortlist
claims require the entire declared sweep to finish. No stationarity claim is
made for omitted added words, unsearched blocks, the larger substring class,
other sources, or M1. A retained nonpositive F would be a covering relaxation
witness for this fixed fit population only.

## Synthetic evidence and implementation decision

`mechanism.py` contains the supplied-text graph and exact move scorer.
`test_mechanism.py` has five focused tests: exhaustive tiny covering dictionaries
and single moves against item40's independent sliced-string DP; a feasible
improving swap after infeasible deletion; rejection of overcapacity ranking
states as incumbents; ID-renumbering-safe cached word plans; and randomized
two-add/one-remove moves checked against full DP. All five passed.

The pinned synthetic fixture contains 300 invented sources totaling 75000
characters, an independently generated 2048-word pool, and a 249-word seed.
It constructs 188961 occurrence arcs. On core6 with 8 GiB address space and a
60-second outer/55-second worker cap:

| Work | Completed opportunities | Recomputed programs | Measured seconds |
| --- | ---: | ---: | ---: |
| Graph and seed | 1 | 300 | 0.197 |
| All additions | 1799 | 41600 | 5.889 |
| All removals | 249 | 29482 | 3.225 |
| All removals times four added words | 996 | 216398 | 23.361 |

Total worker elapsed was 33.352 seconds; peak RSS was 145120 KiB. Fourteen
standalone removals and 56 swaps failed coverage. See
`synthetic-spec.json` and `synthetic-results.json` for pinned hashes, exact
synthetic objective values and counters. These invented-data timings support
implementing a small bounded direct search; they neither predict corpus gains
nor guarantee that a corpus sweep fits the proposed budget. All ranking,
removal and swap work is included. No corpus probe was used to choose the design.

Root approved implementing the opportunity set and proposed budgets; the next
decision is review of the inactive loader/runner/reporter and freeze. The reporter
must rebuild the exact parent pool, source and seed bindings; independently
decode and min-F rescore every retained dictionary; check capacity/bans and
complete metadata; and preserve failures. Public outputs remain numeric
metadata, fixed enums and hashes. Source, dictionary words, plans and packets
stay private. There is no execution authorization in this draft.
