# Item 66: price every entry across all source paths

Mathematical-only draft, 2026-10-24. This is a separate refinement of the
character-fraction certificate, not an item63 owner-price implementation or
measurement. Component intent is preserved: exact allowed substrings, complete
paid dictionary cardinality, fixed source geometry and existing M1 gates remain
unchanged. No private input, source changes, qualification, corpus experiment,
price-grid fitting or scalable kernel is authorized by these files.

## Fixed objects and target

Fix nonempty finite source strings indexed by distinct source IDs, a global set
of banned exact strings, and every allowed occurrence `(source,start,end)` of
every nonempty substring. A banned string has no allowed occurrences anywhere,
including when it occurs inside another source. Let `q_o` be a nonnegative
integer for **every** allowed occurrence, including those with zero penalty.
The input must contain exactly these occurrences; missing, fake, banned,
negative or boolean values are rejected.

A dictionary contains at most B distinct paid strings. Each source has one
complete forward path using its entries. Paths cannot use a particular source
occurrence twice. Distinct source IDs count separately even when their strings
are identical. An entry can occur many times in one source and across sources.
All these possible occurrences count, including overlapping occurrences that
cannot simultaneously lie on a path.

Write Q for the total original q penalty of the chosen paths. As in the prior
certificate, fix positive integer D and define

```
F = 10 C - N
L = sum_p min_complete_path sum_o [D * (9 if length(o)=1 else -1) + q_o].
```

Thus `L <= D*F + Q` for any dictionary and its covering paths. A bound `Q <= T`
implies `F >= ceil((L-T)/D)`. Integer ceiling is `-(-(L-T)//D)`, including for
negative numerators. No dictionary, path or coverage witness follows merely
from a positive lower bound; an empty dictionary class also satisfies it
vacuously. The tiny oracle requires the unrestricted allowed graph to cover
all sources, but does not assume that B entries can do so.

## Global multiplicity lemma

For every occurring allowed entry e let

```
m_e = number of ALL allowed occurrences of e across ALL source IDs
      (shared and one-owner, overlapping and zero-q occurrences included).
```

For a nonnegative integer price lambda, define

```
a_e(lambda) = floor(lambda / m_e)
r_o(lambda) = max(q_o - a_e(lambda), 0).
```

For each source p, `R_p(lambda)` is the maximum sum of residual penalties on
any nonoverlapping set of allowed arcs, with free skips. It includes every
allowed entry, not just one-owner entries or highly ranked entries. Free skips
relax the requirement to cover; they do not provide free encoding actions.

For a fixed dictionary and all its chosen source paths, let `U_e` be the set
of used occurrences of e. It is a subset of the m_e allowed occurrences. Then

```
sum_{o in U_e} [q_o-r_o(lambda)]
  = sum_{o in U_e} min(q_o, a_e(lambda))
 <= |U_e| * a_e(lambda)
 <= m_e * floor(lambda/m_e)
 <= lambda.
```

Summing over selected entries removes at most `lambda * |dictionary|`, which
is at most `lambda * B` since lambda is nonnegative. The used residuals in each
source form a permissible nonoverlapping schedule. Consequently

```
Q <= G(lambda) = lambda * B + sum_p R_p(lambda).
```

The entry charge is paid **once globally**, not once per source. In particular,
using within-source multiplicity for a shared entry can undercharge removal.
Replacing floor with ceiling can also violate the bound. The chosen protocol
counts all allowed occurrences; it is sufficient without claiming that this is
the only mathematically possible safe denominator. An entry with no allowed
occurrences contributes no used penalty and needs no division. Unused entries
still consume paid dictionary capacity; ignoring them in the removal sum does
not grant free slots. Unused or nonoccurring dictionary entries can be dropped
without changing any chosen path and without increasing cardinality. Therefore
exhaustive tests over occurring allowed words cover every useful dictionary;
the original lambda*B bound remains valid even if unused entries are retained.

## Finite prices and explicit baseline combination

Supply a finite sorted distinct family Lambda of nonnegative integer prices
including zero. The theorem oracle evaluates exactly that family, with no
adaptive additions, tuning or grid search. Since every price bounds the same Q,

```
G = min_{lambda in Lambda} G(lambda)
```

is valid. Ties choose the smaller price only to make the receipt deterministic.
At zero, the new bound is the sum of **all-entry** maximum schedules. It is not
the item57 owner/shared allocation and is not the item63 owner-price bound.
There is no equality or universal domination claim for zero price or for the
uncombined global family.

If an existing certificate T_old bounds the same Q for the same fixed q,
allowed geometry and feasible dictionary class, `min(T_old,G)` is safe. The
prototype computes the unchanged tiny item57 certificate and, for every
one-owner budget k, returns

