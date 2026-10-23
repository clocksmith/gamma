# Full-substring character-fraction certificate

Status: synthetic prototype and design, 2026-10-23. No corpus read, pool query,
fit cost, launch, or result is authorized by this document. The proposed
[execution freeze](FREEZE.md) requires team review before corpus execution.

This extends the candidate-space question in
[all-length-fraction-v1](../all-length-fraction-v1/FREEZE.md) beyond entries
shared by two programs. It represents **every nonempty exact substring** of a
fixed source population, including one-owner entries, minus an explicit set of
complete-source and solve-body bans. No substring-length ceiling or occurrence
count ceiling is needed. The implementation is
[implicit.py](implicit.py), with [synthetic tests](test_implicit.py).

## Proposed scope and what a result would mean

A first future run would reuse item 13's two exact, independently qualified
300-program fit populations (R and naming), with at most 256 optional entries
per dictionary and eight bits per selection. It would load only each pinned
`fit-sources.json`, verify all per-source qualification hashes, and derive
complete-source/body bans from those fit sources. Validation and the final
held-out populations remain closed. No source rewriting is part of this test.
This draft does not open those private files or infer their costs.

For a complete encoding let C be single-character selections and T all
selections. The objective is F = 10C - T. For nonempty programs, C/T <= 0.10
exactly when F <= 0. Single-character edges cost 9; longer edges cost -1.
Every occurring character is a candidate entry and consumes one of the 256
slots if selected. Nonoccurring strings can be removed from a dictionary
without changing its encodings, so excluding them loses no feasible solution.

A positive certified lower bound excludes a 10% character fraction for **any
dictionary and segmentation in this fixed-source full-substring class**.
It also excludes any stricter reusable-entry subclass on those same sources.
A nonpositive lower bound is inconclusive. A feasible F <= 0 dictionary proves
only that fraction condition on these sources; exact decode, complete costs,
entry reuse and semantic entry legality must still be checked.

[M1](../MILESTONES.md) requires 400 of the frozen 500 problems, median <= 32,
p95 <= 96, reusable shared entries, and zero whole-solution entries. The
[research rules](../RESEARCH.md) also reject disguised task-specific answer
bodies and require reporting large one-off chunks. Removing the two-owner
filter does not establish that every remaining string is M1-legal. In
particular, a near-whole one-owner entry may evade an exact-string ban while
still representing a disguised answer. This larger class is useful for a
negative certificate; a positive witness needs a separate substantive audit.
Neither outcome establishes M1 on 500, other source rewrites, another subset,
selection quantiles, general solving, or publication rights.

## Valid dual with one multiplier per source start

Let y_(p,i,j) mark an occurrence used by the path for source p, and x_e mark a
selected dictionary entry. The exact dictionary constraint includes
y_(p,i,j) <= x_(source[p][i:j]) and sum x_e <= B, with B = 256.

Assign one nonnegative multiplier lambda_(p,i) to **every** occurrence
constraint starting at (p,i). Sharing multipliers restricts the dual search;
it does not restrict the primal candidate pool. For a word e define

    W_e = sum(lambda_(p,i) for every occurrence start of e).

The Lagrangian lower bound is

    L(lambda) = sum_p shortest_path_p(base_cost + lambda_at_start)
                - sum_of_B_largest(W_e over all allowed distinct words).

There is one W contribution per occurrence, including overlaps and multiple
occurrences in one program. All W are nonnegative, so selecting up to B entries
reduces to the largest B weights, or all entries if fewer than B exist. For
every feasible dictionary/path, each relaxed constraint contributes a
nonpositive term; independently minimizing paths and dictionary choices can
only lower the value. Thus L(lambda) <= F for every feasible solution.

