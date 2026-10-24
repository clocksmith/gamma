# Item63 entry-price owner path cap

Status: mathematical proposal and explicit tiny supplied-input oracle only. No private input, scalable implementation, price search, binder, complexity measurement or original-fit run is authorized. This refines the owner-only item57 mechanism. It does not combine item60 joint caps, item61 required owners or item62 required-owner/joint path caps.

## Fixed quantities

Fix a finite source population, exact allowed substring universe and exact bans. Give every allowed occurrence a nonnegative integer penalty q; every occurrence must be represented. Let D>0 be the integer denominator. The relaxed path value L is the sum of minimum complete-path costs with edge cost D*base+q, where base is9 for a singleton and−1 otherwise. q and L remain unchanged throughout this construction.

An entry is one-owner when it occurs in exactly one original source. For one-owner entry e belonging to p, let m_e>0 count **all allowed occurrences**, including overlapping occurrences and zero-q occurrences. Let W_e sum its original q over all occurrences. A_p(t) is the prefix sum of the t largest original W_e among p's distinct entries, with finite counts and canonical ties; only t<=min(B,m_p) is required. R_p(0) is the maximum sum of q on nonoverlapping one-owner intervals in p, allowing free skips and every allowed one-owner interval. Item57 uses f57_p(t)=min(A_p(t),R_p(0)).

Absent entries have no owner and no positive occurrence count. They must not acquire fake ownership or create finite marginal slots. Unused paid entries still consume dictionary capacity; omitting their zero contribution only relaxes the bound.

## Price removal lemma

Supply a finite sorted distinct family Λ of nonnegative **integer** prices containing0. The mathematical validity holds for any such fixed family; a future experiment must freeze its family and budgets before inputs. For each λ and each one-owner entry e, set

    a_e(λ) = floor(λ / m_e)
    qλ(p,i,j) = max(q(p,i,j) − a_e(λ), 0).

This residual is used only to bound owner penalty. It does not replace q in L, shared activation weights or A_p.

Consider any nonoverlapping owner intervals from a complete path, using at most t distinct one-owner entries. For each used entry e, the removed penalty is

    sum_used_occurrences min(q_occurrence, a_e)
        <= number_used_occurrences * a_e
        <= m_e * floor(λ/m_e)
        <= λ.

Summing over at most t used entries gives removal<=λt. The residual penalty is at most R_p(λ), the maximum nonoverlapping residual schedule over **all** allowed one-owner intervals, with free skips. Therefore

    Q_owner,p <= λt + R_p(λ).

This is valid when t counts all selected owner entries, including selected but unused entries. Shared intervals in the complete path cause no problem: deleting them leaves nonoverlapping owner intervals with gaps, and free skips cover those gaps in the upper-bound schedule.

Using ceil instead of floor, undercounting occurrences that can remove positive penalty, or omitting positive low-ranked arcs from R can invalidate the inequality. Counting all allowed occurrences is the definition of this protocol. A separately specified variant could safely count only positive-q occurrences: zero-q arcs remove nothing, so that count still bounds the number of positive-removal terms (with explicit handling of entries whose count is zero). That variant is not implemented or evaluated here. For example, source `aa`, banned whole `aa`, both singleton penalties1, m_a=2 and λ=1: ceil(1/2)=1 removes2 even though the entry charge is only1. The false residual bound would give1 for a path with owner penalty2. The correct floor is0.

## Concavity, finite allocation and domination

Define on the finite owner prefix domain

    f63_p(t) = min(A_p(t), min_{λ in Λ} [λt + R_p(λ)]).

A_p has nonnegative decreasing marginal increments, so its linear interpolation is nondecreasing and concave. Each price expression is affine with nonnegative slope. The pointwise minimum of these concave functions is concave: its hypograph is the intersection of convex hypographs. It is also nondecreasing because every constituent is nondecreasing. At integer arguments, f63 has nonnegative decreasing increments. In particular f63_p(0)=0 because A_p(0)=0. Flooring affects the constant R_p(λ), not the slope in t, so it does not break this argument.

