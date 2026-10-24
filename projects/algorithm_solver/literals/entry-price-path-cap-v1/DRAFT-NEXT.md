# Item63 supplied-input implementation proposal

Design only. Root authorized this document, not implementation, pinning, measurement, private reads, binder or launch. Preserve the recorded theorem/proof/tests and all ancestor files. This proposal refines owner-only57 with fixed entry prices; it does not merge60,61 or62.

## Fixed baseline and price family

Use the exact original28 sources, bans, occurrence penalties and potentials to reconstruct the unchanged50/53/57 scientific baseline. The penalties used by63 are the same fixed q53 on every allowed occurrence:

    q53(p,i,j) = max(0, d_p(i) − d_p(j) − D*base(i,j)).

The old relaxed potentials d, relaxed path value L, denominator D, original shared activation weights H, owner activation prefixes A and finite owner counts do not change. Reconcile the complete accepted57 scientific proof and both50/53 paired proofs. The simplest initial implementation should call unchanged57 production/checker for their respective full baseline, then construct a separately charged potential/index context for63. Reuse an existing context only through a separately reviewed interface proving the same quantities; do not monkeypatch57 or call duplicated construction free.

The candidate price family is fixed globally for every owner and every supplied fixture:

    Λ / D = [0,1,2,4,8,16,32,64,128,256,512,1024,2048,4096,8192].

There are exactly15 prices, equivalently [0]+[2**r for r in0..13], multiplied by D using integer arithmetic. This is not an input-optimized family, does not estimate a source-dependent scale and does not add prices after observing results. The dyadic grid may miss useful intermediate prices or be too small/large for some counts; lambda0 still guarantees nonweakening of57. This family is a bounded diagnostic choice, not a claim of optimal pricing. In particular the existing theorem's general fixed-q toy is not evidence of q53 or original-fit gain.

For each entry e, the denominator m_e counts **all** allowed overlapping occurrences, including zero-q occurrences. A separate positive-q-only denominator can also have a valid proof, but is outside this protocol. At each price use floor(lambda/m_e), never ceil. All residual schedules include every allowed one-owner arc, not only dictionary/top entries.

## Exact multiplicity from compressed suffix groups

The unchanged33 Index partitions all nonempty substring entries into compressed suffix groups. Each group g has a suffix-array interval [lo,hi), depth interval [first,last] and excluded whole-entry lengths. Every entry at an allowed depth in that group occurs at exactly the hi−lo suffix starts. Therefore

    m_e = hi − lo

independently of the entry's depth inside the group. This is occurrence multiplicity; `group['multiplicity']` instead counts allowed **distinct lengths/entries** and must never be used as m_e.

Global exact-string bans remove the whole entry, so they do not partially reduce m_e at an allowed depth. This argument would not apply unchanged to position-specific occurrence bans. Source-terminal boundaries remain part of the index construction. A one-owner group has exactly one source ID across its complete suffix interval, even when its suffix starts repeat many times in that source. Zero-owner paid alphabet/seed extras do not occur in the full index, get no denominator and create no owner marginal slots.

### Production: laminar parent/terminal structure and per-start depth walk

Do not expand groups into permanent per-start lists: the sum of interval widths can be quadratic. Instead derive one O(G)-size numeric parent structure from the existing groups:

1. Sort group IDs by (lo,−hi). The intervals are laminar and nonempty; keep structural groups even when every depth is banned. Use a virtual root of depth0 and [0,N). A genuine first-level group may have that same interval as the virtual root; handle it explicitly rather than requiring strict containment against the virtual root.
2. Use a stack to assign the smallest containing structural parent. Verify interval containment and `child.first=parent.last+1`, using root depth0. Distinct genuine groups cannot share the same interval under the current Index contract. Preserve original group IDs and depth/exclusion metadata.
3. Sweep suffix ranks with nested interval start/end events to identify the deepest active group for each suffix terminal. Verify that its last depth equals that rank's source-truncated remaining length. Build the existing (source,start)↔rank mapping once. These checks prevent a terminal suffix that prefixes a longer suffix from being treated as an ordinary leaf.
4. For one source start, walk terminal→root, reverse the transient chain, then discard it after that start. Its positive-length depth segments partition1..remaining without overlap or gaps. Classify support independently of bans using the checked owner interval. For one-owner groups belonging to this source, m=hi−lo is constant over the segment; inspect all candidate depths, excluding exact banned lengths/endpoints. Shared segments need no owner schedule updates.

The chain length is at most the suffix's remaining length. Across all source starts, transient group visits V are at most the total number of raw substring occurrences E=Σ n_p(n_p+1)/2. No binary search or O(log N) lookup is performed for each priced occurrence. Permanent state is parent/terminal/rank arrays plus the unchanged index; only a single O(n_max) chain is transient. A cache keyed by distinct m values may hold the15 exact quotients floor(lambda/m); there are at most G such keys. Count cache construction/quotient work explicitly.

### Forward schedules by start, without an edge graph

