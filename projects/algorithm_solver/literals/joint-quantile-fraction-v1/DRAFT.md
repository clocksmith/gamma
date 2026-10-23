# 42: Joint quantile and character-fraction certificate, design draft

2026-10-23. Inactive protocol and implementation, tested on synthetic inputs only. No private source,
case, or multiplier artifact has been opened for this item. This is not an
execution freeze. No corpus execution, dictionary search, promotion, or new
population conclusion is authorized by these files.

## Question and population

For the **same fixed 300 fit sources** as item 35, can any allowed flat dictionary
of at most 256 entries simultaneously admit encodings with aggregate character
fraction at most 10%, median selection count at most 32, and nearest-rank p95 selection
count at most 96? Original R and item-13 naming remain separate fixed-source
questions. The full substring pool, exact whole-source/body bans, all charged
singletons, and lack of fallback are inherited unchanged from item 35. The
method deliberately relaxes other requirements, so a positive certificate can
exclude this named joint target; it cannot establish feasibility.

**This is not a necessary fit-only condition for the 400-program M1 cohort.**
With all 100 validation programs compact, a 400-program median target only
necessarily forces 100 fit programs to have at most 32 selections, and its p95
target only necessarily forces 280 fit programs to have at most 96. Moreover,
negative validation `10C-N` can offset positive fit `10C-N`. A fixed-300
certificate therefore excludes neither M1 nor a 400/500-program target. Any
future combined-population extension requires its own freeze and input access.

N counts dictionary selections (path edges), excluding Finish. Total actions
are N+1 per program; the corresponding action median/p95 limits would be
33/97. All caps below are selection caps; no threshold is changed.

## Inherited dual and the joint extension

Let `D` be the positive integer multiplier denominator. For an occurrence edge
`o=(p,i,j)`, define `b(o)=9` for a singleton and `b(o)=-1` otherwise. For any
complete collection of encodings, its integral objective is
`F = sum b(o) = 10C-N`; fraction at most 10% is exactly `F <= 0`.
Item 35 supplies nonnegative integer `q[p,i,length_bin]`. Every occurrence gets
its corresponding multiplier `q(o)`. Each allowed dictionary string `e` has
weight `W_e=sum_{all occurrences of e} q(o)`. Let `T(q)` be the sum of the largest
256 such weights, with the inherited exact piece multiplicities. If fewer than
256 strings exist, use all of them.

For every legal dictionary and its paths, the sum of multipliers on *used*
occurrences is at most the weight sum of its entries, hence at most `T(q)`.
Occurrences in one path cannot repeat the same start/end edge, and all
multipliers are nonnegative. Consequently, for any family of admissible path
collections `A`,

```
DF >= min_{paths in A} sum_o (D*b(o) + q(o)) - T(q).
```

The joint path family imposes the stated quantiles but otherwise allows every
allowed substring independently. It remains a relaxation of all legal
dictionaries satisfying those quantiles. Subtract the **original** `T(q)`;
cardinality penalties below never change dictionary weights or the top-256
calculation. If the integer numerator is `B`, publish `ceil(B/D)` as an integer
lower bound on `F`. A positive lower bound excludes the fixed-300 joint target.
Zero or negative is inconclusive. No rounded dictionary is needed for this proof.

## Option E: exact cardinality and exact median union

Let `d_p(K)` be the minimum sum of `D*b+q` on a path for source `p` using at most
`K` edges, and let `g_p` be the unrestricted minimum from item 35. Missing paths
have infinite cost. Compute exact-cardinality layers up to 96 and take prefix
minima; one rolling layer contains suffix costs for the previous cardinality.
Each of the 11 inherited length windows uses a heap of previous-layer endpoint
costs. Expired endpoints are discarded; forbidden endpoints are temporarily
removed and restored, preserving alternatives in overlapping future windows.
The unbounded 257+ bin and global exact bans remain active.

For 300 nonempty encodings with sorted positive integer counts `n_1..n_300`,
the median condition is `n_150+n_151 <= 64`, not merely a single rank cap.
Together with `n_285 <= 96`, it is exactly the union over integers `a=1..32`
of these four-category assignments:

| Category | Assigned programs | Selection cap |
| --- | ---: | ---: |
| Lower half | 150 | a |
| Upper middle | 1 | 64-a |
| Remaining p95 portion | 134 | 96 |
| Tail | 15 | unrestricted |

Forward direction: choose `a=n_150`, and assign programs in sorted order.
Reverse direction: the assignment gives `n_150 <= a`, `n_151 <= 64-a`, and
`n_285 <= 96`. The order of the first two caps is valid because `a <= 32`.
The tail is genuinely unrestricted: forcing all programs below 96 would make
the exclusion unsound. Nonempty sources ensure `a>=1`.

For each `a`, solve the integer transportation problem using the four respective
costs `d_p(a), d_p(64-a), d_p(96), g_p`; take the minimum over all 32 cases.
The prototype uses integral successive shortest augmenting paths, then checks
an independent assignment dual: potentials `u_p,v_c` satisfy
`u_p+v_c <= cost[p,c]`, and `sum u_p + sum quota_c*v_c` equals the assignment
cost. This certifies exact assignment optimality without trusting its optimizer.
Subtracting `T(q)` gives the exact joint path-family bound at this fixed `q`.

Path work is 96 cardinality layers over source positions and 11 windows, with
heap factors and ban-removal work, rather than enumerating the full substring
pool. Path memory is rolling layers and heaps for one source plus multiplier
storage and the 300-by-96 answer table. Assignment work is 32 transportation
problems of 300 rows and four categories, each with 300 unit augmentations.

