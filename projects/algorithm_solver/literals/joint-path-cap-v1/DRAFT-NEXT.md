# Item60 production proposal: local shared prefixes and all-arc schedules

2026-10-23 EDT. **Design only.** No production implementation, private input, binder/pending, complexity measurement or corpus run is authorized. Preserve the mathematical DRAFT/proof/tests and all57/53/50files. The next permissible implementation step needs separate root approval; measurement needs a separately reviewed pinned supplied-input specification, and any original-fit run needs a new freeze and cross-review.

## Fixed authority and reused baseline

Keep57's fixed53penalties, original source and ban identities, original occurrence order, ownership, denominator, suffix potentials d and L. Derive q53 on each allowed occurrence by

    q53(p,i,j) = max(0, d_p(i) − d_p(j) − D*base(i,j)).

For old edges, this is the exact53tightening, not the original loaded q. For new edges it is the same potential extension. Do not optimize, scale, refit or substitute penalties. Reconstruct and reconcile the accepted50/53proofs and accepted57owner tops, counts, caps, allocation, full257curves and commitments. No private57output is an input. A later binding would preserve the original allowlist and accepted public57authority, not add a new source population.

The simplest reviewable initial implementation would call unchanged57`caps.check` for its complete baseline, then create a separately charged unchanged53`Tighten` context for the new local shared and all-arc calculations. This duplicates structural/potential reconstruction; disclose its work and memory rather than calling the baseline free or independent. It avoids changing frozen57or introducing an unreviewed shared-state interface. Only if separately justified could a new isolated factoring share the context while proving byte-identical57baseline receipts. Either way, the57scientific baseline is explicitly reused; independent60checking must reconstruct it through57's independent authority rather than trust production output.

Do not merge item61's required-owner constraint into60. The item60formula retains all j from0through min(k,B,total owner entries). Combining mechanisms would be a separately named question.

## Local shared weights without a shared-substring graph

Accepted50authority proves every occurring globally shared entry is already in the original pool, including shared singletons. Recheck this completeness against the full structural index: the set/count of old shared `(group,length)` identities must equal the full allowed shared class, with exact bans and occurrence ownership. A missing shared entry is a failed authority check, not a reason to use an incomplete S_p. Classify support by distinct original source IDs; absent paid alphabet entries do not become occurring entries, and repeated occurrences do not create shared ownership.

Stream every original-pool occurrence from the checked original occurrence traversal. For an entry classified shared, compute its q53from d and add it to a per-source, per-entry integer accumulator. Never use the global shared weight as a local weight, skip zero-penalty occurrences from counts, or use only global topBentries. Process one source's accumulators at a time, then discard them after constructing that source's bounded topBlist. The existing original-pool strings/trie and occurrence carriers are allowed inherited state; do not materialize a new all-shared substring string/edge graph.

Each local list is ordered by descending local all-occurrence weight, then57's `(group,length)` identity. Positive entries outside the global shared topBcan belong to a source's topB and must be considered. Shared entries absent from that source have local weight zero, but are still real globally available entries. To reproduce finite canonical zero ties without a dense source-by-shared-entry matrix:

1. Aggregate every shared entry actually encountered in this source; count all positive resulting entries and retain their topBwith the fixed tie order.
2. If at least B positive entries exist, the list is complete.
3. Otherwise all positive identities fit in the bounded set. Fill to min(B,m_shared) from globally shared identities in ascending identity order, skipping those positive entries. Those selected zero-weight entries may be absent locally or occur only with zero q. At most2Bidentities need inspection in this branch before filling, unless the finite global list ends sooner.

Keep exact global shared count and local encountered/positive counts, occurrence counts, ordered top identities/weights and prefix commitments. Check that summing local weights across sources reproduces each inherited tightened shared entry weight; this can use one global numeric vector indexed by original entry ID, not new substring bytes. Its global topBmust equal the accepted57/53shared prefix. This reconciliation checks completeness and accounting but cannot replace the local top calculation.

Production storage is inherited index/trie/old occurrences plus a per-source numeric accumulator, a global shared identity/weight vector and O(PB)local prefix/top storage. No P-by-M_shared dense matrix or full new-edge graph is required. These are proposed explicit-state bounds, not observed memory usage.

## All-arc schedule and independent recurrences

Compute Rall forward for each source using only its prefix vector and checked banned endpoints:

    r[0]=0
    r[end]=max(r[end−1],
               max_{start<end, allowed} r[start]+q53(start,end)).

Unlike57's one-owner schedule, do not apply the longest-shared-prefix ownership filter. Every allowed shared or one-owner occurrence is inspected, including entries outside every top list. Keep the free skip and nonnegative q; do not use negative base costs directly as schedule weights. Count all inspected endpoints and admitted occurrences, with separate shared/one-owner counts if obtained from independently checked ownership. No source substring string need be created inside this loop.