Process each source's starts in increasing order and keep one prefix vector r_lambda for every price. All r vectors start at0. At start i, all predecessors of i have already propagated their offers, so r_lambda[i] is final. First propagate the free skip to i+1, then inspect the depth segments above and offer

    r_lambda[j] = max(r_lambda[j],
                      r_lambda[i] + max(q53(i,j)−floor(lambda/m),0)).

The start-order traversal is a topological relaxation of exactly the usual end-order recurrence; no future source value is consumed before its predecessors. Shared q/m/depth work is done once per allowed owner arc, with the15-price loop inside the arc loop. Compute q53 once, use the group quotient cache, and retain zero residuals in the accounting. Do not truncate arcs or opportunistically drop a price. Lambda0's complete vector must equal the freshly reconstructed57 owner-only forward vector, not just its final cap.

This organization permits per-start counts/segments and O(15n_p) schedule state without a dense start×length matrix or materialized full substring/edge graph. Retaining all final source/price vectors for later independent replay costs O(15N), disclosed separately from baseline vectors and index state.

## Independent counts: per-start Z matching

Use a different algorithm for multiplicities, rather than reconstructing the production parent/terminal map. For each source p and start i, form numeric symbols

    ord(text[i:]) + [-1] + ord(text)

where−1 is absent from all Unicode code points. Run a fresh linear Z matcher. For each position in the second copy of the source, its Z value is the longest match to text[i:], capped by the pattern length and remaining source length. Histogram these match lengths, then suffix-sum the histogram. At every depth l, the suffix sum is the exact number of overlapping within-source occurrences of text[i:i+l]. This needs O(n_p) transient numeric state and work per start; discard it before the next start. It does not construct substring strings for each depth or store counts for all starts.

The independent57 reconstruction already proves which entries are one-owner and that all shared entries are present in the old pool. Recompute its support/longest-shared-prefix authority through fresh old-entry AC matching and full33 partition/support checks. For a one-owner arc, within-owner occurrence count equals global m_e, so Z provides the required denominator independently of group interval width. For shared arcs this equality need not hold; they are excluded by the independently established owner filter. Exact banned endpoints come from a fresh banned-word AC traversal, checked against the full index.

Also compare every old one-owner entry's Z count with its fresh global AC occurrence count. This detects old-singleton/seed-extra and overlapping-match errors without trusting the group width. New entries use the same all-depth Z computation and independent ownership proof; no missing-new-entry exception or inferred count is allowed.

Commit the complete count stream without storing it as an edge graph. For each (source,start), hash canonical increasing-depth records `(end,m)` for every allowed one-owner arc, encoded as compact ASCII JSON `[end,m]` followed by one newline, with integers in ordinary decimal form and no spaces. An empty start stream hashes the empty byte string. Retain one hash and arc count per start; combine them in sorted source/start order. Production and checker must agree on these commitments, total arcs, source counts and all inherited full-class/support identities. Hashes bind the complete count traversal; the checker still independently computes counts rather than accepting the hashes as evidence by themselves.

The production group's width rule and the checker's Z rule should additionally agree entry-by-entry with explicit substring matching in tiny tests. A full field of group identities need not be attached to every production arc. The shared33 index and support verification remain disclosed dependencies; Z count recovery itself does not use its occurrence widths.

## Independent backward schedules and every forward recurrence

The checker processes starts in descending order, endpoints in ascending order, with its per-start Z vector, fresh q53 and exact bans. For every price,

    b_lambda[i] = max(b_lambda[i+1],
                     max_allowed_owner_j residual_lambda(i,j)+b_lambda[j]).

All residuals are nonnegative and skips remain free. Keep backward vectors separately from production forward vectors. Caps require b_lambda[0]=r_lambda[n] for all sources and prices, with lambda0 agreeing with the independent57 baseline.

Verify every production forward recurrence in the same streamed endpoint pass, without retaining edges or rerunning Z. Validate supplied r vectors' integer shape and r[0]=0. Initialize an audit vector at end j with the supplied free-skip value r[j−1]. For each allowed owner arc i→j, accumulate

    audit_lambda[j] = max(audit_lambda[j], r_lambda[i]+residual_lambda(i,j)).

After all starts are processed, require audit_lambda[j]=r_lambda[j] at every positive j. Although accumulation visits starts backward, it merely gathers all terms of each forward recurrence; all values on the right are the supplied vector. The acyclic recurrence and r[0]=0 make equality at every position a complete verification of that vector. Thus one independently derived residual can feed both the backward update and forward-recurrence audit. Count both candidate evaluations and all15N checked positions. Do not describe this as an independent recount of the baseline if baseline reconstruction was skipped.

## Prefixes, allocations and retained proof

Retain all15 caps per owner. For every finite t<=min(B,m_p), compute

    f63_p(t)=min(A_p(t), min_lambda[lambda*t+R_p(lambda)]).