## Option P: necessary quantile relaxation with integer penalties

The exact median implies at least 150 programs have at most 32 selections. Together
with p95, this gives a necessary three-category assignment with quotas
`150 / 135 / 15` and caps `32 / 96 / unrestricted`. It is weaker than the exact
median: 150 counts equal to 32 followed by 150 counts equal to 33 satisfy this
relaxation but have median 32.5.

For a finite grid of nonnegative integer penalties `t`, including zero, compute

```
g_p(t) = min_path sum_o (D*b(o) + q(o) + t)
h_p(K) = max_t [g_p(t) - t*K].
```

For every path with `N<=K`, `g_p(t)-tK <= sum(D*b+q)+t(N-K)
<= sum(D*b+q)`. Thus `h_p(K) <= d_p(K)`. Inclusion of zero also guarantees
`h_p(K) >= g_p(0)`, so even the finite grid cannot weaken item 35's bound.
Different programs and caps may choose different maximizing penalties; these
are separate valid lower bounds before assignment and need no shared `t`.

Minimize total row cost using `h_p(32), h_p(96), g_p(0)` and the exact
three-category quotas. A rolling integer DP tracks short count 0..150 and tail
count 0..15; the medium count is the number of processed rows minus those two.
This costs at most `300*151*16*3` transitions and `151*16` states per layer.
Subtract the same `T(q)`. The result lies between the inherited unrestricted
bound and Option E's exact joint bound. This is a proof oracle, not another
weighted primal dictionary objective or a rerun of item 18.

An eight-value synthetic grid is pinned in `synthetic-contract.json`. A future
corpus freeze must pin an explicit grid in the actual inherited denominator;
the invented fixture's numerical scale is not a tuning result for item 35.

## Public motivation and interpretation

Item 35's public independently checked bounds were `-27266` for R and `-28259`
for naming; its rounded proposals did not cover the cohort. Its public relaxed
path diagnostics show many short edges. Those observations motivate testing
whether selection-count constraints strengthen the dual, but establish neither a
positive joint bound nor the quality of any new dictionary. Item 40's min-F
repair asks for feasible witnesses and separately reports their N distribution;
this proposal asks a complementary lower-bound question over the full pool.

Reusing each sealed item-35 multiplier once is an interpretable diagnostic:
report old path term, joint path term, their difference, unchanged dictionary
term, and final bound. Old multipliers were optimized for unrestricted paths;
failure to certify at them is not evidence against the joint method. There is
no claimed probability of a positive result. Neither source changes nor typed
2c representations fall within this fixed-source flat scope.

## Synthetic evidence and execution boundary

`mechanism.py` contains only path and assignment mechanisms; `benchmark.py`
constructs 300 invented strings totaling 75,000 characters with varied lengths,
invented integer multipliers, and globally applied exact synthetic bans. The
benchmark has no private-input argument or corpus loader. Its specification
pins the fixture, code, Python binary and inherited public code contract. Each
mode is restricted to one assigned core (P:4, E:5), 8 GiB address space, a
115-second worker alarm and a 120-second hard external cap. It retains failures.
Results are synthetic complexity evidence only, not extrapolated corpus timing.

Focused tests compare capped paths with exhaustive paths on small invented
strings, penalty bounds with those exact costs, assignment solvers with
exhaustive assignments, and the median union with its direct rank definition.
The separate production and report implementations now bind source/q identities
through a public-only pending contract, implement independent full-pool top-256
and capped-path replay, and retain exact assignment primal/dual or Hall-cut
receipts. The pending contract remains inactive; private execution requires
root/Claude review and exact-match activation. No existing frozen item changes.

The component intent is preserved: this draft adds a bounded proof diagnostic
and its synthetic checks, while leaving representation, qualification,
population, protected-input and promotion boundaries unchanged.

## Selected next protocol, following synthetic checks

Both synthetic modes completed under the pinned caps. Exact cardinality paths
took 14.635 s, the necessary assignment 0.060 s, and all 32 exact median
assignments 1.751 s; total worker elapsed was 16.554 s and peak RSS 61,448 KiB.
The penalty mode took 3.707 s total and peak RSS 140,192 KiB. These are measured
results for the invented fixture only; see `synthetic-exact.json` and
`synthetic-penalty.json` and their shared specification hash. They establish
mechanism feasibility at that synthetic size, not a corpus timing guarantee.

The selected main design is **Option E**. For each separately named source
cohort, evaluate exactly six multipliers obtained from its sealed item-35 `q`:
`floor(s*q)` for `s = 0, 1/4, 1/2, 1, 2, 4`. No optimizer, adaptive grid,
deduplication-based omission, dictionary proposal, or source qualification is
added. The denominator is unchanged. Every point independently satisfies weak
duality; taking the largest conditional lower bound is valid. All six points
in both cohorts must complete and replay before reporting a complete result.

Replay will use an independent per-cardinality segment tree, reconstruct global
ban endpoints independently, and check exact assignment primal/dual receipts.
For every point it will also replay the unrestricted bound and report the
necessary three-class diagnostic separately. The scale-one unrestricted bound
must match item 35's public certificate. Proposed caps are one cohort worker
on each of cores 4 and 5, 8 GiB per process, 1,200 seconds for the entire
production job and a separate 1,200 seconds for independent replay. Actual
launch remains subject to the new freeze and review.

Item-35 seed min-F encodings generally violate the quantile caps. They are
**not** conditional feasible upper bounds: this protocol will neither assert
that a conditional lower bound is below seed F nor publish a gap to seed F.
No new feasible witness or population qualification is produced.
