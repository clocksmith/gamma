# Item68: require owner slots inside priced-prefix caps

Mathematical-only draft, 2026-10-24. This combines the two constraints inside
the allocation, while preserving exact fixed sources, global bans, q, paid
entry capacity and the existing character-fraction objective. It does not
change either ancestor, authorize private data or define a scalable corpus
implementation, price search, run, freeze or promotion.

## Fixed quantities and the coverage requirement

Use the complete allowed exact-substring occurrence graph and nonnegative
integer q from the unchanged tiny item57/61/63 proofs. Every global banned
string is excluded at every occurrence. Sources have distinct IDs, even if
strings coincide. Capacity B and the one-owner budget k count distinct paid
entries. Shared entries occur in at least two distinct sources; a one-owner
entry occurs in exactly one source. Occurrence counts include overlaps and
zero q, while actual paths are nonoverlapping complete source paths.

Let `A_p(t)` be the sum of the t greatest full-occurrence weights of entries
owned by p, for finite ranks `0..min(B,m_p)`, with `A_p(0)=0`. Let H(s) be the
sum of the greatest `min(s,m_shared)` shared-entry weights. H always uses the
**same actual owner count j** through H(B-j); it cannot be optimized with a
different split from the owner allocation.

Compute shared-only reachability for each entire source, using all allowed
shared strings. Let F be the sorted set of sources not coverable this way and
r=|F|. Every dictionary covering all sources needs at least one one-owner entry
owned by each p in F: otherwise that source's path would use shared entries
only. Different forced sources require distinct entries, since a one-owner
entry cannot serve two sources.

Thus k<r is an empty covering class. Those rows carry an explicit empty flag
and null charge, numerator, bound and deltas. For k>=r there is a defined
numerical bound, but coverage need not exist: the floor is necessary, not
sufficient. In particular, one paid entry per forced source does not always
cover all its private characters. This proof uses general shared reachability,
not the special private-character equivalence established for another fixed
population. When r>B, every retained row is empty.

## Priced prefixes and mandatory slots

Fix a supplied finite sorted family of nonnegative integer prices including
zero, without fitting it to an experiment. Item63 establishes for every source
and finite entry count t the bound

```
f_p(t) = min(A_p(t), min_lambda [lambda*t + R_p(lambda)]),
```

where R is the maximum nonoverlapping owner-only residual schedule after
subtracting `floor(lambda/m_e)` from each occurrence and clipping at zero.
Its m_e counts every allowed occurrence of that one-owner entry. These are
not item66's global shared-entry prices. No new residual or occurrence rule is
introduced here.

Each finite f_p has f_p(0)=0 and nonnegative nonincreasing marginal increments.
This follows from item63's concave top-weight prefix and finite affine minimum;
its continuous piecewise-linear extension is nondecreasing and concave. Because
zero price is included, `f_p(t) <= f57_p(t)=min(A_p(t),R_p(0))` pointwise.
All values are exact integers.

For exact total owner count j, define

```
U_required_priced(j) = max sum_p f_p(t_p)
subject to sum_p t_p=j,
           1<=t_p<=min(B,m_p) for p in F,
           0<=t_p<=min(B,m_p) otherwise.
```

Reserve one slot for every forced owner and initialize its value to f_p(1).
A mandatory value of zero still consumes its slot. For a forced owner the
remaining marginals start at rank2; for another owner they start at rank1.
Take the greatest remaining marginal increments, respecting within-source
prefixes, until exact j is reached. Since increments are nonincreasing, stable
sorting by decreasing increment, source ID, then rank is an exact optimizer.
Equal-valued earlier ranks precede later ranks from that same source, including
zero increments. The finite lists are never padded with fake entries.

This gives exact values for all j from r through
`min(B,sum_p min(B,m_p))`. The chosen tiny implementation reuses item61's
unchanged constrained-allocation helper with the newly supplied f_p arrays;
the tests separately enumerate all finite allocation tuples.

## Certificate and domination of both predecessors

For a dictionary with exactly j owner entries, actual owner penalties in p
are at most f_p(t_p), and its at-most B-j shared entries contribute at most
H(B-j). Every covering dictionary satisfies the mandatory constraints above.
Therefore, for k>=r,

```
T68(k) = max_{r<=j<=k, j<=B, finite available ranks}
           [H(B-j) + U_required_priced(j)]
```

bounds its total q penalty. Ties choose the smaller j. With the unchanged
relaxed path value L, positive integer denominator D, and F_objective=10C-N,
weak duality gives

```
L <= D*F_objective + actual_q_penalty
F_objective >= ceil((L-T68(k))/D).
```

The code uses exact `-(-(L-T)//D)` for negative as well as positive numerators.
The symbol F for the forced set above is unrelated to this integer objective.
Finish actions are not added to the inherited objective.

