# Item 57: cap each owner's charge by a nonoverlapping path schedule

2026-10-24 UTC. Mathematical design and invented supplied-input checks only.
No corpus input, binding, timing campaign, runner, pending contract or launch.
This follows [item 53](../potential-tightening-v1/DRAFT-NEXT.md) at its fixed
integer penalties and unchanged suffix potentials. It does not change any
item 50/53 file or make an empirical claim about either cohort.

## Fixed quantities and scope

Keep all allowed exact substring occurrences, the global source/body bans,
original distinct-source ownership, denominator D, fixed nonnegative occurrence
penalties q53, suffix distances d, and summed path minimum L unchanged. A
singleton remains a paid entry, classified by actual distinct-source support.
Let B be capacity (eventually 256) and k the at-most one-owner-entry budget.
Every source must be segmented completely; no uncounted fallback characters.
The objective is F = 10C - N, with base cost 9 for a singleton and -1 for a
longer occurrence. The full allowed DAG uses edge cost D*base + q53.

An entry with no occurrence can be omitted without affecting paths or penalties;
keeping it only consumes capacity. All sets below consist of occurring entries.
A shared entry occurs in at least two distinct source IDs. A one-owner entry
occurs in exactly one, regardless of repeated or overlapping occurrences.

This construction caps the **path's used penalties**, not a dictionary's sum of
all occurrence weights. The latter can exceed the new cap. Do not describe the
new charge as an upper bound on that activation sum. Shared occurrence sums
remain the unchanged item 53 upper bound; a joint shared-plus-one-owner path cap
is outside item 57. Coverage quotas from item 56 are unnecessary here.

## Per-owner bound

For owner p and its one-owner entry e, define w_e as the sum of q53 over every
occurrence of e. Sort its entry weights in descending order with deterministic
entry-identity ties. A_p(j) is the sum of the first j weights, A_p(0)=0.

Let R_p be the maximum total q53 weight of a nonoverlapping set of **all** allowed
one-owner occurrences in p. Intervals are half-open; touching intervals are
compatible. Free skips are permitted in this auxiliary scheduling problem, so
R_p is not required to encode or cover the source. No dictionary-capacity or
entry-count constraint is imposed on this schedule. These relaxations are
intentional upper bounds, never a witness or free decoding fallback.

If a dictionary contains j_p one-owner entries belonging to p, the one-owner
penalties on any actual complete path are bounded by both:

* A_p(j_p): every used occurrence belongs to those selected entries, all q are
  nonnegative, and their total occurrence weights are no larger than the top j_p.
* R_p: the path's used one-owner occurrences form a nonoverlapping schedule.

Consequently their sum is at most f_p(j_p) = min(A_p(j_p), R_p). This holds for
**every** encoding path, not only minimum-F, minimum-N, or canonical paths.

## Exact relaxed allocation

A_p has nonnegative, nonincreasing increments. Capping at R_p preserves this:
increments before crossing R_p are unchanged, the crossing increment is between
zero and its original increment, and later increments are zero. Thus f_p is
discrete concave and nondecreasing.

Let U(j) be the maximum sum_p f_p(j_p) subject to integer j_p>=0,
sum_p j_p=j, and each owner having enough distinct entries. Form every owner's
marginal sequence f_p(t)-f_p(t-1). Taking the largest j marginals gives U(j)
exactly: the sum of any feasible prefix selection is at most the unrestricted
largest-j sum, and a deterministic sort by descending marginal, then owner ID,
then rank makes that selection prefix-closed. The upper bound is therefore
attained by an allocation in this relaxed numerical problem. This is not a
claim that an actual dictionary/path attains all selected owner caps together.
A heap containing the next marginal of each owner implements the same ordering.
Zero marginals and tied caps remain in the finite sequence; tie rules preserve
prefixes. Owners with no one-owner entries contribute nothing.

Let H(s) be the unchanged prefix sum of the largest s shared-entry weights,
clamped to the number of shared entries. The new charge at support budget k is

    T57(k) = max_{0 <= j <= min(k,B,m_one)} [U(j) + H(B-j)].

Use fewer one-owner slots on equal maximizing charges, as in item 53. The relaxed
owner allocation is exact for this formula, but the formula itself is a safe
upper bound on actual path penalties, not a primal optimum.

## Weak duality and dominance

