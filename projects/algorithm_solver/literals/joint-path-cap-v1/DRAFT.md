# Item60: jointly cap shared and one-owner path penalties

2026-10-23 EDT. **Mathematical proof and tiny supplied-input oracle only.** No private input, corpus measurement, production algorithm design, binder, pending contract or execution protocol. This follows the joint-cap suggestion in [item57](../owner-path-cap-v1/DRAFT.md) without changing any prior fixed-q result, implementation or source population.

## Fixed quantities and the claim

Use the same full allowed substring occurrence DAG, exact global source/body bans, original distinct-source ownership, nonnegative integer occurrence penalties q, positive integer denominator D, unchanged suffix distances and summed unrestricted path minimum L as57. The proof applies to any such q, including fixed53penalties. All character entries are paid and classified by actual source support. Repetition within one source does not make an entry shared.

Each actual complete encoding uses a dictionary of at most B entries, at most k of which have exactly one distinct source owner. Shared entries have at least two owners. Every source must be covered; there is no free character fallback. An entry with no occurrence can be omitted without changing its paths or cost; omitting it can only relax the upper capacity constraint.

Let F=10C−N, with base cost9 for a singleton occurrence and−1 for a longer occurrence. N excludesFinish. Edge cost is D times base plus q. Let Q be the penalty sum of the actual used occurrences across all source paths. The new charge bounds **Q**, not the dictionary's sum of penalties over all its activated occurrences. The latter may exceed this path cap.

The proposed joint charge is valid and never exceeds57's charge at any support budget k. Its per-source entry allocation is exact for a stated relaxation. It is not an exact optimization of a globally consistent dictionary, a feasible witness or an M1 result.

## Per-source ingredients

For entry e, define local all-occurrence weight

    w(e,p) = sum of q(a) over every allowed occurrence a of e in source p.

Absent occurrences contribute zero. The global weight is w(e)=sum_p w(e,p).
For a one-owner entry owned by p, these two weights coincide.

For each source p:

- S_p(s) is the sum of the largest s local weights w(e,p) among globally shared entries. It clamps to the finite number of shared entries; missing entries are not invented. Absent local entries can be retained with their actual zero weights or omitted without changing the value.
- A_p(t) is the sum of the largest t all-occurrence weights of entries owned only by p. A_p(0)=0, and t cannot exceed that owner's actual finite entry count m_p.
- Rall_p is the maximum total q of a nonoverlapping set of **all allowed occurrences** in p, shared and one-owner together. Half-open intervals may touch. Free skips are allowed in this auxiliary schedule; it need not cover the source, respect a dictionary or limit entry count. Those are explicit upper-bound relaxations, never decoding freedoms.

Retain the57quantities Rone_p, the analogous one-owner-only schedule maximum, H(s), the global shared top-s entry prefix, and

    U57(j) = max sum_p min(A_p(t_p), Rone_p)
             over t_p >= 0, t_p <= m_p, sum_p t_p <= j.

All weights are nonnegative. Prefixes are nondecreasing with nonincreasing increments. Zero-valued real entries remain part of finite count accounting; an absent entry is not interchangeable with an extra zero slot.

## Path bound at a fixed split

Take an actual dictionary with j one-owner entries and j_p of them owned by p, so sum_p j_p=j. There are at most s=B−j shared entries. Within source p, its actual used shared penalties are at most S_p(s): the chosen globally shared entries are a particular subset of at most s entries, each used at most its full occurrence sum. The used one-owner penalties are at most A_p(j_p). Therefore

    Q_p <= S_p(s) + A_p(j_p).

The entire actual path is nonoverlapping and uses only allowed occurrences, so Q_p<=Rall_p as well. Consequently

    Q_p <= g_p(j_p;s) = min(S_p(s) + A_p(j_p), Rall_p).

This joint cap excludes double charging overlapping shared and one-owner opportunities that57bounds separately. It applies to every actual encoding path, not only a minimum-F, minimum-N or canonical path.

Shared choices are deliberately independent across p in S_p. Different sources may select different top-s entry sets in this relaxation, even though one real dictionary must choose a single shared set. The expression is an upper bound on Q, not an attainable shared-entry assignment.

## Exact relaxed owner allocation

For a fixed s, g_p(t;s) is nondecreasing and discretely concave in integer t. Adding the constant S_p(s) preserves the prefix increments; capping at Rall_p leaves unchanged increments before crossing, one possibly reduced crossing increment, and then zeros. If the baseline already reaches the cap, every increment is zero.

The baseline matters:

    g_p(0;s) = min(S_p(s), Rall_p),

which generally is not zero. Define

    J(j) = max sum_p g_p(t_p; B−j)
           over 0 <= t_p <= m_p, sum_p t_p <= j.

For this fixed j/s, begin with sum_p g_p(0;s), form each owner's finite marginal sequence g_p(t;s)−g_p(t−1;s), and add the largest j available marginals. These marginals are nonnegative and nonincreasing within each owner. Sorting by descending value, then owner ID, then rank makes the selected marginals prefix-closed, including zero and tied values. Thus the unconstrained top-j upper bound is attained by a feasible prefix allocation. A heap of the next available marginal per owner implements the same order.

For the j values used below, j<=sum_p m_p, so enough real entries exist to attain exactly j marginals if desired. The at-most and exactly-j maxima are equal because all increments are nonnegative. The implementation still retains finite counts and never pads missing entries. This proves exactness **only for the numerical per-source relaxation J**, not for simultaneous dictionary/path realization.

