# Length-sensitive full-substring dual (board item 35)

Status: reviewed mechanism with a [prelaunch execution freeze](FREEZE.md) and
synthetic-tested runner. No private source/q reads, population measurements or
launch have occurred for item35. Item33 recordedc8ed60959 and remains unchanged.
The execution design deliberately follows its disclosed zero-multiplier result;
review and core allocation are still required before launch. The implementation is
[implicit.py](implicit.py), tested by [test_implicit.py](test_implicit.py).
Component intent and authority are preserved.

## Question and unchanged primal universe

Item33's full allowed-substring relaxation gives every outgoing occurrence at
one source start the same multiplier. Many rare longer alternatives sharing that
start can therefore have identical dictionary weights, and top256 may spend many
activations on them. Length bins can distinguish some of these alternatives;
they do not eliminate the effect, especially within the257+ bin. No conclusion
about the sign or strength of a corpus bound follows from this motivation.

Retain exactly item33's primal universe: every nonempty exact substring of the
same fixed source population, minus the same exact whole-source/body bans. All
occurrences, including overlaps, one-owner entries and near-whole fragments,
remain represented. Every selected entry, including characters, consumes one
of B=256 slots; there is no free fallback alphabet. No maximum length, owner
count requirement or occurrence truncation is introduced.

The objective remains F=10C-T, with cost9 for length1 and−1 for longer selections.
For nonempty complete encodings, F<=0 is equivalent to C/T<=10%. A positive
certified lower bound excludes that fraction for every dictionary/segmentation
in this fixed-source class. A nonpositive bound is inconclusive. A feasible
nonpositive witness would show only this fraction condition after exact decode,
coverage, capacity and entry audit; one-owner near-whole fragments may still be
substantively prohibited disguised answers. Neither outcome proves M1 or
performance under different sources, populations or rewrites.

## Fixed multiplier family and weak-duality proof

The eleven bins are fixed before any source use:

| Bin | Inclusive lengths |
| ---: | --- |
| 0 | 1 |
| 1 | 2 |
| 2 | 3 |
| 3 | 4 |
| 4 | 5–8 |
| 5 | 9–16 |
| 6 | 17–32 |
| 7 | 33–64 |
| 8 | 65–128 |
| 9 | 129–256 |
| 10 | 257 and longer |

Let b(l) denote the bin of length l. Each occurrence constraint
`y_(p,i,j) <= x_(source[p][i:j])` receives nonnegative multiplier
`q_(p,i,b(j-i))/D`, for integer q>=0 and positive integer D. Multipliers share
only within a source/start/bin; the candidate universe is not restricted.
For each allowed distinct word e,

```
W_e(q) = sum(q_(p,i,b(len(e))) over all occurrences of e at (p,i)).
L_num(q) = sum_p min_path sum_edges(D * base_cost(length) + q_(p,i,b(length)))
           - sum_of_B_largest(W_e(q)).
```

Every feasible primal path/dictionary has y−x<=0 on each occurrence, so adding
these nonnegative-multiplier terms cannot increase its F. Minimizing paths and
dictionary independently lowers it further. Therefore `L_num(q)/D <= F` for
every feasible dictionary and segmentation. Nonnegative weights make the
cardinality subproblem exactly the B largest weights, or every allowed word if
fewer than B exist. Words are distinct entries; repeated occurrences contribute
to a word's weight but do not consume additional slots.

All certificate arithmetic uses Python integers. The valid integer lower bound
is `ceil(L_num/D) = -(-L_num // D)`, including negative numerators. Floating-point
optimizer values, tolerances and heuristic witness costs cannot certify a bound.
Optimized Python/PYTHONOPTIMIZE is rejected explicitly because validation uses
assertions. Empty paths need separate fraction interpretation; a future contract
must pin a nonempty source population rather than infer C/T from0/0.

## Exact embedding of item33 and ascent derivative

Set every bin at a start to item33's multiplier: `q_new[p,i,b]=q_33[p,i]`.
Every occurrence cost and every word weight then matches item33 exactly, hence
its entire numerator, top256 penalty and path sum are reproduced. This embeds
the old feasible multiplier family. The supremum over the enlarged family
cannot be lower, but this says nothing about a finite optimizer's strict gain.
A future procedure must retain and independently replay item33's certificate as
an initialization and diagnostic. Retaining the best verified initialization
prevents reporting a weaker completed certificate; it does not promise any
improvement or guarantee that a budget-limited execution completes.

For a minimizing path and maximizing dictionary selection, define

```
g[p,i,b] = count(path edges starting at i in bin b)
           - count(selected distinct entries in bin b occurring at i).
```

The chosen path and dictionary make L_num an active affine function of q, so g
is a concave supergradient: `L_num(q') <= L_num(q) + g·(q'−q)`.
Path counts are0/1. Dictionary counts include every selected length in an
interval/bin piece, even if several lengths share the same occurrence starts.
The projected ascent uses this derivative. Its schedule, quantization,
initialization, stopping rule and budgets are fixed in [FREEZE.md](FREEZE.md).

## Compressed pieces and exact top256 without word expansion

Reuse item33's generalized suffix index and independent completeness verifier.
Each compressed trie group represents one suffix-rank interval[lo,hi) and every
allowed depth in[first,last], excluding explicitly banned lengths. Split this
depth range at the eleven fixed bin boundaries. A piece stores its parent group,
bin, suffix interval, clipped depth range, banned depths and multiplicity.
There are at most K*G pieces for K=11 and G=O(N) parent groups. Pieces partition
exactly the old allowed word set; no new word is created or omitted.

