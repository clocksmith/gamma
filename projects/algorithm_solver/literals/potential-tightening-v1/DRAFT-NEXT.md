# Item 53 execution design: minimum penalties at fixed old potentials

2026-10-24. Design only. This auxiliary document does not change the
[theorem](DRAFT.md), [supplied-DAG oracle](proof.py), its tests, or any item 50
file. No private inputs, new implementation, pending contract, benchmark or
launch is authorized by this document. Implementation and supplied-input
measurement require root approval; a corpus launch additionally requires a
separate frozen contract and Claude review. Item 50 must first have an accepted,
recorded independent report.

## Matched question and exact construction

Measure the gain from tightening old occurrence penalties, holding every old
suffix potential fixed. The two cohorts are the identical original R and naming
300 fit sources from items 28/35/50. The target is `F = 10 C - N`, denominator
`D = 1,000,000`, at most 256 paid exact-string entries, and every support budget
`k = 0,...,256`. A one-owner entry occurs in exactly one distinct source ID;
overlapping occurrences and repetitions do not create extra owners. Characters
are optional paid entries and use the same support classification as other
strings. No source, pool restriction, ownership definition or ban changes.

Reconstruct the exact old graph and its backward distances `d`, including all
suffix positions, from item 28's ordered pool and integer occurrence q. For
every allowed edge `i -> j`, use

```
b(i,j) = 9 if j-i == 1 else -1
q53(i,j) = max(0, d(i)-d(j)-D*b(i,j))
```

The old edges must satisfy `q53 <= q28`. Each old tight successor retains its
cost, every new edge satisfies the same Bellman inequality, and the full graph
therefore has exactly the same distance at every suffix. In particular
`L53 = L50 = L28`. New-only edges are exactly item 50's lift. Tightening is not
a multiplier search, potential update, normalized step, warm-start selection
or optimization across q points.

The theorem's scope stays exact: this is componentwise minimal among
nonnegative multipliers satisfying the fixed-d Bellman inequalities, hence
maximal for that fixed-L certificate; it also maximizes the exact dual among
assignments preserving those actual suffix distances. It does not maximize a
dual family in which actual path distances may rise.

## Input and identity contract

Inherit the exact nine-file private allowlist and cohort-specific five-file
reads from item 50's [freeze](../potential-lift-certificate-v1/FREEZE.md):
original control/scope-joint fit sources and seed dictionaries, the common
original item 28 result, and the two original pool/q pairs. No private item 50
output is needed. No validation,400-source carrier, item35 q, case, protected
file, directory inventory or source execution is added.

The future public-only binder must pin item 50's active contract and accepted
public results, as well as its item28/33/35 and original item13 qualification
authorities. Record item 50's source/pool/q/ban/input-binding digests and complete
257-row arrays before item53 private access. The parent report must be complete,
independently replayed for both cohorts, and have no unresolved failure. Binding
its current bytes is insufficient if the expected accepted-report fields fail.
Pending construction is inactive and reads no private metadata; exact activation
may change only its active flag after review.

At runtime, retain item50's strict signed64, one-dimensional q loading, exact
payload size, Python-int conversion, original occurrence order, old pool order,
seed inclusion, optional96-character accounting, exact learned-extra checks and
source hashes. Old absent characters or absent seed extras have zero weight;
they are not occurring one-owner entries. Removing those zero-weight absent
entries from the full occurring universe cannot change an at-most256 maximum,
but their original pool/seed counts and hashes must still be verified. Existing
accepted parents have zero learned extras; generic completeness checks must
not silently assume this if supplied synthetic inputs contain extras.

Rebuild primitive-arrow, solve-definition/body and whole-source bans through
the unchanged pinned parser. Require identical source hashes, ban digest,
suffix/interval geometry, exact excluded lengths and all source endpoints.
Counts alone do not prove identity. The item35 shape remains R:76,107 characters
and13,553,771 allowed entries; naming:76,033 and13,561,646; both111,543 groups
and966 exact banned occurrences. An implementation must compare the public
parent values, not use these numbers to construct the universe.

Replay the original28 per-program path list in lexicographic string-PID order,
L, original top256 charge, numerator, denominator and ceiling before using any
new result. The unchanged old bounds are R22,196 and naming13,725. Derive d
afresh; do not accept stored production or parent potentials as an authority.
Preserve item50's exact original13 qualification reuse and its separate inherited
item23 exit137 caveat. There are no fresh qualification or witness claims.

## Production calculation and justified reuse

Partition occurring entries into disjoint **old** entries present in the exact
item28 pool and **new-only** entries absent from it. Classify each independently
as one-owner or shared. The old pool's completeness proof implies all shared
entries and occurring alphabet characters are old; one-owner seed extras also
remain old. Assert that fact against the full interval geometry rather than
using it as an unchecked optimization.