For a covering dictionary of size at most B and at most k one-owner entries,
let j_p count its entries per owner and j=sum j_p. Its actual path penalties Q
are bounded by sum_p f_p(j_p) plus the shared top-prefix at B-j, hence Q<=T57(k).
The unrestricted fixed-q full DAG minimum satisfies L<=D*F+Q for those paths.
Therefore

    D*F >= L-T57(k),       F >= ceil((L-T57(k))/D).

Negative base costs cause no issue: all edges advance in an acyclic source DAG.
Only the multipliers, not the base costs, require nonnegativity.

For any allocation, sum_p f_p(j_p)<=sum_p A_p(j_p). Maximizing the right side
over owners gives the ordinary top-j prefix of all one-owner entry weights.
Thus T57(k)<=T53(k) at every k, with identical L and D. Numerators and their
integer ceilings cannot worsen. A positive lower bound excludes F<=0 only in
the fixed-source/support class; it does not prove the class contains a covering
dictionary. A nonpositive result does not bound the optimum over other q/d.

## Top-B sufficiency, and what cannot be truncated

Every relevant j_p<=j<=B. The top B entry weights **per owner**, with all ties
resolved deterministically, therefore determine every needed A_p(j_p). The top
B shared entries likewise suffice. Entry counts below B must remain known;
missing entries cannot be replaced by invented zero-valued entries.

R_p is different. It must use every allowed one-owner occurrence, or an exact
implicit calculation proved equivalent. Truncating its schedule to occurrences
of only the owner's top B entries is unsound: a lower-weight entry can supply a
compatible interval and raise R_p. On source `aaaa`, the tests give each `aaa`
occurrence penalty 10, each `a` occurrence penalty 4, and `aa` penalty zero.
The top1 entry `aaa` has weight 20 but restricted schedule cap 10. The omitted
entry `a` has weight 16 and alone covers the source with penalty 16 at B=1.
The full R_p=16 is required; the truncated cap 10 is not an upper bound on this
actual allowed path's one-owner penalty.
Likewise, an inherited global top256 list does not determine the top256 **per
owner**, and neither list determines R_p. Full old/new allowed-entry provenance
and exact bans would still need reconstruction in any later implementation.

## Algorithms and limits of this prototype

For explicit occurrences, compute R_p by weighted interval scheduling:

    r[0]=0
    r[t]=max(r[t-1], max_{one-owner (i,t)} r[i]+q(i,t)).

With occurrences bucketed by endpoint, this uses O(n_p+E_p) work and O(n_p+E_p)
storage including buckets, or O(n_p) auxiliary storage with an ordered stream.
Free skip r[t-1] is essential. It is unrelated to the negative-cost shortest-path
recurrence used to reconstruct L. Per-owner bounded top lists require
O(E + M log B) aggregation work after entry identity/ownership is available;
full entry weights require either streaming each entry's occurrences or explicit
weight storage. Keep at most min(B,m_p) weights per owner, rather than B global
weights. Allocation needs O(P+B log P) heap work and O(PB) capped-prefix storage
in a straightforward implementation. Combining all k=0..B by direct scanning
costs O(B squared), negligible in the proof but still counted.

These are **explicit-graph** bounds, not a demonstrated scalable full-substring
method. The full occurrence set can be quadratic in source length and explicit
substring bytes cubic. The supplied [proof.py](proof.py) intentionally materializes
all allowed substring strings and a complete q mapping for tiny inputs; it also
rescans edges per source. It is an exhaustive oracle, not a production adapter.
A future implementation must derive exact R_p over the full allowed graph,
including exclusions and old/new edges, within a separately approved envelope.
No runtime extrapolation, corpus feasibility, implicit shortcut or resource
claim is made here.

## Development evidence and interpretation

[Tests](test_proof.py) independently enumerate tiny dictionaries, every complete
encoding path, nonoverlapping interval subsets, and integer owner allocations.
They compare charges, fixed-q path minima, exact ceilings, and the weak-duality
inequality for all covering cases. Cases include cross-entry overlap with strict
gain at actual q53 potentials, repeated one-owner occurrences, nonoverlap with no
gain, shared singletons, zero weights, capacity zero, excess capacity, ties,
missing/negative/bool penalties, and optimized-Python rejection.

No multiplier search, potential update, dictionary witness, source execution,
qualification, corpus measurement, independent MIP, M1, semantic reuse, canonical
action, publication-readiness or promotion claim follows. Gamma intent and the
existing component boundaries are preserved. The next step is review of this
proof and an explicit full-graph algorithm proposal; no corpus runner is part of
this task.