Each relevant t_p<=j<=B. The top B one-owner weights per owner and top B local shared weights per source determine all needed prefixes. However Rall_p must still include **every allowed occurrence**, including entries outside those top lists. Omitting low-ranked arcs from a schedule can lower its cap below an actual path and is unsound. No inherited global top256 list determines either all local shared prefixes or full schedules.

## Combining with57 and weak duality

For a fixed split j, item57 independently gives

    Q <= C57(j) = H(B−j) + U57(j).

The joint relaxation gives Q<=J(j). Both inequalities hold for the **same actual j**, so define

    C60(j) = min(J(j), C57(j)),
    T60(k) = max_{0 <= j <= min(k,B,sum_p m_p)} C60(j).

Take the minimum at each split before maximizing across splits. No monotonicity in j is assumed: increasing j also decreases shared allowance. If maximizing charges tie, report the smaller j deterministically. As k grows the maximization domain only expands, so T60(k) is nondecreasing.

For every dictionary/path collection in the fixed source/support class, its actual split belongs to that domain and Q<=T60(k). The full allowed DAG shortest-path minimum satisfies

    L <= D*F + Q,
    D*F >= L − Q >= L − T60(k),
    F >= ceil((L − T60(k))/D).

Negative base costs are harmless because every source graph is acyclic; q, not the base cost, must be nonnegative. Integer ceilings use exact arithmetic, including negative numerators.

Pointwise C60(j)<=C57(j). Hence T60(k)<=T57(k), with unchanged L,D, and both raw and integer lower bounds cannot worsen. They may tie. This is a dominance theorem, not an empirical claim about either recorded cohort. A positive bound excludes F<=0 only in the named fixed-source/support class, which may have no covering dictionary. A nonpositive bound says nothing about other multipliers, source alternatives, representations or larger populations.

## Strict invented example at fixed53 penalties

Take p=`abc`, q=`abd`, ban the two whole strings, B=3 and D=1. Start with the character-only q=0 distances d_p(i)=9*(3−i). Apply the fixed53potential rule q(i,j)=max(0,d(i)−d(j)−base(i,j)). Singletons get0, and every allowed length-two occurrence gets19. The unrestricted distances remain unchanged and L=54.

Shared entry `ab` has global weight38. Owner-only `bc` and `bd` each weigh19. Item57's one-owner caps are19 per source. At k=2 it charges H(1)+U57(2)=38+38=76, giving integer lower bound−22. Those two kinds of arcs overlap within each source: `ab` cannot coexist with `bc` or `bd` on the respective path.

Rall is19 for each source. The joint charge is38 for all feasible splits, so T60(2)=38 and the new bound is16. Dictionary `{a,bc,bd}` covers both sources with two selections each, one singleton each: total N=4,C=2,F=16. The exhaustive oracle confirms this equality and all other covering dictionaries/paths. This is a nonvacuous strict **toy** improvement. Scaling D and q together by3 preserves the integer result and exercises rational/integer accounting. It does not estimate any corpus effect.

## Why the57minimum remains necessary

Take two sources both `ab`, ban `ab`, and allow the shared singletons. Give p's `a` occurrence penalty10 and `b` penalty0; give q's `a` penalty0 and `b` penalty10. With s=1, each local top-one sum is10 and Rall is10 in each source. The joint relaxed shared baseline is therefore20, choosing `a` for p and `b` for q. But a single global shared entry can collect only10 across sources: H(1)=10. The minimum with57retains that global coupling information and lowers the final charge to10.

The example illustrates the relaxation's distinct shared choices; it does not claim a one-entry covering dictionary exists. Calling J an exact dictionary optimum would be false. Removing the57minimum would remain a valid bound but could weaken57, contrary to the intended dominance claim.

## Supplied-input prototype and checks

[proof.py](proof.py) explicitly materializes every allowed substring occurrence and its full q mapping for tiny supplied strings. It computes both schedule recurrences by endpoint, unchanged shortest-path distances, local/global weight prefixes, stable exact allocations at each split, and all k=0..B charges and ceilings. It has no corpus loader, production adapter, runtime campaign or invocation contract. Explicit occurrences can be quadratic and substring bytes cubic in source length; the per-split allocation is repeated intentionally for clarity. This oracle is not a scalable full-pool algorithm proposal.

[test_proof.py](test_proof.py) independently enumerates interval subsets, all finite owner allocations, tiny dictionaries and every complete path. It verifies the per-source inequality, exact relaxed maxima, pointwise minimum, dominance, k monotonicity, L, and weak duality/ceilings for every covering case. Six focused tests pass, including18deterministic tiny random pools, the strict fixed53example, shared coupling, repeated occurrences, shared singletons, zero weights/baselines, finite counts, capacity0/excess capacity, stable ties, missing/negative/bool q, uncovered full graphs and optimized-Python rejection. Test elapsed time is a development check, not a complexity measurement or corpus forecast.

Component intent is preserved: exact paid entries, fixed sources/q and explicit ownership, independent small oracles, retained prior results and conditional claims. This establishes no new corpus bound, witness, semantic reuse, action compression, qualification, M1, novelty, publication readiness or promotion. A production design would require a separate task and review; none is proposed here.