Proposed production implementation, entirely in new item53 files:

1. Rebuild old occurrences with a trie in the original sorted-PID/start/end
   order; retain entry IDs alongside their endpoints. Compute old backward d,
   original per-entry weights, original certificate and occurrence-order digest.
2. Traverse those already retained old occurrences once more after d is known.
   Sum `q53` per old entry and verify nonnegativity, `q53 <= q28`, and unchanged
   costs on a retained tight successor at every position. Count old occurrences
   reduced, total multiplier reduction, and old entries whose weight falls.
   Never rematch or materialize old substring copies just to obtain entry IDs.
3. Build the full accepted index once. For each new-only entry use item50's
   unchanged lift formula. Unique-occurrence intervals use endpoint minima and
   exact best-first range splitting. Split around bans and all old exception
   depths; isolate singleton lengths if they could enter an interval. Repeated
   one-owner entries stream all allowed new depths and all their occurrences.
   Maintain separate exact new-only top256 lists by support class, even though
   the shared new-only list is required to be empty for this pool.
4. Merge each class's new-only top list separately with original old weights
   and tightened old weights. These produce the full50 and full53 class tops.
   Every tie uses descending weight then ascending `(group ID, length)`, exactly
   as item50. Retain zeros when required by the occurring class cardinality.
5. Compute all257 exact allocation maxima for both sets of class tops. With
   class prefixes A(one-owner) and B(shared), use
   `T_k=max_j[A(j)+B(min(256-j,m_shared))]` for
   `0<=j<=min(k,256,m_one_owner)`. Break charge ties toward fewer one-owner
   slots, as item50. Report integer bound `ceil((L-T_k)/D)` using integer
   division, including negative numerators.

This reuse is exact: a top256 of any subset is sufficient when selecting at
most256 entries from its union with another subset. A new-only entry outside
its class's top256 cannot displace a retained entry under the same deterministic
tie order. One new-only calculation therefore supports both50 and53 aggregation
within a phase. Reusing item50's **combined** top256 would be unsound: after
old weights fall, a previously excluded new-only entry can become relevant.
Likewise, item50's maximizing allocation or top identities cannot be assumed
to remain maximizing after tightening.

The production adapter should retain old occurrence entry IDs during its own
reconstruction rather than invoke item50's full certificate twice. Do not edit
item50 or monkey-patch its frozen Lift. If old reconstruction is adapted from
its code, disclose that lineage and pin the new copy. The independently checked
original28 certificate remains the authority, not implementation similarity.

## Independent reporter calculation and shared boundary

A new item53 checker adapts the independent50 traversal without changing its
measured file. It reconstructs old occurrences through Aho-Corasick, sorts them
into the authoritative order, computes start-to-end paths by incoming/end-order
relaxation and suffix potentials by forward relaxation on the reversed DAG.
Verify every old Bellman edge and a tight continuation from every suffix. Bind
the complete potential digest between production and replay as an additional
check, not as an input to replay.

After deriving its own d, the checker sums old q and q53 independently, checking
every old occurrence and every old-entry reduction. Its full aggregation streams
**every allowed group depth**, including unique entries. For each new-only
depth it sums the ReLU penalty across all occurrences; no production endpoint
RMQ, interval heap, retained top choices or stored potentials are used. For an
old depth, use its independently summed original/tightened weights and verify
membership/completeness at that depth. Separate bounded sorted top lists and a
separate allocation loop produce both257-row arrays. Stream each new-only depth
once and feed its weight to the two lists; mathematical equality of that term,
not production output, justifies this intra-reporter reuse.

Shared dependencies are explicit: item33's Index and partition/suffix/ban
verifier, original parser code, exact file/dtype/provenance loader, integer
serialization conventions, and the public parent contracts. Production trie/
backward paths and reporter AC/end-order paths remain distinct; support uses
owner-change prefixes versus same-owner-run endpoints. The old-input loader may
be reused only without causing item50 production or its scalar evaluator to run.
The full source/ban/index authority is shared; this is independent scalar replay,
not an independently implemented suffix-array or JavaScript parser proof.

Require equality of old certificate, occurrence digest, every suffix potential,
geometry, class cardinalities, original/tightened old weights' digests, new-only
class top digests, full50/full53 top identities and all514 rows. Production work
counters and reporter work counters differ and are labeled separately.

## Comparison to the independently recorded50 result

Reconstructed50 must match the accepted public50 `bindings_sha256`,
`source_identity_sha256`, `banned_set_sha256`, `parent_certificate_sha256`,
`old_occurrence_order_sha256`, `old_path_terms_sha256`, geometry, class counts,
denominator, L, original28 terms, all257 rows and `top_entries_sha256`.
Use its exact integer/string-key canonical digest convention. Its
`checked_proof_sha256` may also be matched by rebuilding precisely its scientific
PROOF_FIELDS subset; do not compare runtime counters to a different algorithm.
The top digest permits exact identity reconciliation without opening private50
results or publishing source-derived entry IDs.