The λ=0 candidate has a_e=0 and R_p(0)=Rone57_p. Thus f63_p(t)<=f57_p(t) pointwise. The result does not depend on a special q53 geometry; arbitrary supplied nonnegative integer q is supported. No strict q53 example is asserted here.

Allocate j real owner-entry slots across sources by taking the j largest marginal increments of these finite concave prefixes. Stable owner/rank ties preserve prefix closure, including zero increments. This gives the exact relaxed allocation optimum U63(j), rather than an arbitrary upper estimate. Retain at most B owner slots globally but never truncate the arcs in any residual schedule.

Let H(s) be the sum of the s largest original activation weights among shared entries, capped at their finite count. Then

    T63(k) = max_{0<=j<=min(k,B,total_owner_entries)} [U63(j) + H(B−j)].

Every covering dictionary with at most B paid entries and at most k one-owner entries has total path penalty Q<=T63(k). Its full relaxed path cost is at least L, hence

    D*F >= L − Q >= L − T63(k),
    F >= ceil((L−T63(k))/D).

The domain includes j=0; no required-owner lower bound is imposed. The exact finite allocation and pointwise f63<=f57 give T63(k)<=T57(k) for every k. Charges are nondecreasing in k; lower bounds are nonincreasing. Negative numerators use exact mathematical ceiling. None of these numerical statements supplies a covering dictionary or proves that a budget class is nonempty.

## Strict example with an existing covering dictionary

Use sources p=`aaabX` and s=`aXb`, ban both whole sources, and assign q=10 to every allowed occurrence of `aa`, `ab` and `bX`; all other allowed penalties are0. Set D=1, B=4 and Λ=[0,6]. The characters `a`, `b`, `X` are shared. The relevant entries `aa`, `ab`, `bX` belong only to p.

Entry `aa` has two overlapping occurrences and W_aa=20. Entries `ab` and `bX` have one occurrence each and weight10. R_p(0)=20, attained by `aa` followed by `ab`, or the other `aa` followed by `bX`. At λ=6, the two `aa` residuals are7 and the `ab`/`bX` residuals are4, giving R_p(6)=11. Consequently

    f57_p(1)=20,
    f63_p(1)=min(20,20,6+11)=17.

All shared weights and s's owner penalties are0. At k=1, T57=20 and T63=17. The fixed relaxed value is L=16, so the lower bound increases from−4 to−1. This is a strict raw and integer gain but remains nonpositive and inconclusive about the target.

The paid dictionary {`a`,`b`,`X`,`aa`} covers both sources and contains exactly one one-owner entry, so this example's strict k1 comparison is not an empty-class artifact. It does not prove the pricing correction is necessary or optimal, nor that the lambda family is best. It is a constructed general fixed-q example, not a corpus result or a q53 result.

## Proof-oracle boundary and tests

`proof.py` imports unchanged57's explicit tiny full-graph oracle for L, ownership, original activation prefixes and baseline. The new residual schedules enumerate every allowed owner interval and retain their vectors/penalties. Price choice is supplied; there is no search. The code deliberately stores all intervals and is not suitable for corpus use.

`test_proof.py` independently enumerates all nonoverlapping interval subsets, all covering dictionaries up to B, every complete encoding path and all finite owner allocations on tiny inputs. It checks each price-removal inequality, every residual maximum, exact allocation, original relaxed path value and weak duality, including unused paid entries. Cases cover the strict coverable example, all low-ranked arcs, overlapping/zero-q occurrences, floor-versus-ceil failure, lambda0 identity, no-owner populations, zero capacity/ties, random tiny populations and invalid/missing/fake/bool/negative inputs. Optimized Python is explicitly refused.

A later scalable proposal must preserve all-occurrence counts, full residual schedules, exact identity/bans and finite prefix semantics, disclose shared dependencies and independently verify every recurrence. It needs separate root authorization, a frozen finite price family and budget, supplied-input implementation/measurement, and new original-fit approval. No execution permission is implicit in this proof.
