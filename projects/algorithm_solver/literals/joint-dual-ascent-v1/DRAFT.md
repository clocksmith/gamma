# Item 45: ascent on the exact joint conditional dual

Status: mathematical design and invented-source proof/complexity measurement
only, approved for that scope on 2026-10-23. No private input, q, source, case or
run receipt has been opened. After the synthetic measurement, root approved
preparation of a separate production wrapper, binder and freeze; launch still
requires root/Claude review and exact contract activation. The component remains an exact-literal research relaxation under
GOALS and the algorithm-solver CATSCAN. No M1 gate or corpus authority changes.

## Why this is a different optimization question

[Item 42's public record](../joint-quantile-fraction-v1/README.md) reports the
strongest of six fixed scales at q=0: −23,660 for R and −23,655 for naming.
The unit-scaled item 35 q gives weaker joint bounds, −26,617 and −27,289.
That q was optimized for unrestricted paths, not for the joint selection-count
constraints. Scaling it is not optimization of the joint dual. These negative
bounds do not prove existence of a dictionary reaching 10%.

Keep exactly the eventual named 300 fit sources per cohort, all allowed exact
substrings, the full global source/body ban set, 256 paid entries, the 11 item 35
length bins, and the exact item 42 joint family. N counts **selections**, excluding
Finish. Sorted counts must satisfy n150+n151 <=64 and n285<=96. This is the
same fixed-300 conditional question; it is not a necessary condition for the
400-program M1 population and cannot exclude M1 or the 500-program target.

## Exact concave objective and direction

For occurrence coordinate i=(program,start,length bin), use q_i>=0, an integer,
with fixed positive denominator D. Let x(P) be the occurrence-indicator vector
of a family P of source-covering paths, and b be 9 on singleton edges and −1
on longer edges. Thus sum b=F=10C−N. Let A be the exact joint family above.
For a distinct entry e, a(e) counts **all** its allowed occurrences in those
coordinates. Dictionary singleton entries are paid and included in this pool.

```text
L(q) = min(P in A) [D F(P) + q · x(P)]
T(q) = max(|S| <= 256) q · sum(e in S) a(e)
B(q) = L(q) − T(q)
```

Every feasible capacity-256 dictionary/path pair in A has D F >= B(q), because
used occurrences are bounded coordinatewise by all occurrences of its activated
entries and q is nonnegative. Negative longer-edge costs cause no cycle issue:
every source edge moves strictly right in a finite DAG. B is concave: L is a
minimum of affine functions, and −T is the negative of a maximum of linear ones.

Choose an exact minimizing joint path family P_q and exact maximizing entry set
S_q, with deterministic ties. Then

```text
g(q) = x(P_q) − sum(e in S_q) a(e)
B(q') <= B(q) + g(q) · (q' − q).
```

This is a **supergradient** for concave maximization, not a subgradient inequality
in the opposite direction. The inequality follows by evaluating L(q') at P_q
and lower-bounding T(q') by S_q. At ties, any such pair is valid. The direction
does not promise an improving finite step or a jointly feasible dictionary.

## Joint minimizer and bounded path extraction

1. Run rolling exact-cardinality layers to obtain d_p(k), the minimum weighted
   path cost with at most k selections, k=1..96. Keep only two cost layers for
   one program at a time and the 97-element cap-cost vector per program. Also
   obtain each program's unrestricted path cost g_p.
2. For every a=1..32, solve the exact integer assignment with categories
   `(cap a, cap 64−a, cap 96, unrestricted)` and quotas `(150,1,134,15)`.
   Retain integer primal labels and dual potentials, or a Hall certificate.
   Choose minimum value, then smallest a; retain all 32 cases for verification.
3. For a program assigned cap K, choose the smallest k with d_p(k)=d_p(K).
   Recompute only its exact layers 1..k. Keep rolling Python-integer costs and
   compact uint32 endpoint backpointers for **this program only**, then release
   them before recovering another program. Endpoints use the smallest end on
   equal cost; the suffix is recursively tied the same way. The layer index
   decreases on every recovered edge. Check exact endpoint coverage, every ban,
   recovered edge count and integer cost equality to the assigned optimum.
4. Recover uncapped programs with one ordinary DAG pass and endpoint array.
   Independently sum all recovered edge numerators and check equality to the
   assignment optimum, the two exact quantile predicates and F accounting.

The prototype has an explicit 64 MiB endpoint-table cap per program. It checks
`4*k*(source_length+1)` before allocating and requires endpoints below the uint32
sentinel. Cap breach fails rather than shortening a source, reducing a cap or
silently retaining incomplete paths. Only endpoint indices, not 96 layers of
Python integer costs for the entire corpus, are retained. A future production
contract must freeze its own exact cap after this synthetic measurement.

For N total source positions and longest source n_max, cost-layer memory is
O(n_max), backpointers O(96 n_max) compact bytes, cap receipts O(96·300), and
q/gradient storage O(11N), in addition to the existing full-pool index. Recovery
adds at most one more capped-DP pass over each capped program. With binary heaps,
the cardinality work is O(96·11·N log n_max plus ban-heap work); the recovered
pass is bounded by the same expression. Exact assignment over 300 rows/four
categories is separately measured for all 32 cases, not treated as free.

## Dictionary multiplicity and ties

Use item 35's complete suffix-interval/length-bin pieces. Every length in one
piece has identical occurrence coordinates and therefore identical weight.
Select the top 256 **distinct entries**, represented by piece multiplicities;
ties use piece index, then shortest legal lengths within a piece. Bans remain
excluded globally. The start/bin dictionary term is obtained by interval range
addition of the selected multiplicities, followed by prefix sums mapping suffix
ranks back to source positions. Do not replace multiplicity by a binary selected
piece flag or count only occurrences used by the recovered paths.

Check q·dictionary_occurrences=T exactly and q·used_occurrences plus base costs
equals L. This identifies the selected linear functions even when their values
tie. No vocabulary strings need be materialized for production gradients.

## Search protocol and proposed parameters, not frozen

Initialize at q=0 and retain its exact certificate. At a future binding, its
independent joint numerator must match item 42's corresponding q=0 receipt;
this is a future input/certificate check, not a current private probe. Retain
best q by the **integer numerator**, with the initial q winning exact ties.
Therefore a successfully verified completed search cannot report a weaker best
bound than that baseline. An incomplete search remains incomplete even if it
has a promising partial point.

Projected integer updates have the form
`q_next = max(0, q + s_t*g)`, coordinatewise, with positive integer step s_t.
The parameter proposal below follows measurement of two complete invented
iterations and remains subject to root review. A finite integer
schedule need not tend to zero and is not presented as a convergence theorem.
Finite steps may decrease B. Zero projected movement is a stop diagnostic,
not proof of primal feasibility or global optimality. No Polyak step may use the
seed encoding: it is not known to satisfy the joint quantile constraints and
is not a conditional primal upper bound. No such gap is reported.

The first production design should start only at zero. Adding a separate item 35
warm trajectory would need its own predeclared budget/comparison; the existing
six-scale evidence is not permission for adaptive restarts.

## Proof checks and measurement before any production proposal

Invent short sources, enumerate every allowed segmentation and capacity-limited
dictionary on a small exact joint family, and verify the objective independently.
For all q,q' on a small multiplier grid, exhaustively check the supergradient
inequality and concavity, including zero-weight and path/dictionary ties. Check
the recovered path count/cost, exact global bans, compact-byte cap failure,
dictionary multiplicity, and projected integer updates. The tiny family uses
the same median-union construction with explicitly smaller quotas; it is not
corpus evidence.

Then measure a complete invented 300-program iteration: all cap costs, all 32
assignments, exact top-entry selection, path recovery, occurrence multiplicities,
gradient construction and an integer update. Include pool-build cost separately
and total wall/peak memory; do not report DP-only timing as iteration cost.
The whole synthetic job is capped at 60 seconds on core 4 with 8 GiB. No actual
source, q, corpus cost or run file is read. Report measurements and a concrete
step/budget proposal to the root before writing a production runner or binder.

## Completed invented-only measurement

[synthetic-complexity.json](synthetic-complexity.json) records the complete job;
[synthetic-spec.json](synthetic-spec.json) pins its exact original receipt,
prototype, test and measurement-script bytes, Python 3.14.4 interpreter bytes,
parent contract and limits. Those executable files were unchanged between the
measurement and its retrospective provenance pin. No production parameter was
frozen by that measurement.

Four focused tests passed, including every ordered pair on a 3×3 multiplier
grid for the supergradient inequality, exact midpoint concavity checks, exhaustive
small path/dictionary costs, negative-edge recovery, global exact bans,
selected-entry multiplicity and endpoint-cap rejection.

The larger fixture has **300 invented programs, 20,955 source characters and
maximum source length 80**, 15,885 allowed distinct substrings, 6,465 length
pieces and 106 global exact bans. This is materially smaller and has shorter
sources than the earlier 75,000-character synthetic fixture. These timings
cannot be extrapolated to private-source runtime.

| Component, seconds | q=0 iteration | Next invented iteration |
| --- | ---: | ---: |
| Cardinality and unrestricted costs | 3.432 | 3.444 |
| All 32 exact assignment cases | 2.868 | 2.913 |
| Dictionary weights and occurrence multiplicities | 0.115 | 0.138 |
| Path recovery and gradient | 2.172 | 1.777 |
| Projected integer update | 0.017 | 0.012 |
| Complete iteration including overhead | 8.607 | 8.288 |

Pool construction took 0.119 seconds; the whole job including tests took 17.110
seconds on core 4. Peak process RSS was 50,592 KiB; the largest live per-program
endpoint table was 12,960 bytes. Both iterations evaluated every one of the
32 median-union cases and chose a=32.

The deliberately simple synthetic step s=D changed the exact numerator from
−10,307,000,000 to −20,241,000,000. The retained best stayed at q=0. This demonstrates
why finite ascent steps cannot be assumed to improve the objective. It neither
selects a good corpus step nor licenses adaptive corpus tuning.

## Root-approved finite search procedure, pending cross-review

Use one zero-start trajectory per cohort, at most **16 evaluated q points**
(15 updates), D=1,000,000. At iteration t=0.., compute r as the integer ceiling
of sqrt(t+1), using an integer square root. The root-approved schedule is

```text
s_t = max(1, D // (4*r))
q_next_i = max(0, q_i + s_t*g_i).
```

A +1 occurrence direction initially changes an edge's multiplier by one quarter
of an objective unit; the scale declines deterministically with the iteration
number. There is no L2 gradient normalization, so the positive-coordinate scale
does not shrink merely because the population has more occurrence coordinates.
Gradient squared norm remains a diagnostic and a zero-direction stop check.
This fixed schedule was chosen by root after the design review; it was not
selected by synthetic sweeps or private-input tuning and is not claimed optimal.

Projection may zero negative updates and finite steps may lower the objective.
Stop early on zero supergradient or unchanged projection with an explicit
diagnostic reason; make no primal-feasibility or optimality claim. The finite
horizon, integer rounding and unit floor give no asymptotic convergence guarantee.
There is no line search, restart, objective-driven parameter adjustment or seed
upper bound. The measured prototype/scripts remain byte-for-byte pinned; the
approved schedule is implemented in a separate production wrapper.

Root approved separate **1,200-second production and 1,200-second independent-report**
phase caps, one cohort per core 4/5, 8 GiB per worker, and the 64 MiB per-program
endpoint cap. These are fixed resource limits, not runtime estimates.
They require the proposed freeze and cross-review; no production execution is authorized.
A hard phase failure leaves an incomplete result, not a promoted partial best.

Keep the q=0 checkpoint and final best q as certificate targets. The independent
report must reconstruct the full allowed pool, bans, dictionary term, cardinality
costs and all 32 assignment proofs for each distinct target, including the
q=0 match to item 42. Search can retain scalar/gradient-norm/hash diagnostics for
other trajectory points without rerunning them all independently, but those
numbers must remain explicitly labeled **search diagnostics**, not additional
independently verified bounds. A selected best point is never accepted based
only on its search-side objective or gradient. The initial q wins exact ties.
