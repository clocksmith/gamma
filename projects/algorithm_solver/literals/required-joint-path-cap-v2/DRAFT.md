# Item 62: required owner slots inside joint path caps

2026-10-24. Mathematical proof and tiny supplied-input oracle only. No private
inputs, production kernel, corpus design, complexity measurement, pins, binder,
runner or launch. This combines the mathematical mechanisms of
[item 60](../joint-path-cap-v1/DRAFT.md) and
[item 61](../required-owner-cap-v1/DRAFT.md) under identical sources, global bans,
ownership, fixed nonnegative integer q, denominator D and full-DAG minimum L.
Existing records and measured files remain unchanged. Gamma's goals and
CATSCAN authority are preserved; no component boundary or gate changes.

## Quantities and required slots

For each source p, let A_p(t) be the sum of the largest t all-occurrence weights
of allowed one-owner entries owned by p. Let Rone_p and Rall_p be maximum
nonoverlapping q sums over, respectively, all allowed one-owner arcs and all
allowed arcs in p. Free skips are permitted in those scheduling bounds.
For s shared slots, S_p(s) is the sum of the largest s local all-occurrence
weights of globally shared entries; H(s) uses their global weights. All finite
prefixes saturate at actual availability. Singletons are paid and classified
by distinct source owners; repetitions in one source do not create sharing.

Let P* contain the sources with no complete shared-only segmentation, using
every allowed shared entry without a slot limit. Put r=|P*|. Every covering
dictionary must select at least one distinct one-owner entry for each p in P*.
Private-character detection is not a substitute for this reachability test:
global bans can force an owner even when all its characters occur elsewhere.
Require a complete full-allowed-graph path; otherwise the tiny oracle rejects
the input rather than inventing a finite L. Absent entries can be removed from
a dictionary without changing its paths and do not enter occurring counts.

For total one-owner slots j and shared budget s=B-j, define

    g_p(t;s) = min(S_p(s) + A_p(t), Rall_p)
    f_p(t)   = min(A_p(t), Rone_p).

Both are nondecreasing concave finite sequences; g_p(0;s) can be nonzero.
Use the same required allocation set for both:

    T_j = { t : sum_p t_p=j,
                1<=t_p<=m_p for p in P*,
                0<=t_p<=m_p otherwise }.

Here m_p is the number of real occurring one-owner entries. Top B prefixes
suffice for relevant t, but scheduling must retain every allowed arc. The
defined j range is r<=j<=min(B,sum m_p). Each such j is achievable as a finite
numerical allocation if every forced owner has an entry; this does not assert
that a covering dictionary exists at j or within B slots.

## Exact numerical allocation and same-split combination

Define Jreq(j)=max over T_j of sum_p g_p(t_p;B-j), and retain item 61's
Ureq(j)=max over T_j of sum_p f_p(t_p). Evaluate

    C62(j) = min(Jreq(j), H(B-j) + Ureq(j))
    T62(k) = max C62(j), for r<=j<=min(k,B,sum m_p).

The two terms are combined at the **same j**, before taking the maximum. The
maximizing allocations for the two terms need not agree; each independently
bounds the same actual dictionary/path penalty, so their minimum is valid.
This is not a claim that a common dictionary realizes both relaxed maxima.

For exact Jreq allocation, start t_p at 1 for forced owners and 0 otherwise.
Its mandatory baseline is

    sum_{p not in P*} g_p(0;s) + sum_{p in P*} g_p(1;s).

Equivalently add g_p(1;s)-g_p(0;s) for forced owners to the all-owner zero-slot
baseline. Do not add entire g_p(1;s) on top of an already counted shared
baseline. A zero first-slot increment still consumes one real mandatory slot.
Residual marginal sequences start at rank 2 for forced owners, rank 1 otherwise.
Their increments remain nonnegative and nonincreasing. Taking the largest j-r
residual increments attains the exact maximum: every allocation selects at
most that sum, and descending value followed by source ID and rank makes the
selected set prefix-closed, including ties and zero values. The same reasoning
applies to Ureq. The oracle sorts all finite residual increments explicitly;
it makes no scalable implementation or memory claim.