For every k require `T53_k <= T50_k`, numerator53>=numerator50 and ceiling53>=
ceiling50. Require k0>=old28 bound and k256 equal an independent unrestricted
top256 calculation. Charges are nondecreasing in k and bounds nonincreasing.
Report each exact charge reduction and each integer-bound gain separately:
a strict raw improvement can round to the same integer bound. Report largest
positive k for50 and53; neither a positive bound nor an increased endpoint
proves that the corresponding support class contains a covering dictionary.

## Complexity, limits and required development evidence

Let E28 be the old occurrence count, S28 the stored old pool bytes, T28 attempted
trie transitions, N source characters, G groups, H excluded depths, U new-only
distinct entries and R repeated-new occurrence contributions. Production adds
O(E28) work for tightening and O(number_old_entries log256) for its additional
top merge to item50's old construction and new-only aggregation costs. It keeps
O(E28) occurrence records with entry IDs, not a new full graph. The unique-range
algorithm retains its item50 cost; repeated-new streaming can still cost
Theta(sum n_p squared). This is a worst case of the selected exact traversal,
not a theorem that every possible algorithm must be quadratic.

Reporter streaming visits every allowed depth, so it cannot call itself
subquadratic in the full string universe. It additionally sums each new-only
occurrence and every old occurrence once. Preserve linear-size source/index/
old-graph storage plus bounded top lists; no full new q vector, all substring
bytes or all new occurrence graph is stored. Charge and report index and banned
endpoint storage separately. Do not claim saved asymptotic cost by ignoring
failed trie transitions, repeated overlaps, zero weights, or old-entry mapping.

Proposed frozen envelope is the same as50:600seconds per cohort,1200seconds
for the complete production phase, and a separately invoked1200second report
phase with600second cohort workers. R/core6 and naming/core7, each8GiB address
space and one native numerical thread, subject to root's nonoverlap queue.
All input hashing, parser work, reconstruction, exact aggregation, comparison,
serialization and final publication count. Use literal bootstrap deadlines
before imports/preflight, BaseException deadlines and process-group cleanup.
Normal cleanup fits the phase deadline; one emergency deadline is at most
10seconds from first failure and phase deadline+10, never replenished. Fresh
directories, no retries, no partial promotion and no success before cleanup.

Before any launch, focused supplied-input tests must cover all-edge q53,
unchanged every-suffix distances, strict old reductions with strict bound gain,
reductions with no top-charge gain, raw gain hidden by ceiling, all257 budgets,
one-owner characters, absent alphabet entries, seed extras, primitive-body bans,
tie ordering, and a new-only entry entering after an old top entry falls.
Compare production and reporter against exhaustive tiny graphs/dictionaries.
Adapt the already public item50 invented large fixtures for a separately pinned
complexity check only after root approves it; inherited timing is not new
measurement. Guard and publication tests must preserve the corrected absolute
failure deadlines, and parent50 drift must fail before private reads.

## Acceptance, interpretation and public output

Required acceptance is exact old28/50 reconstruction, identical geometry and
feasible-entry classes, fixed every-suffix d, occurrence/entry dominance,
independent all514-row/top replay and complete bounded receipts for both cohorts.
Any failure invalidates the new result; do not repair by changing inputs, q,
support k, pool or time limits. An incomplete50 comparison blocks publication.

Predeclare these outcomes for the eventual freeze: P1 all required dominance
and identity checks pass (required true); P2 some cohort/k has a strict raw
charge reduction (uncertain); P3 some cohort's largest positive k increases
(uncertain); P4 some cohort has positive unrestricted k256 (uncertain). Report
all257 rows regardless of which outcomes occur. These outcomes do not select a
cohort, budget, q, or follow-up candidate from validation.

A complete zero-gain result means tightening these particular old potentials
does not improve the measured charges; it does not refute changing d or the
larger dual family. A nonpositive unrestricted bound is inconclusive about an
actual representation. A positive bound excludes aggregate C/N<=10% only in
this fixed300-source, paid-entry/support class. No M1, 400/500-population,
held-out, semantic reuse, canonical actions, package, behavior, witness,
dictionary or global dual-optimality claim follows.

Public output is restricted to hashes, counts, timing/RSS, original terms,
all25750/53 numeric row comparisons, reduction statistics and outcome flags.
Sources, q, potentials, entry IDs/strings and per-source derived diagnostics
stay private. Component intent is preserved; no boundary or promotion authority
changes. The next concrete step is review of this design, followed by isolated
item53 implementation and supplied-input evidence, then a separate freeze.