An independent checker reconstructs old occurrences with fresh AC/end-order traversal, source ownership, exact banned endpoints and suffix potentials. It computes a backward all-arc schedule

    b[n]=0
    b[start]=max(b[start+1],
                 max_{end>start, allowed} q53(start,end)+b[end]).

Require b[0]=r[n], while retaining separate vector commitments: forward and backward vectors are not expected to be identical. Independently verify **every** recorded production forward recurrence from the checker's fresh q and bans, in addition to checking every backward recurrence. A single equal maximum is insufficient. This may require another full endpoint traversal; count it explicitly. The schedule work remains quadratic in source length in this first proposal. No full-DAG edge/string materialization or implicit range shortcut is assumed.

For local shared weights, the checker independently aggregates fresh AC occurrences by source/entry. It may use a numeric vector over all shared old entry IDs for one source, then a full stable sort, rather than production's bounded heap/zero-fill. Compare every local top identity, finite count and prefix digest. The common structural index is an explicit shared dependency; occurrence matching, local summation, scheduling direction and allocation implementation remain independent.

## Efficient per-split allocation

Retain57's exact owner topBprefixes A_p, finite owner entry counts, Rone caps, U57(j) and H(s). New input is local S_p(s) and Rall_p. For each feasible j, set s=B−j and baseline

    G0(j)=sum_p min(S_p(s),Rall_p).

Then initialize at most one next-marginal heap entry per owner. Compute each marginal directly from A_p(t), S_p(s) and Rall_p; no full function matrix is necessary. Pop at most j entries with the fixed owner/rank tie order. This gives J(j). Take `min(J(j), H(s)+U57(j))`, then running maxima over j for all k. Preserve finite available slots, zero marginals and the smaller-j tie rule.

Production can therefore use O(BP+B squared log P) allocation work beyond stored prefixes and O(P) active heap memory, without storing all257byPbyBfunction values. An independent checker can use a simple scan over owners for the next largest marginal, costing O(PB squared) across all splits, or explicitly flatten/sort each split's finite marginal sequences. The scan has a different implementation from the production heap and avoids a repeated large sort. It must check every derived capped-prefix increment against the direct formula and verify concavity/nonnegativity; a straightforward full check across257splits,300owners and256ranks is about19.7million integer comparisons/arithmetic operations, not a runtime estimate.

Store per-split baseline, exact joint/57/min charges, selected owner/rank increments or their complete commitments, finite allocation counts and all257final rows. Reconstruct discarded intermediate function values in the checker. Avoid a retained257×P×BPython-object matrix. Assertions include same L/D, unchanged57baseline, pointwise minimum validity, T60<=T57, monotone charge in k and exact negative/positive integer ceilings.

## Required supplied-input evidence before any measurement

A new kernel and independent checker must agree with the existing tiny exhaustive oracle on raw local weights, local and owner top identities, all schedules, every recurrence, finite counts, every per-j allocation and all257budget rows. Include the strict fixed53shared/one-owner overlap example, the shared-coupling counterexample, repeated occurrences, locally zero/absent shared entries, topBlocal entries outside global topB, stable ties, banned endpoints, non-ASCII source handling only if inherited contracts admit it, and insufficient shared/owner entry counts.

Explicitly test a low-ranked arc necessary to the correct Rall, so top-list truncation cannot pass accidentally. Test a malformed original pool missing a shared entry, wrong occurrence order, wrong support class, wrong q53versus original q, corrupted d or one altered recurrence; each must fail rather than produce a bound. Test both allocation implementations against complete tiny owner allocation enumeration, including nonzero baselines and an owner already saturated at t=0.

Only after code/spec review could a separately pinned invented complexity harness use the two original50/53/57public fixtures and supplied original q, reconstruct every baseline, compare all60production/checker quantities and count the duplicate baseline/context work. Keep fixture identities and outputs fixed; no adaptive shrink or preliminary corpus probe. Any time/memory budget, cores and process cleanup contract belong to that later reviewed harness, not this proposal. Historical timings are not a matched speed comparison.

## Interpretation and later gates

A successful supplied-input implementation would establish correctness only on its checked invented inputs and resource envelope. A later original-fit protocol would still need public source/pool/q binding, exact accepted57reconciliation, full private allowlist, explicit failure dominance, bounded production/replay and independent review before launch. It would report raw and integer improvement separately, all k, and known coverage-feasibility boundaries without treating k or a positive bound as sufficient evidence of a feasible class.

There is no new qoptimization, source change, witness, source execution, qualification, validation/protected access, current-best comparison, M1 or promotion in this question. New60results, if ever authorized, must be separate from the unchanged57baseline and from any61required-owner result.
