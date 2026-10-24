# Item49: conditional support-budget certificates

2026-10-24, design and supplied-input prototype only. No execution contract,
corpus loader, binder, optimizer, witness search or launch is authorized here.

**Preflight disposition:** stop before complexity benchmarking or corpus work.
Independent public-metadata review proved that both proposed q points give
nonpositive bounds at every k, without computing any support-budget trajectory.
See [README](README.md) and [public-preflight.json](public-preflight.json).
The derivation below remains valid; its proposed fixed-q experiment is not
informative for positive exclusion. Support-specific q optimization is untested
and would require a different design, not an implicit extension of this one.

## Question and population

For each of the two unchanged item35 fixed **300 fit source** populations
(R and naming), can a dictionary of at most256 paid literal entries achieve
`F = 10C - N <= 0` if at most k entries occur in exactly one distinct fit source?
`C` counts singleton selections and `N` counts all literal selections, excluding
Finish; actions are `N + 1` per program. This is the same fraction relaxation as
35. It imposes no compactness gate. The definition counts **all paid entries**,
including unused entries and singletons; it is not a count of owners in chosen
paths, occurrences, families, or semantically reusable components.

The universe is exactly35's nonempty occurring substrings, with its unchanged
whole-source/body exclusions, optional paid characters, and256 capacity. An
absent character is not a free fallback. All repeated occurrences within one
source still give support one; identical bytes in two distinct source IDs give
support at least two. Source spelling, population and bans remain fixed.

This is conditional representation evidence only. It does not establish M1,
exclude the full400 or500 population, establish semantic reuse, or constrain
other sources, typed representations or dictionaries outside the defined model.
A nonpositive bound is inconclusive, not a positive witness. Positive bounds
at small k do not show that allowing more one-owner entries is sufficient.

## Original fixed proposal, stopped at public preflight

Use k in `(0,1,2,4,8,16,32,64,128,256)`, and exactly two q points per population:
all zero, and the exact recorded-best item35 integer q with its denominator.
No multiplier optimization, rescaling, data-dependent ladder, extra q point,
source probe, validation input or qualification is proposed. Report both q
curves and their pointwise maximum, preserving every result. Later binding must
identify35's accepted independent evidence, exact source/ban/index identities,
recorded q digest and denominator. No private binding is performed in this draft.

## Proof

Let U1 be allowed words occurring in exactly one source, and U2 those occurring
in at least two. Every allowed word belongs to exactly one class. Let D be a
positive integer denominator. For each occurrence e, of word v at source p/start
s, set nonnegative integer multiplier `q_e = q[p,s,length_bin(v)]`. Its base
integer cost is `b_e = 9` for a singleton, otherwise `-1`.

Let `L(q)` sum the independently shortest full-pool source paths with edge
numerator `D*b_e + q_e`. Let `W(v)` sum q over **every** occurrence of v,
including overlapping occurrences. For any feasible dictionary V and any
complete paths using it, each occurrence is used at most once. Therefore

```
D*F = sum_used(D*b_e + q_e) - sum_used(q_e)
    >= L(q) - sum_{v in V} W(v).
```

Nonnegativity is necessary for the second inequality. Let A(j) sum the top j
weights in U1, and B(h) sum the top h in U2. With m1/m2 their actual sizes and
capacity B0=256, the **exact** largest dictionary charge is

```
T_k(q) = max_{0 <= j <= min(k,B0,m1)}
             A(j) + B(min(B0-j,m2)).
```

For each exact one-owner count j, nonnegative weights permit taking as many
shared slots as available; zeros need not be taken, but taking them is legal.
This does not invent unavailable entries or require exactly256 entries. Empty
classes, fewer than256 total entries, zero weights and ties are covered. Ties
use fewer one-owner slots, then piece order within each class; this is only a
deterministic maximum-charge receipt, not a proposed dictionary or packet.

Thus every permitted dictionary satisfies
`F >= ceil((L(q)-T_k(q))/D)`, calculated with integer arithmetic as
`-(-numerator // D)`, including negative numerators. A positive integer lower
bound excludes `C/N <= 0.1` in this conditional model (nonempty full sources
give N>0). Neither package bytes nor Finish are silently added to F; their
absence is the existing relaxation, not permission to omit them in M1.

