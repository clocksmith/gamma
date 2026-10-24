# Item 50: potential lift of the item 28 occurrence certificate

2026-10-24. Mathematical design and supplied-input prototype only. No private
inputs, production binder, runner, optimizer, witness search, or launch. The
next decision is whether the exact aggregation method merits a separately
authorized invented complexity measurement. Item 47 remains unchanged.

## Question and fixed scope

Lift the recorded item 28 arbitrary occurrence multipliers to **every allowed
nonempty exact substring** of the unchanged R/naming 300-program fit sources.
Keep the item 35 global whole-source/body bans, optional paid singletons, and
256-entry capacity. Charge every occurrence, including overlapping occurrences.
Classify a paid entry by how many distinct source IDs contain its bytes, not by
chosen paths, number of occurrences, semantic role, or family. All paid entries,
including singletons and unused entries, obey the one-owner count. Absent old
alphabet or seed entries have zero occurrence weight and are outside the full
occurring-substring universe.

Predeclare **all 257 values k=0,...,256**. The former support-budget ladder
0,1,2,4,8,16,32,64,128,256 may be shown as a display subset; it is not a choice
made after seeing private data. There is one exact constructed lift per cohort,
with no q optimization, scaling grid, restarts, fitted choices, or seed upper
bound. The objective remains F=10C-N, where C counts singleton selections and
N counts all selections, excluding Finish. This is an aggregate 10% fraction
relaxation, not canonical encoding, a package optimum, a compactness certificate,
or M1 evidence. Source alternatives and protected populations remain closed.

The [item 49 fixed-q preflight](../support-budget-certificate-v1/README.md)
showed that its two specific q points cannot yield positive bounds. It did not
exclude support-conditioned certificates. The present construction explicitly
retains the already positive [item 28](../all-length-fraction-v1/README.md)
path value while admitting every additional allowed edge.

## Identity and old certificate requirements

A future binding must independently establish equality of the old and full
source maps by exact per-ID UTF-8 hashes, and derive equal whole-source/body ban
sets from those same sources. A shared public cohort name is insufficient.
Rebuild the complete item 28 pool: all allowed shared length>=2 strings, union
all pinned seed learned entries and all 96 optional ASCII/newline characters.
Keep paid characters; there are no mandatory/free graph edges. Verify exact
sorted pool identity, q file hash and integer denominator, and old occurrence
order: sorted source ID, increasing start, increasing end, with the pool ID for
each occurrence. The old integer q is retained **exactly**, including slack
edges. No replacement by smaller potential penalties is proposed.

Replay nonnegative exact integer q values and all old entry sums, shortest
paths, top-256 charge, numerator and published certificate. Every old occurring
edge must be allowed in the full universe; all old suffix positions must reach
the end. ASCII coverage supplies a character edge at every position even though
dictionary selection later pays for that character. An old absent entry may be
dropped from the full universe because its weight is zero. If an old occurring
entry is newly banned, or any source/ban/pool/q identity fails, stop; do not
quietly reinterpret the equality proof as a weaker experiment.

The supplied prototype accepts these objects in memory only. It checks source
hashes, ban equality, q values/length, ordered occurrence digest, old seed and
alphabet inclusion, and shared-pool completeness. It maps old entries to full
suffix intervals and depths; exact shared-entry count equality proves no
allowed shared length>=2 entry is omitted. This does not substitute for a
future pinned private provenance replay or independent source/body-ban parser.

## Exact potential proof

Let D>0 be item 28's integer denominator; b=9 for a singleton, otherwise -1.
For each program let d_i be the exact old backward shortest distance under
cost Db+q28, with d_n=0. Negative longer-edge base costs are harmless in this
acyclic graph. Old Bellman inequalities give

```
Db + q28(i,j) >= d_i - d_j.
```

For each newly allowed occurrence i->j set

```
qnew(i,j) = max(0, d_i - d_j - Db).
```