Certificates use nonnegative Python integers q_(p,i) and a positive integer D,
with lambda = q/D. The exact numerator is computed with Python integer
arithmetic. Since F is integer, ceil(numerator/D) is the certified lower bound.
No floating-point optimizer value or tolerance is accepted as a certificate.
This is a valid restricted multiplier family, not the exact full dual optimum
or a promise of a positive bound on real sources. A long one-owner suffix-edge
group can contain many different lengths with the same W. The top-256 term can
spend many activations on words sharing the same starts. A nonpositive result
may therefore reflect this multiplier restriction even if every feasible
dictionary has F > 0. It does not prove that the full-substring pool attains the
target or that literal representation fails. Length-binned or group-sensitive
multipliers are possible future refinements, outside this frozen procedure.

## O(N) groups represent every distinct substring

Let N be the total source length, P the number of sources, and L the maximum
source length. Construct a generalized suffix array with a distinct separator
for each source, then discard separator starts. Separators sort before source
characters and prevent cross-source substrings. Retain the LCP between each
adjacent pair of truncated source suffixes.

A compressed suffix-trie edge becomes one group:

    suffix-rank interval [lo, hi), allowed depth range [first, last].

Each depth is one distinct word. Every word at these depths has exactly the
same occurrence-start interval, so all its W_e values are identical. A group
stores only its interval, two depths and explicitly banned depths. There are
O(N) groups even when there are Theta(N^2) distinct words and their copied
contents would require Theta(N^3) character bytes.

For one dual iteration, build a prefix sum of q in suffix-array order. Group
weight is prefix[hi] - prefix[lo], and multiplicity is last-first+1 minus its
banned depths. Sort groups by weight; consume their multiplicities until B
entries have been counted. This computes the exact top-B sum over the full
pool. At most B actual words need be materialized for a witness attempt.

Exact banned strings are located by two suffix-prefix binary searches. Each
occurring ban excludes one depth from its group and records its forbidden
endpoint at every occurrence start. Nonoccurring bans have no effect. This
admits all remaining substrings, including one-owner and near-whole words.

## Heap shortest paths and optimization

For source length n, set d[n] = 0 and process i backwards:

    d[i] = q[i] + min(9D + d[i+1] if that character is allowed,
                     -D + min(d[j] for j >= i+2 and (i,j) is not banned)).

A heap contains reachable endpoints j >= i+2 keyed by (d[j],j). Before the
query, temporarily pop banned endpoints appearing at its minimum, read the
minimum allowed endpoint, then restore the popped values. Every endpoint is
inserted once. Removed minima can be charged to explicit banned occurrences;
there is no enumeration of all longer edges. If neither branch is reachable,
the state remains unreachable. An unencodable source fails closed.

The returned path identifies a zero/one path-start indicator. If k words were
selected from a group, add k to a suffix-rank difference array on [lo,hi).
One prefix scan gives the number of selected entries occurring at every start.
Their difference from the path-start indicator is a valid ascent
supergradient of the concave dual. Production methods
`certificate`, `weighted_selection`, and `selected_occurrences` implement these
operations. [optimize.py](optimize.py) implements the bounded loop.

The optimizer uses projected ascent with the pinned step schedule in the
execution freeze, retaining the best exact quantized certificate. A qualified seed
dictionary supplies a feasible upper bound only after its bans, capacity,
coverage and objective are checked. Materializing the shortest allowed words
from selected groups gives one deterministic witness candidate; the second
registered candidate takes the longest allowed depths. A top-weight candidate may not cover
every source. It must be rejected as infeasible, not repaired with uncharged
characters or omitted programs. Zero or negative dual values never stand in
for an actual witness.

## Independent completeness and integer replay

The verifier does not trust the production trie, cached ban endpoints, path
DP, group weights, or reported distinct-word count.

1. Check that suffix positions are exactly all source starts. Check sorted
   (first character, tail suffix rank) keys; an inverted suffix order would
   propagate to an inverted tail until a differing character or empty tail
   contradicts this check. Independently recompute truncated-source LCP with
   generalized Kasai replay in linear time.