As k increases the activation set grows, T_k cannot decrease and this lower
bound cannot increase. At k256, T equals35's unrestricted top256 weight sum
exactly; selected tie identities may differ, but the numerical bound must not.
At q0 every capacity term is zero, so all k give the same zero-q bound. The
pointwise maximum of the two nonincreasing curves is also nonincreasing. Its
k256 endpoint equals the maximum of those two35 points; claim equality to the
recorded35 best only after replay establishes that it dominates q0.

Do not use a seed F as a conditional upper bound unless its full paid
dictionary satisfies k. The public35 seed has three one-owner entries, so it
cannot certify feasibility at k0/1/2. No new seed feasibility probe is needed
for this certificate question.

## Implicit classification and exact capacity computation

Each33 compressed suffix-trie edge group represents a contiguous interval of
suffix occurrence ranks and a range of word lengths. All represented lengths
have exactly the same occurrence interval. Removing banned lengths does not
change the remaining words' support. Each35 length-bin piece inherits that
interval, so all words in it have the same support class and weight.

In suffix-rank order, prefix-sum adjacent changes of source ID. A nonempty
interval `[lo,hi)` has support one exactly when the transition prefix at
`hi-1` equals that at `lo`. Construction costs O(total source characters) and
each group classification costs O(1). No distinct-owner set per substring or
quadratic word inventory is needed. An independent checker can instead compute
same-owner run endpoints and test `hi <= run_end[lo]`, alongside35's independent
universe/bans checker. Small tests explicitly enumerate words and owners.

Compute each piece weight with35's per-bin suffix-rank q prefix sums. For each
support class, retain only its best256 nonempty pieces by `(descending weight,
piece index)` using a bounded heap. These suffice for its best256 entries:
every earlier piece has at least one entry, so a later piece cannot be needed
before capacity is exhausted. Expand at most256 **scalar weights** per class,
respecting each piece's multiplicity; materialize no word strings. Compute
prefix sums and all k allocation maxima exactly. The prototype stores a
linear list of piece records, not a quadratic string pool.

Additional work beyond35's index/path calculation is O(n + P log256 + 256*10)
time and O(n + P + 256) memory for n suffix positions and P pieces. The eleven
q prefix scans remain O(11n + P); full-path cost is unchanged35. A future checker
should independently sort compressed class records and consume multiplicities
instead of sharing the bounded-heap selector. It must reconcile class counts,
all allocation rows, exact integer arithmetic, monotonicity and k256 equality.

## Prior evidence and interpretation

[25](../fraction-capacity-v1/README.md) and
[28](../all-length-fraction-v1/README.md) gave positive bounds in narrower
shared-string pools with explicit seed/character exceptions.
[33](../all-substring-fraction-v1/README.md) admitted every allowed substring;
[35](../length-sensitive-fraction-v1/README.md) sharpened that bound using
length bins, but its lower bounds remained negative (R−27266, naming−28259).
This question tests a missing conditional axis. It does not relabel those
negative bounds or claim any q optimization exhausted the full dual.

k0 is **not** identical to25/28: those pools retain specific one-owner seed or
character exceptions. Here even singletons obey support accounting, while the
path relaxation still permits every35 edge and charges its activation in T_k.
No semantic-reuse inference follows from either support class. A unique
character may already make a small-k model infeasible; the interpretation must
remain representation feasibility, not a claim that program logic needs
problem-specific chunks.

## Supplied-input verification and deferred complexity exercise

`prototype.py` has only supplied-input functions. `test_prototype.py` uses tiny
invented sources to compare interval classes against explicit word owners,
compressed activation maxima against exhaustive dictionary subsets, independent
explicit path costs, integer weak duality, bans, singleton ownership, ties,
empty classes, multiplicities, small pools, bin boundaries and k256 replay.
No production report or independent full-scale checker is claimed by these tests.

The initial design proposed one deterministic invented300-source fixture
of75000 total characters, with repeated blocks and source-specific suffixes,
plus small distinct-character stress cases. Measure index construction,
classification, each q's path and activation steps separately, peak RSS, group/
piece/class counts, and verify compressed versus independently sorted capacity
terms. Its proposed hard cap was120 seconds on one assigned CPU,8GiB, all timing failures
retained. This is a proposed synthetic mechanism exercise, not a measured runtime
or an engineering estimate. **This exercise was not run and is no longer
proposed for the fixed-q question**, because the public preflight already settles
its inability to exclude. Any support-optimized extension needs its own design,
synthetic evidence, budgets and freeze; no launch is authorized.

Component intent is preserved: exact fixed-source literal evidence, distinct
representation and semantic claims, retained failures, and closed protected
populations. No component boundary changes are proposed.