Every full graph edge now satisfies the same inequality. Along a complete
path, potentials telescope to d_0, so the full path cost is at least d_0. An
old minimizing path consists entirely of retained edges and achieves d_0.
Therefore **every suffix distance**, and in particular the sum L of source
start distances, is exactly unchanged. No full quadratic graph is needed to
establish this: check old inequalities and tight old paths, then apply the
defining inequality symbolically to new edges.

For a full-pool string v define W(v) as the sum of its old/new q over every
occurrence. Nonnegativity implies, for any dictionary V and complete paths,

```
D*F >= L - sum_{v in V} W(v).
```

Let A(j) be the sum of the j largest weights of support-one strings and B(h)
the corresponding shared-string sum, with actual class sizes m1,m2. The exact
maximum charge under capacity256 and at most k one-owner entries is

```
T_k = max_{0 <= j <= min(k,256,m1)} A(j) + B(min(256-j,m2)).
bound_k = ceil((L-T_k)/D).
```

Nonnegative weights justify filling available shared slots, without inventing
missing entries. Ties use fewer one-owner slots; individual entry ties use
compressed group ID then length. These selected entries describe the maximum
charge, not a dictionary witness or packet. The bound is nonincreasing in k.
At k256 the charge is exactly unrestricted full-pool top256, so that endpoint
is a valid full-class lower bound at this specific lifted q, not an optimum.

Every full shared entry already belonged to item 28: shared length>=2 entries
by construction, and shared singletons through the optional alphabet. Its
occurrences and q values are unchanged. Thus T_0<=old_top256 and L=L28, yielding
bound_0>=28's recorded positive bounds 22196 (R) and 13725 (naming), **after
identity and old-certificate replay**. This is a mathematical prediction, not
a newly executed certificate. A positive bound at small k does not prove that
larger k is sufficient, nor that one-owner strings are semantically unreusable.
A unique character can itself make a small-k model infeasible. A nonpositive
bound is inconclusive and says nothing about the maximum over other multipliers.

## Exact aggregation without quadratic stored strings

Reuse the full substring compressed suffix interval/depth representation from
[33](../all-substring-fraction-v1/implicit.py). Each group has the same suffix
occurrence interval for all its depths. Source-ID transition prefixes classify
support in O(1) per group. Remove exact global banned depths. Old weights are
replayed directly and inserted in their class top256 heap, including support-one
seed and singleton exceptions. **No new entry is shared.** Skip all shared
groups when computing new penalties.

For a new length ell in one-owner group I,

```
W(ell) = sum_{(p,i) in I} max(0, d[p,i] + D - d[p,i+ell]).
```

These weights depend on exact endpoints. They are not constant across a group
or one of item 35's length bins; reusing that weighted-selection formula would
be wrong. The prototype handles two cases:

1. **One occurrence:** build static range minima of (d_endpoint, endpoint).
   Split each allowed depth interval around banned and old-entry exception
   depths. A range query gives its maximum weight. Pop the global largest
   candidate, split around its chosen depth, and query the two residual ranges.
   Extract at most256 entries from the union of these ranges. This suffices for
   global top256 even after merging repeated entries and old exceptions. For a
   zero-weight range all depths tie; explicitly choose its first depth.
2. **Repeated occurrences in one source:** stream each allowed new depth and
   sum its exact nonnegative potential penalty across all occurrences. Keep
   only a bounded top256 heap. Do not materialize substrings or edge lists for
   these additions. Overlaps and repeated starts of different lengths count.

The current prototype deliberately uses exact streaming for repeated groups,
not an unmeasured branch-and-bound refinement. A future refinement could use
range minima to upper-bound repeated-group depth intervals, but it is outside
this implementation and cannot be silently added after measurement/freezing.

Let N be total characters, G the O(N) compressed groups, E28 the old occurrence
count, S28 the total bytes in existing old strings, H the number of excluded
depths, and R the number of repeated-one-owner new occurrence contributions
actually streamed. Let U be their number of distinct new entries and T28 the
number of attempted old-trie character transitions. Beyond the existing
suffix-index cost, old trie construction and occurrence traversal cost
O(S28+T28+E28), with T28<=sum_p n_p(n_p+1)/2. This does not claim output-linear
matching: unsuccessful transitions and nonterminal prefixes count too.