2. Build independent range-minimum trees. For every group require positive
   depths, minimum remaining suffix length >= last, minimum interior LCP >=
   last, and both exterior neighboring LCP values < first. These conditions
   prove that every represented depth has exactly the claimed occurrence
   interval. Intervals are unique; no duplicated interval/depth word is allowed.
3. Sum the represented depth counts and require equality to the independently
   computed number of distinct substrings, sum(remaining - preceding LCP).
   Every represented word is real and unique, so count equality proves full
   coverage without enumerating words.
4. Independently relocate every exact ban with a separate sliced-prefix
   comparison implementation, check its group/depth exclusion and multiplicity,
   and reconstruct banned endpoints. Recompute weighted multiplicities and the
   exact top-B sum from q.
5. Replay shortest paths using a segment tree, querying endpoint intervals
   separated by banned endpoints. This differs from the production heap DP.
   Subtract the top-B sum with exact Python integers and compare the numerator.

The executable's structural checks use assertions; any future launcher must
prohibit optimized Python mode (`-O`) or replace assertions with explicit
validation errors. A future report must independently reconstruct this index
from pinned fit sources, rather than accepting a serialized index on trust.

## Complexity and bounded execution proposal

Let K <= O(N) be the group count, H the total character length of distinct ban
strings, and M their total occurrence count. Source separators add P positions.
The current suffix-sort dependency uses comparison sorting at each doubling
round: O((N+P) log^2(N+P)) time and O(N+P) storage. Trie construction is linear
after suffix sorting; sorting groups costs O(N log N). Ban preprocessing costs
O(H log N + M) time and O(N+M) endpoint storage. M is a real budget risk if a
future ban policy contains many short, common strings; it is not silently
truncated.

One heap certificate iteration costs O((N+M) log N + K log K) time and O(N+M)
working storage. Top-B selection and its gradient do not expand multiplicity.
Independent replay costs O(N + H log N + (N+M) log N + K log K) time and
O(N+M) storage. Temporary verifier slices are limited to supplied ban lengths.
Materializing B witness words costs O(BL) character storage. These are operation
counts; arbitrary-precision arithmetic also depends on integer bit length.

Before a corpus run, freeze exact sources, bans, qualification receipts,
dependency/runtime hashes, ascent procedure, quantization and witness choices.
A proposed first comparison uses the item 28 budgets: R on core 0, naming on
core 1, OMP/BLAS threads 1, at most 2,000 iterations or 1,200 seconds per arm,
8 GiB address space per worker, and a 2,400-second whole-job deadline including
input checks, index construction and certificate replay. A timed-out or
memory-failed arm produces a retained failure record, not a clipped pool or an
accepted partial certificate. No claim of corpus feasibility or expected
runtime is made from the synthetic tests.

## Synthetic acceptance evidence

`python3 -m unittest discover -s projects/algorithm_solver/literals/all-substring-fraction-v1 -p 'test_implicit.py'`

Eleven tests pass. They include 180 randomized comparisons of the entire
implicit pool, top weights, selected-occurrence counts and exact numerators
against the old explicit all-occurrence dual; 40 tiny exhaustive dictionary
enumerations checking weak duality; prefix/repeated/duplicate suffixes;
one-owner near-whole words; source/body-style exact bans; unencodable pools;
very large integers; and independent rejection of corrupted suffix order,
LCP, group coverage and membership. A generic 700-character distinct-symbol
source has 245,349 allowed distinct words represented by 700 groups. A separate
3,302-character repetitive fixture checks the linear LCP replay path. Optimizer
tests check retained exact bounds and feasible upper bounds; actual synthetic
subprocesses verify deadline termination and whole-job rejection on failure.

These are implementation checks on invented strings. They are not a run,
feasibility measurement, qualification receipt, or evidence about the private
Gamma populations. Component intent and all protected-data boundaries remain
unchanged.
