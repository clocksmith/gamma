# Item71: price entries using certified nonoverlapping use counts

The proof target is a stronger upper bound on occurrence penalties Q for the
same fixed sources, allowed entries, nonnegative integer q, denominator D,
capacity B and valid relaxed path value L. The certificate premise remains
D*(10C-N) >= L-Q for every covering segmentation. Finish is excluded. The
supplied tiny oracle derives L from the complete allowed-graph shortest paths
with arc cost D*(9 for singletons, -1 otherwise)+q; it never invents L.

Items63/66 divide an entry price by all occurrences, including overlapping
ones. A complete source segmentation cannot use overlapping occurrences of
the same entry. This draft replaces that divisor with a certified upper bound
on how many occurrences can jointly appear. It changes no source, entry ban,
paid character rule, q, potential or frozen ancestor implementation.

## Multiplicity and removal lemma

For each allowed nonempty exact entry e and source p, let m_ep be its count
of all allowed occurrences, N_p the source length and ell_e the entry length.
Set n_ep=min(m_ep,floor(N_p/ell_e)), and n_e=sum_p n_ep. An entry with no
occurrence is irrelevant and is never divided by. Every present entry has
1 <= n_e <= m_e=sum_p m_ep. For a one-owner entry, the sum has one term.

A complete segmentation uses e at most m_ep times and its disjoint intervals
occupy ell_e characters each, so it uses e at most n_ep times in source p.
Thus across all sources it uses e at most n_e times. The same argument works
for any nonoverlapping subset of occurrence intervals; coverage is unnecessary
for the removal lemma itself. Count zero-q occurrences too. Distinct source
IDs count separately even when their strings are equal.

For nonnegative integer price lambda define
r_a(lambda)=max(q_a-floor(lambda/n_e),0) on an occurrence a of e. Each used
occurrence loses at most floor(lambda/n_e), hence all uses of selected entry e
lose at most n_e*floor(lambda/n_e) <= lambda. Unused dictionary entries remove
nothing. Paid singleton entries obey the same rule; they have n_ep=m_ep.

More generally, any independently certified positive upper bound u_e on the
joint nonoverlapping usage can replace n_e. Exact maximum packing counts are
valid but are not the algorithm specified here. Arbitrarily reducing a count,
using a single source's count for a shared entry, or taking a minimum across
sources is invalid. This chosen n sums source bounds; any alternative must
bound total usage across every source. A looser bound from total supporting
source length can also be valid.

## Owner and global certificates

For owner entries only, let R_p(lambda) be the maximum residual weight of
nonoverlapping allowed owner occurrences in p, with free skips. A dictionary
using t_p distinct owner entries in p has Q_owner,p <= lambda*t_p+R_p(lambda).
Use exactly63's finite envelope
f_p(t)=min(A_p(t), min_lambda(lambda*t+R_p(lambda))), including lambda0.
A_p(t) is the unchanged top-weight prefix of actual owner entries. These are
concave nondecreasing prefixes, f_p(0)=0, with finite real slots including zero
marginals. Since n_e<=m_e, every residual and each R_p weakly decreases at the
same price, so f_new<=f63 pointwise. Lambda0 still gives the unchanged57
owner schedule cap. The unchanged shared prefix H is taken at B-j for actual
owner count j; exact concave marginal allocation and max over j<=k give a
bound at least as strong as63.

The68 required-owner restriction also applies: each source that cannot be
covered using shared entries alone must reserve one real owner slot, even if
its value is zero. Allocate the remaining finite marginals and maximize over
r<=j<=k, using H(B-j) at the same j. This dominates68 pointwise. Budgets k<r
are empty and all numeric fields are null; r>B makes all rows null. No finite
prefix is padded. Defined rows are not a general claim that the class is
nonempty; explicit examples below supply covering dictionaries.

For all entries, let R_all,p(lambda) be the maximum all-entry residual schedule
weight, with free skips. Any dictionary of at most B entries has
Q <= G_lambda=lambda*B+sum_p R_all,p(lambda). Minimize over the same fixed
finite price family. The new G is no greater than66's G at every same price
and in its minimum. Combine with a valid owner/required-owner charge by taking
the minimum only when source/bans/q/L/D/B and all entry identities agree.
This global minimum does not invent an allocation split or imply universal
domination by the standalone global cap of the owner bound.

Signed rounding is ceil((L-charge)/D), including negative numerators.
B=0 can describe an empty covering class for nonempty sources; numerical
relaxation rows do not supply a witness. The explicit required-owner empty
flags remain separate from general coverage feasibility.

## Fixed tiny examples to verify independently

Use D=1 and the unchanged illustrative family [0]+[2**r for r in range(14)].
These are supplied general-q examples, not reconstructed corpus q53.

1. Owner example: p='aaaaX', s='Xa', ban both complete source strings. Give
   every 'aa' occurrence q=10, 'aX' q=15 and all other allowed occurrences0.
   B=3,k=1. For 'aa', m=3 and n=min(3,floor(5/2))=2; for 'aX', both counts1.
   Old priced owner charge24 becomes20. The allowed covering dictionary
   {'a','X','aa'} has one owner entry. The relaxed path construction gives
   L=26, so the bound improves2 to6. Exact complete-path enumeration must
   verify the bound; no attainment is asserted.
2. Global example: two distinct source IDs both 'aaaabaaaab', whole string
   banned. Give 'aa' q=10, 'b' q=5 and other allowed occurrences0, B=1.
   Across both sources m_aa=12 and n_aa=10; m_b=n_b=4. Old global minimum92
   at lambda16 becomes88 at lambda32; the zero-price cap is100. The57 charge
   is120, so the explicit minimum improves too. {'aaaab'} covers both sources
   with one shared entry. The relaxed path value is L=-8, so bounds improve
   -100 to-96. No positive-bound or attainment claim is made.

Tests must verify these numbers independently and enumerate tiny dictionaries
and complete joint paths to check actual D*(10C-N), not only compare two
implementations of the same formula. Check owner/global/required dominance,
all price caps and nonoverlap usage counts, zero-q arcs, singleton entries,
shared repeated strings, bans, fixed-grid ties, finite zero slots, B0/r>B,
negative ceilings, malformed inputs and optimized-Python refusal.

## Prospective scalable boundary, not an execution protocol

This theorem's implementation enumerates tiny supplied graphs only. A later
scalable design must reconstruct n from original allowed occurrence geometry,
retain count commitments and independently verify every residual recurrence.
The owner divisor depends on entry length even within a constant-support
suffix group. Existing multiplicity-only caches and group-level arithmetic
cannot be reused without changing their keys and proving equivalence.

For one-owner entries, min(group_occurrence_count,N_owner//length) can be
computed in the existing length loop. For shared entries, all allowed shared
strings are already in the verified original pool, so sparse per-source
counts can accumulate sum_p min(m_ep,N_p//length) by entry identity. Global
support width alone does not recover that sum. Independent per-source
matching/counting must agree with the production geometry. Exact greedy
packing is potentially stronger but is a different declared algorithm. The
conservative count can be loose: for e=a^ell in a^(2ell-1)b^((ell-1)^2),
N=ell^2 and m=n=ell but only one occurrence fits without overlap. A source
position order is needed for exact greedy packing; suffix-array order is not
that order.

Any scalable implementation needs a separate reviewed design, invented
measurement and frozen contract before original inputs. This draft provides
no runtime forecast, price-grid adequacy, optimality, corpus gain, full256
exclusion, dictionary improvement, qualification or M1 claim. A nonpositive
certificate gives no witness. Component intent and admission/publication
boundaries are preserved; private sources, cases and dictionaries stay private.