Two separate comparisons hold for the same q, geometry and budgets:

1. **Versus61:** at every feasible mandatory allocation, f_p<=f57_p. With the
   same j and H(B-j), its charge cannot exceed item61's constrained optimum.
   Maximizing over the same j range proves T68(k)<=T61(k).
2. **Versus63:** every mandatory allocation is an allowed unconstrained63
   allocation. Item63 also maximizes over all j<=k, including the required
   range. Consequently T68(k)<=T63(k).

Thus T68(k)<=min(T61(k),T63(k)) on the defined domain. With shared L and D its
integer lower bound is at least the maximum of those two lower bounds. Merely
taking the public bound maximum is already valid, but need not be as strong
as enforcing both constraints in one allocation. The comparison is not made
numerically below r; those classes are empty. As k increases through the
defined range k>=r, the charge is nondecreasing and the bound nonincreasing.

Unused/nonoccurring dictionary entries can be dropped without changing paths
or increasing either budget, so exhaustive tests over occurring allowed words
cover useful dictionaries. Mandatory slots cannot be dropped in this way:
each is justified by the source's actual shared-only coverage failure.

## Strict covering examples

Both examples use general supplied q, not reconstructed q53. Their strictness
does not predict a fixed-original-input result or price-family adequacy.

### Strict against both at the minimum feasible owner budget

Sources are p=`aaabXY`, s=`aXb`, z=`zz`. Ban each whole source globally. Let B=5,
D=1 and prices `[0,6]`. Give q=10 only to p's occurrences of `aa`, `ab`, and
`bX`; all other allowed occurrence penalties are zero.

All occurrences of a, b and X are shared. Private Y forces owner p and private
z forces owner z, so r=2. Dictionary `{a,b,X,Y,z}` covers all three sources with
exactly two owner entries, proving that k=r is feasible for this example.

For p, the unpriced cap is20, f57_p(1)=20, f63_p(1)=17, and f63_p(2)=20.
For z, its mandatory first-entry value is zero. At k=2:

| Calculation | Allowed use of the two owner slots | Charge |
| --- | --- | ---: |
| 61 | One for p, one for z; unpriced cap | 20 |
| 63 | Both may be assigned to p | 20 |
| 68 | One for p, one for z; priced cap | 17 |

The same split leaves three shared slots, all with zero q weight. L=24, so the
integer lower bounds are4,4,7 respectively. This is a strict positive tiny
certificate beyond the maximum of the predecessor bounds. It is not an
attainment claim, a q53 result, an M1 result or evidence on the corpus. A
zero-valued mandatory slot is essential to the accounting, not a free slot.

### Nonzero mandatory baseline

Sources p=`aaabX`, s=`aXb`, z=`zz`, with all whole sources banned, B=4 and prices
`[0,6]`. Use the same positive p penalties, plus q=1 on each z singleton;
other penalties remain zero. Only z is forced and its mandatory value is2.
Dictionary `{a,b,X,z}` covers all sources with one owner entry. At k=2 the
charges are22 (61),20 (63),19 (68). Tests use D=3 here to exercise exact ceiling
and separate raw charge improvement from rounded bound improvement.

## Tiny API, verification and scope

`proof.certificate(texts,banned,q,lambdas,capacity=256,denominator=1)` returns
both complete tiny predecessors, the forced set/reachability/counts, mandatory
value, exact constrained priced prefixes and choices, and all combined rows.
It first computes item63 and item61 from identical normalized inputs and
requires exact equality of their complete item57 baseline quantities. No
ancestor receipt with different q, L or allowed strings is substituted.

Dependencies are explicit: unchanged `required-owner-cap-v1/proof.py`, including
its constrained allocation helper, and `entry-price-path-cap-v1/proof.py`, both
of which use unchanged item57 tiny quantities. They are mathematical oracles,
not scalable execution authority. No ancestor file changed.

Six focused tests passed in0.145 seconds; both new Python files compile/import.
Tests independently enumerate every nonoverlapping owner interval schedule at
each supplied price, every finite owner allocation, every dictionary up to B,
and every joint complete path tuple for every covering dictionary. They check
both strict examples, mandatory zero and nonzero slots, shared-only coverage,
global banned singletons, overlapping occurrences, exact L, both domination
claims, raw and integer deltas, null classes and negative nonintegral ceilings.
Sixteen deterministic random tiny populations supplement the fixed examples.
Missing/fake/banned q edges, negative and boolean values, invalid budgets/prices,
consumed ban iterators and optimized Python are rejected or handled as declared.

No private data, corpus probe, scalable implementation, pending contract,
measurement, Git action, source qualification or current-best change is part
of this task. A later execution design needs its own authority and review.