Because increments are nonnegative, the equivalent at-most-j numerical
allocation has the same value whenever j is in the defined finite range.
No imaginary zero-weight entries extend that range. For k<r, output explicit
emptiness with null charge/numerator/integer bound, not a finite certificate.
For k>=r, the necessary owner condition still need not imply coverage.

## Weak duality and dominance

Take any covering dictionary with at most B entries and at most k one-owner
entries, and any complete paths using it. Remove absent entries. Let t_p count
its selected one-owner entries for p and j=sum t_p. Required owners give
t in T_j and j>=r. Its actual used shared q in p is at most S_p(B-j), and its
used one-owner q is at most A_p(t_p); the total in p is also at most Rall_p.
Therefore actual total Q<=Jreq(j). Independently item 61 gives
Q<=H(B-j)+Ureq(j). Hence Q<=C62(j)<=T62(k).

The full-DAG minimum satisfies L<=D*F+Q for F=10C-N, where N counts selections
and C counts singleton selections. Thus

    F >= ceil((L-T62(k))/D).

This applies to every complete path, with no canonical/min-N policy assumption.
The advancing DAG permits negative base costs; nonnegative q is essential to
the entry/schedule upper bounds. Integer ceilings are exact for positive or
negative numerators.

Required allocations are subsets of item 60's allocations, so for each defined
j, Jreq(j)<=J60(j) and Ureq(j)<=U57(j). Therefore

    C62(j) <= min(J60(j), H(B-j)+U57(j)) = C60(j).

Taking the maximum over the restricted j range yields T62(k)<=T60(k), since
60 may additionally consider j<r. Also C62(j)<=H(B-j)+Ureq(j), so taking the
same range maximum gives T62(k)<=T61(k). Both lower bounds therefore weakly
improve for every k>=r. Below r the result is an emptiness proof instead.
As k grows in its defined range, T62 is nondecreasing. If no owners are forced,
62 equals 60; without shared entries, 62 equals 61. Strictness is not universal.

Shared entry identities remain independently relaxed across sources in S_p.
The per-source choices need not fit one globally shared dictionary; retaining
the H+Ureq term is still necessary. Required first slots constrain their owner,
not which literal is chosen or whether that literal actually repairs coverage.
This is an exact finite numerical relaxation, not exact dictionary optimization.

## Strict fixed-q example with a covering dictionary

Use sources `abc`, `abd`, `xyyx`, `zz`, `xx`, globally banning their full strings.
Set D=1, singleton q=0 and every longer allowed arc of length l to q=9l+1.
This is fixed item-53-form q: original shared-plus-character edges have q=19
on `ab` and q=0 on characters; suffix distances remain 9 times remaining length,
and the full extension gives exactly these q. L=126.

With B=6 and k=4, forced owners are the first four sources. The same comparison is:

| Bound | Penalty charge | Integer F lower bound |
|---|---:|---:|
| Item 60 | 76 | 50 |
| Item 61 | 104 | 22 |
| Item 62 | 66 | 60 |

The dictionary `{a,bc,bd,x,y,z}` covers all five sources and has exactly four
one-owner entries (`bc`,`bd`,`y`,`z`). Thus this strict comparison is at a known
feasible owner budget. Its paths have N=12, C=10 and F=88: the bound 60 is not
attained by this witness. Scaling all q and D by three preserves the integer
result. Exhaustive tests enumerate every covering dictionary of at most six
entries from this tiny 15-entry allowed pool and every path through each.

The record also checks independent interval subsets, every finite required
allocation, the nonzero mandatory baseline, zero/tied increments, bans forcing
owners without private characters, no-forced null behavior, r>B, necessary-but-
insufficient coverage floors, random tiny graphs and malformed inputs.

No original-fit conclusion, performance estimate, new q optimization, source
execution, qualification, packet witness, M1, semantic-reuse proof or promotion
follows. Any later supplied kernel, measured protocol or original-fit question
requires separate design and authorization.