```
T66(k) = min(T57(k), G).
```

The global bound applies to all B-entry dictionaries, so it also applies to the
subclass with at most k one-owner entries. This explicit minimum establishes
weak domination of item57. It does not require assuming G itself dominates
item57 or item63. Combining with another valid same-q bound, including item60
or item63, is mathematically safe but is not silently performed by this API.
Different q systems cannot have their Q charges mixed; independently valid
lower bounds could instead be compared as lower bounds.

The k curve remains nondecreasing in charge and nonincreasing in lower bound,
as inherited57 charges are nondecreasing and G is constant in k. A negative
bound is inconclusive about the character gate, not a violating dictionary.
A finite price family need not span a penalty range to be valid; range adequacy
would be a separate diagnostic, not an assumption in this proof.

## Strict covering examples

These are supplied fixed-q mathematical examples, not q53 instances, optimized
potentials or corpus measurements. Attainment is asserted only where an
explicit dictionary and path calculation establishes it below.

1. **Positive price improves the new zero-price bound.** One source `abab`,
   whole source banned, B=1. Give q=10 only to occurrences `(0,1)` (`a`),
   `(1,3)` (`ba`) and `(3,4)` (`b`), and zero to every other allowed arc.
   Prices `[0,2]` give charges30 and28. The entry `ab` covers the source.
   Item57 already gives10, so the combined result stays10; this is not a gain
   over item57.
2. **Zero price alone can improve item57.** Two separate sources `abc`, whole
   source banned, B=2. Give q=10 to every `ab` and `bc` occurrence, zero
   elsewhere. All entries are shared. Item57's charge is40, while the global
   zero-price charge is20 because the two positive arcs overlap in each
   source. Dictionary `{a,bc}` covers both and has Q=20. With D=3 the resulting
   integer bound is16, exactly the example's F; this invented identity is not
   an M1 or corpus result.
3. **Positive price can improve both item57 and item60.** Two separate sources
   `aaabaaab`, whole source banned, B=1. Give q=10 to every `aa` occurrence,
   q=5 to every `b` occurrence, and zero elsewhere. Global counts are
   `m_aa=8`, `m_b=4`. Item57 gives80. Both item60 and the new zero-price bound
   give60. At lambda16 the residuals are8 for `aa` and1 for `b`; each source's
   maximum residual schedule has value18. Thus the new charge is
   `16 + 18 + 18 = 52`, strictly below both baselines. The single entry `aaab`
   covers each source twice, with Q=0. L=-6 at D=1, so the resulting lower
   bound is -58: strict improvement, still no positive certificate. The
   unchanged tiny item60 oracle explicitly confirms its charge60. This is an
   example-specific comparison, not universal domination of item60 by G.

Conversely, with two separate `ab` sources, no bans, B=1, q=1 on every singleton
and zero otherwise, the zero-price global charge4 exceeds item57's2. The whole
entry `ab` covers. This tests why the baseline minimum must be explicit.

## Prototype and independent exhaustive checks

`proof.certificate(texts,banned,q,lambdas,capacity=256,denominator=1)` enumerates
the complete tiny allowed graph and global counts. It evaluates residual
interval scheduling by end-position dynamic programming, with a free-skip
transition at every position. It returns all occurrence rows/residuals,
list-indexed price schedules and caps, each price's charge and ceiling, the
selected global bound, the inherited57 certificate and combined k rows.
List-indexed prices avoid introducing integer dictionary-key axes. This is
not a corpus representation or a resource-qualified execution path.

The only implementation dependency is the unchanged item57 **tiny** proof
oracle for L and its baseline bound. The new global counts and scheduling do
not call item63. Tests separately enumerate every allowed nonoverlapping
interval schedule, every dictionary up to B, and every joint choice of complete
paths for every covering dictionary. They verify the per-entry removal lemma,
all residual schedule positions, every price charge, the global minimum,
combined weak duality, exact positive and negative ceilings, and complete
unrestricted shortest paths. The explicit item60 oracle is an additional
comparison in the third example, not a production dependency.

Seven focused tests passed in0.126 seconds. They include the three distinct
strictness examples, twelve deterministic random tiny two-source populations,
shared overlapping/zero-q counts, global bans, iterator normalization, unsafe
ceil/local-count counterexamples, empty B=0 classes, and rejected missing/fake/
banned/bool/negative inputs and optimized Python. Both files compile/import.
The tests do not establish corpus runtime, scalability, qualification, a
positive full256 certificate, or a dictionary witness. No frozen ancestor or
item63 file changed. No private inputs, pins, measurement or Git action occurred.