Verify nonnegative nonincreasing increments, f(0)=0 and f63<=f57 for every owner/rank. Preserve the actual finite owner count; unused/absent entries do not pad prefix domains. Production can use a next-marginal heap and the checker a full stable marginal sort or explicit owner scan. Both retain exact choices, shared prefixes and all257 rows with smaller-j ties, fixed L/D, monotone charge and exact ceiling. No forced-owner lower bound or joint shared cap is inserted.

Record cap tables, price family, prefix values/commitments, all count commitments, both schedule commitments, every allocation/curve and separate new/baseline work counters. Public metadata may contain the price constants, aggregate counts, numeric curves, times and hashes; source strings, entry identities and per-owner schedules remain private in any later original-fit run. A supplied-input synthetic record may expose its invented numeric tables, but that does not create a public-source policy for corpus artifacts.

## Complexity and explicit counters

Let P be the source count, N total characters, G compressed groups, K=15, V total transient ancestor-group visits, E=Σ n_p(n_p+1)/2 raw endpoints, A' one-owner endpoints before bans and A allowed one-owner endpoints after bans. Let M be the number of distinct occurring one-owner multiplicities, with M<=G. Keep baseline reconstruction costs separate.

Beyond the new inherited index/potential context, production parent/terminal preparation uses O(G log G+N) work and O(G+N) state. Count generation/traversal and schedule work is O(V+A'+K*A+K*N+K*M), with V<=E and A'<=E. Quotient cache state is O(K*M); price schedules/retained audit vectors are O(K*N). Local depth-chain state is O(n_max). Prefix generation costs O(K*P*B); heap allocation is bounded by finite PB marginals and capacity B, with no all-entry identity expansion. These bounds count arithmetic operations; arbitrary-precision integer costs and the inherited index implementation are separate.

Independent per-start Z matching/histograms cost O(Σ n_p²)=O(E) work and O(n_max) transient state. Scanning all endpoint lengths and computing both backward/audit candidates costs O(E+K*A+K*N), with two candidate computations per priced arc explicitly counted. The full15 forward vectors and checker vectors cost O(K*N). Old AC matching, exact ban matching, independent57 reconstruction, support/index verification and final allocation are separate reported work. No O(N²) cross-population matching or per-arc logarithmic occurrence query is proposed.

Required counters include groups/terminal checks, V, candidate owner depths, allowed/banned owner endpoints, multiplicity-cache entries/divisions, q evaluations, per-price residual and forward updates, Z input symbols/comparisons/histogram cells, checked old AC counts, per-start count records, backward/audit candidates, checked forward positions, prefix evaluations and allocation work. Expected structural identities must hold exactly; counters are not performance claims.

## New tiny oracles before any measurement

Before preparing a measurement spec, add focused supplied-input tests for:

- Every entry's explicit all-source overlapping count versus group width, production depth segments and Z suffix sums, including all-equal sources, terminal suffixes that prefix other suffixes, distinct-owner ties, one-owner singletons, absent seed/alphabet entries, zero-q occurrences and whole banned depths.
- Parent/terminal gap/overlap and source-end rejection; corruption of a group width or a terminal depth must fail. Independent Z uses−1 and verifies counts on arbitrary tiny Unicode symbols even though any eventual original source contract stays unchanged.
- Exact original AC counts and original q occurrence order; missing old shared entries, incorrect support and malformed counts fail closed.
- All15 prices, exact integer scaling/floors, repeated-entry denominators larger than some prices, zero residual clipping, lambda0 complete-vector identity, all low-ranked owner arcs and every backward/forward recurrence against exhaustive interval subsets.
- Both allocation implementations against complete tiny owner allocation and covering-dictionary/path oracles, with finite zero ties, no-owner sources, B=0 and exact negative ceilings.
- Corrupt one intermediate production recurrence, one count commitment and one local price cap independently; matching final maxima alone must not rescue the error.

## Eventual invented envelope and later gates

After separate root approval of a new supplied-input implementation and tests, propose the exact same two original public invented fixtures used by50/53/57: the300×250 paired65-prefix fixture and12×1000 repeated-owner fixture, preserving the original generators, seeds, q inputs and historical baseline comparisons. No adaptive shrinking, preliminary corpus probe, selected subset or changed price family is permitted. Run fixtures sequentially in one proposed600-second whole-job budget oncore6,8GiB per process, including imports, preflight, all new tiny oracles, original fixture construction, both kernels, comparisons and success publication. Failure gets one absolute cleanup budget of at most10 seconds, bounded by original deadline+10; process groups are killed before blocking failure I/O. This is a new resource proposal, not permission to run or a prediction that it will finish.

The measurement must reconcile every historical57/53/50 scientific field and every new count/cap/prefix/allocation/row, with complete per-price recurrence verification. Retain duplicate reconstruction work and peak memory, not a matched speed ratio against prior runs. An incomplete budget result remains incomplete with no verdict. Only afterward could a separate reviewed original-fit design bind the exact original nine inputs and accepted predecessor receipts. No pending contract, source read, optimization, semantic qualification, packet, M1, current-best or promotion claim follows from this document.