Aggregation costs O(N+(G+H+256)log N+(G+H+256)log(G+H+256)
+R+U log256), plus old-weight heap insertion O(number_old_entries log256).
Worst case R<=sum_p n_p(n_p+1)/2. Memory is O(S28+N+E28+G+H+256), with no
quadratic new-string bytes or stored new graph. Computing all257 allocation
maxima adds O(256^2), independent of source lengths. Existing index construction
also retains its explicit banned-end occurrences, charged separately if large.
There is no universal fast-runtime claim: repeated one-owner strings can still
force quadratic work, and future execution must fail closed at its hard cap.

## Verification and next decision

Tiny tests independently enumerate allowed strings, supports, all old/new
occurrence weights, all full suffix distances, exact top entries and dictionary
subsets. They cover overlapping repeated owners, banned depths, absent old
entries, seed exceptions, zero-weight ties, capacities0/3/256, integer rounding,
identity drift, q corruption, pool omission and arbitrary old q preservation.
The unique-occurrence range-minimum implementation is compared to enumeration.

The supplied-input `independent.py` checker uses a separate Aho-Corasick old
occurrence enumerator, forward source paths and reversed-DAG suffix potentials,
and verifies all old Bellman inequalities and one tight edge at every suffix.
It classifies source support by same-owner run endpoints and streams **every**
allowed compressed-group depth, including unique occurrences. A bounded sorted
list replaces the prototype's heap, and a different allocation loop rebuilds
all257 charges. It intentionally shares item33's compressed Index plus its
accepted suffix/interval/ban completeness verifier; the discarded zero-q
scalar from that verifier does not verify the lifted q. This common structural
dependency is explicit. Independent old q/pool private provenance and actual
source/body-ban derivation remain future binding obligations. No optimization
or full new graph construction is needed. Cutoff counts alone are insufficient
evidence; all old terms and all257 new allocation terms must agree.

No complexity benchmark has been run. The owner authorized preparing a pinned
synthetic specification for review, with execution still pending:

- One 300-source, 75000-character fixture: 150 pairs share a 65-character
  random prefix, then each source adds an independent 185-character suffix.
  Fixed generator seed50065; alphabet is the96 item28 characters. This targets
  old-pool/occurrence construction as well as unique-entry aggregation. It does
  not assert an exact pool or occurrence count before construction.
- One 12-source, 12000-character repeated-one-owner stress fixture. Each source
  repeats a source-specific12-character period to length1000, with seed50112.
  This exercises exact repeated-occurrence aggregation and overlaps.
- Both use all96 optional characters as the supplied seed, no learned seed
  extras, and bans containing every complete string plus its `[3:-3]` interior.
  These are invented string bans, not claimed executable source/body examples.
- Rebuild each full old shared pool and every old occurrence. Generate exact q
  by the pinned pid/start/end/pool-ID arithmetic in `synthetic.py`, denominator
  1e6. q has no fitted relationship to the sources or objectives. The q
  generation **algorithm** is pinned before execution; its realized vector hash
  is computed during the timed reconstruction, rather than doing an unmeasured
  preliminary pool/q run. Source and ban hashes are pinned before measurement.
- One whole180-second guard on core6,8GiB, with external180-second timeout and
  kill-after10 seconds. Both fixtures, index/old replay, both aggregation cases,
  all257 charges, the independent all-depth replay with exact agreement, and
  the small independent exhaustive oracle suite are inside
  this envelope. Imports/preflight are included in the external guard. Retain
  timing, peak RSS, trie transitions, exact aggregation work and failure phase.

`synthetic.py --pin` prepares only hashes of code, interpreter/runtime and
invented source/ban generation; it does not construct a pool, q or path.
`--run` requires separate review and authorization. No production budget is
proposed from this specification. A timeout is retained as a feasibility
failure, not silently shortened data or a truncated pool. No corpus runtime is
inferred from item 28 or item 35 timings.

Component intent is preserved: fixed-source literal evidence, exact paid-entry
accounting, independent claim scope and closed protected populations. No
component boundary or production behavior changes are proposed.
