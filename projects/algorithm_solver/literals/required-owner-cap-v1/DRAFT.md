# Item 61: require a slot for every forced owner

2026-10-24. Mathematical design and tiny supplied-input oracles only. No private
input, production kernel, complexity measurement, binder, runner or launch.
Keep item 57's exact sources, global bans, ownership, fixed nonnegative q,
denominator D, suffix potentials and full-DAG minimum L unchanged. This includes
its application to item 53's fixed q; it is not a new multiplier optimization.

## Required owners and scope

Let S contain every allowed exact entry with at least two distinct source owners,
including shared singletons. Let P* contain the sources that have no complete
segmentation using S, allowing all shared entries without a cardinality limit.
Write r=|P*|. In every dictionary that covers all sources, each p in P* must own
at least one selected one-owner entry. Such an entry cannot serve another source,
so these r selections are distinct. This is stronger allocation information
than only j>=r: the slots must go to these particular owners.

The forced set comes from full shared-only reachability. Private-character
ownership is not an equivalent definition in general. Accepted item 56's equality
requires its additional all-singletons-allowed authority. Banning a shared
singleton can force a source without any private character; the tests retain
that case. Sources with no path even in the full allowed graph are rejected by
the supplied oracle, rather than assigned a finite path minimum.

Absent dictionary entries can be removed; they never cover a source or improve
nonnegative charge and are excluded from occurring entry counts. Paid occurring
singletons are classified by their actual distinct-source owners. Repeated
occurrences in one source do not create shared ownership. No free decoding edge
or source rewrite is introduced.

## Exact constrained numerical allocation

Keep item 57's per-owner prefixes A_p(t), full nonoverlap caps R_p and
f_p(t)=min(A_p(t),R_p). Their finite increments are nonnegative and nonincreasing.
Let m_p be the actual number of occurring one-owner entries owned by p. For fixed
j<=min(B,sum m_p), define

    U61(j) = max sum_p f_p(t_p)
              subject to sum_p t_p=j,
              1<=t_p<=m_p for p in P*,
              0<=t_p<=m_p otherwise.

For j>=r, assign each forced owner its first slot, paying its entire f_p(1) in
the upper bound. The remaining marginal sequences start at rank 2 for forced
owners and rank 1 for other owners. They remain nonincreasing. Select the largest
j-r residual marginals, ordered by descending value, then string owner ID, then
rank. That deterministic ordering is prefix-closed within every owner, including
zero/tied marginals. It attains the unrestricted largest-marginal sum, hence the
exact constrained numerical maximum. No claim is made that paths or actual
dictionaries simultaneously attain these per-owner caps.

The equivalent sum t_p<=j version has the same value for j<=sum m_p, since all
increments are nonnegative and unused available slots can extend an allocation.
For j beyond availability it saturates; this implementation simply restricts j
to finite available entries. It never invents zero-valued entries to fill slots.
If r>B, every examined budget is empty. Top B weights per owner still suffice
for all relevant prefixes, but the full scheduling computation cannot truncate
its occurrence set. The prototype reuses item 57's explicit oracle quantities;
it is not a scalable corpus implementation.

Let H(s) be the sum of the largest min(s,m_shared) shared entry weights. Define

    T61(k) = max [ U61(j) + H(B-j) ]
             over r<=j<=min(k,B,sum m_p).

Choose fewer one-owner slots when charges tie, as before. For k<r the candidate
class is empty by the coverage argument: publish an explicit empty marker and
null charge/numerator/integer bound. Do not encode emptiness as a finite numerical
certificate or report it as evidence of a feasible class. For k>=r, this necessary
condition alone does not prove coverage or B-entry feasibility.

## Weak duality and dominance

Take any covering dictionary of at most B entries and at most k one-owner entries,
and any complete encoding paths through it. Let t_p count its occurring selected
one-owner entries, j=sum t_p. Every forced owner satisfies t_p>=1. Actual used
one-owner q in p is at most f_p(t_p), and used shared q is at most H(B-j).
Therefore total path penalty Q<=T61(k). The fixed full-DAG minimum obeys
L<=D*F+Q, where F=10C-N. Thus

    F >= ceil((L-T61(k))/D).

The charge bounds actual path-used q, not all activation weights. Negative base
costs are harmless in the advancing DAG. Nonnegative q is needed for the entry
weight and schedule upper bounds. No canonical/min-N tie policy is assumed.

The constrained allocation set is a subset of item 57's allocation set, and its
j range is also restricted. Hence T61(k)<=T57(k) whenever k>=r; the numerator and
integer lower bound cannot worsen. Below r, item 61 instead proves emptiness.
As k increases through the defined range k>=r, the charge cannot decrease. Positive
bounds exclude F<=0 only in the fixed-source/support class, without proving that
class is feasible. A nonpositive result is inconclusive about other q or d.

## Strict and null mechanisms

A strict example uses sources `abba`, `cc`, `aa`, bans their complete source
strings, character-only original edges with q=0 and D=1. Their old distances are
9 times remaining length; q53 on a longer allowed edge of length l is 9l+1,
and is zero on singleton edges. Only `a` is shared. The forced owners are the
first two sources. At B=3,k=2, the dictionary {a,b,c} covers every source and
uses exactly the minimum feasible two one-owner entries. Item 57 can instead
allocate both charged slots to the first owner, reaching charge38; item 61 must
reserve one slot for the second owner, reducing the maximum charge to28. This
is a strict gain at a known feasible minimum k, with identical q and L, not a
claim that the bound is tight or close to 10%.

If there are no forced owners, the allocation and all charges equal item 57.
If every residual marginal is zero or the unconstrained maximizer already
satisfies all requirements, the numerical change can also be null. Even with
r>0, larger k may erase a gain by supplying the previously omitted owner slot.
Tests compare exact integer owner allocations and enumerate every covering tiny
dictionary and every path through it, including bans, repeated owners, shared
singletons, zero/tied weights, capacity zero/excess and all budgets below r.

No corpus inference, complexity estimate, independent confirmation, source
execution, fresh qualification, packet witness, M1 or current-best change is
made. Gamma component intent and boundaries are preserved. A future supplied
kernel and any measured protocol require their own review and authorization.