For bin b, build the prefix sums of q[p,i,b] in suffix-array order. A piece's
weight is `prefix_b[hi]−prefix_b[lo]`, shared by each of its allowed lengths.
Sort pieces by descending weight and deterministic piece index, taking
`min(remaining_budget, multiplicity)` entries per piece. Multiplicity is counted
arithmetically, including when many entries share the same weight. This is the
exact topB sum over all distinct words, not a heuristic group selection.

For a selected piece with k lengths, add k to a bin-specific suffix-interval
difference array. A prefix scan gives the dictionary part of g at every start.
No individual occurrence list is expanded. At most B words may be materialized
for later shortest-first/longest-first witness diagnostics; these are not
included as executed corpus procedures in this draft.

## Production interval DP and independent heap replay

For source length n, let d[n]=0 and process starts i backwards. Each bin[lo,hi]
queries the endpoint interval `[i+lo,min(n,i+hi)]`; the final unbounded bin ends
at n. Exclude exactly the banned endpoints for that start. An interval with its
lower bound beyond n is empty. The recurrence is

```
d[i] = min_b(q[p,i,b] + D*(9 if b==0 else -1)
             + min(d[j] over the allowed endpoint interval for b)).
```

The production DP keeps reachable `(cost,endpoint)` pairs in an online segment
tree. Sorted banned endpoints split each query into disjoint half-open ranges;
range minima are exact. Ties use endpoint then bin for reproducible backtracking.
If every branch is unreachable, the state stays unreachable. An uncovered source
fails closed and cannot be dropped from a denominator or assigned free edges.

Independent replay retains a separate heap for each bin. At each backwards step,
insert the new lower-bound endpoint if reachable. Lazily remove endpoints beyond
the current upper bound. Temporarily remove banned minima, read the first valid
minimum, then restore the removed banned entries. Every endpoint is retained
until expiration; a nonminimum endpoint is not discarded as dominated.

An ordinary monotone deque is unsafe here. An endpoint dominated by a cheaper
endpoint may be the best allowed alternative when that cheaper endpoint is
banned at the next queried start. Restoring only a popped minimum cannot recover
an alternative that the deque previously discarded. The heap version deliberately
retains those alternatives. Per-bin heaps can retain buried expired elements,
so their storage is O(KN), not an asserted O(N) aggregate bound.

The verifier first invokes item33's independent suffix-order/LCP/group/ban
completeness replay with zero multipliers. It independently reconstructs the
bin partition, checks every piece and bin lookup, recomputes topB from integer
prefix sums, and relocates bans by separate sliced-prefix searches. It compares
these endpoint sets with the production cache. The final numerator uses the
independent heap DP, not production segment-tree distances or backpointers.
Neither certificate verifier alone supplies source provenance; a later runner
must pin authorized sources, qualification receipts and dependency hashes.

## Complexity and remaining run decisions

Let N be total source length, P source count, G parent groups, S<=K*G pieces,
H total length of distinct ban strings and M total banned occurrence count.
The inherited suffix build costs O((N+P)log²(N+P)) time/O(N+P) space; exact ban
location costs O(H log N+M). Piece splitting costs O(KG+KM) with the current
small fixed K=11. No length or occurrence cap is hidden in these counts.

A certificate iteration uses O(KN+S log S) time for weights/topB and
O((KN+M)log N) for the segment-tree paths, including endpoint exclusions.
Dictionary derivatives take O(KN+KB) time. Working storage is O(KN+S+M), including
multipliers, derivative arrays and path metadata. Independent replay adds the
parent completeness/ban checks and has the same per-bin heap path bound, with
O(KN+S+M) storage. Arbitrary-precision arithmetic also depends on integer bit
length. Materializing B witness words separately costs O(B*maximum_source_length).
The allowed word count can be Theta(N²); neither production path expands it.

The [freeze](FREEZE.md) now pins item33 identities by inherited public metadata,
the verified lift and22 bin releases, projected ascent and independent reporting.
Its1,200-second optimizer budget includes initialization and releases; a2,400-second
whole-job deadline covers all execution phases. No resource estimate or draft
file authorizes a run before root/Claude review and core allocation. A finite
nonpositive result remains a limitation of the tested multiplier search, not a
certificate that the full pool can meet10%.

M1 remains400/500,<=256 shared entries, median<=32/p95<=96 selections,
<=10% single-character selection bits and zero whole-solution entries. The
negative-certificate superset includes one-owner fragments only to make a valid
exclusion stronger; it does not relax M1 entry legality or other owner gates.

## Synthetic evidence

Nine focused tests pass. They cover160 randomized complete explicit-occurrence
comparisons (including exact topB and binwise derivative counts),60 lifted
item33 comparisons at three capacities,40 exhaustive tiny dictionary searches
for weak duality,40 concave supergradient inequalities, every length boundary
through257+, a banned-minimum alternative, huge integer arithmetic, unencodable
pools and rejection of corrupted pieces, bins, suffix membership and bans.
A700-character distinct-symbol fixture has245,349 allowed words represented by
at most11 times its700 parent groups. This checks structure, not a corpus
performance estimate. All strings are invented within the tests.

Run only the focused synthetic checks:

```
python3 -B -m unittest discover -s projects/algorithm_solver/literals/length-sensitive-fraction-v1 -p 'test_implicit.py' -v
```

Runner preparation adds six focused checks: verified zero-parent retention and22
identity skips, exact nonzero release deduplication, corrupt-parent rejection and
zero-budget baseline preservation, equality-only optimality, real synthetic
process timeout/failure cleanup, and a complete invented300-source two-arm report
with corrupted multiplier/accounting/packet rejection and failure reporting
without input access. Fifteen tests pass in total. No private source or q file
was opened to prepare them.
