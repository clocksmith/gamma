# AF-1 Solution: The Aligned Associativity Frontier

## 1. Exact aligned sizes

Direct substitution into

\[
c(A)=32\left\lceil\frac{9A+1}{32}\right\rceil
\]

gives:

| \(A\) | \(9A+1\) | \(c(A)\) |
|---:|---:|---:|
| 1 | 10 | 32 |
| 2 | 19 | 32 |
| 3 | 28 | 32 |
| 4 | 37 | 64 |
| 5 | 46 | 64 |
| 6 | 55 | 64 |
| 7 | 64 | 64 |
| 8 | 73 | 96 |
| 9 | 82 | 96 |
| 10 | 91 | 96 |
| 11 | 100 | 128 |
| 12 | 109 | 128 |
| 13 | 118 | 128 |
| 14 | 127 | 128 |

## 2. Complete Pareto frontier

Within a fixed physical size, the largest associativity dominates every smaller
one. Therefore:

- \(A=3\) dominates \(A=1,2\);
- \(A=7\) dominates \(A=4,5,6\);
- \(A=10\) dominates \(A=8,9\);
- \(A=14\) dominates \(A=11,12,13\).

The complete undominated set under the stated definition is therefore

\[
\boxed{\{3,7,10,14\}}.
\]

No member of this set dominates another. Their memories are strictly
increasing:

\[
32<64<96<128,
\]

and their capacities are also strictly increasing:

\[
3<7<10<14.
\]

Thus reducing memory between two frontier points necessarily reduces capacity,
and increasing capacity necessarily increases memory.

## 3. Ratios relative to fourteen ways

Since \(c(14)=128\), the exact ratios are:

| \(A\) | memory ratio | memory saving | capacity ratio |
|---:|---:|---:|---:|
| 14 | \(1\) | \(0\) | \(1\) |
| 10 | \(3/4\) | \(1/4\) | \(5/7\) |
| 7 | \(1/2\) | \(1/2\) | \(1/2\) |
| 3 | \(1/4\) | \(3/4\) | \(3/14\) |

The alignment calculation has an important consequence: \(A=12\) is not a
higher-capacity 112-byte alternative under the supplied representation.
Because \(9(12)+1=109>96\), it rounds to 128 bytes and is dominated by
\(A=14\). Any claimed 112-byte twelve-way cell requires a different physical
representation and a separate theorem.

## 4. Exact budgeted allocation

Let the tables be \(i=1,\ldots,n\), and let

\[
\mathcal A=\{14,10,7,3\}.
\]

Define the dynamic-programming value

\[
D_i(r)=
\min\left\{
\sum_{j=1}^{i}d_j(A_j):
A_j\in\mathcal A,\ 
\sum_{j=1}^{i}B_jc(A_j)\le r
\right\}.
\]

Use \(D_0(r)=0\) for \(r\ge0\), and \(+\infty\) for an infeasible state. The
recurrence is

\[
\boxed{
D_i(r)=
\min_{\substack{A\in\mathcal A\\B_ic(A)\le r}}
\left[D_{i-1}(r-B_ic(A))+d_i(A)\right].
}
\]

This is finite because there are \(n(R+1)\) states and at most four transitions
per state. It uses at most

\[
4n(R+1)
\]

candidate inspections. A sparse implementation may retain only reachable
memory totals, but that does not change the optimum.

## 5. Correctness

The proof is by induction on \(i\). Every feasible allocation for the first
\(i\) tables has a final choice \(A_i=A\); deleting that choice leaves a feasible
allocation for the first \(i-1\) tables with budget \(r-B_ic(A)\). Conversely,
appending any legal \(A\) to a feasible predecessor produces a feasible
allocation for the first \(i\) tables. Taking the minimum over all final choices
therefore considers every feasible allocation exactly through its final
choice, proving the recurrence and global optimality.

Store with each finite state the selected predecessor. When objective values
tie, compare their reconstructed associativity vectors under the frozen order

\[
14\prec10\prec7\prec3.
\]

Selecting the first vector at every tie returns the lexicographically first
global minimizer. Equivalently, one may store rank-preserving persistent
backpointers and compare their finite ranks.

## 6. Transfer boundary

The theorem removes arbitrary associativity values and arbitrary memory
allocation from the search. It guarantees the exact best allocation only after
the penalty tables \(d_i(A)\) are supplied.

Those penalties cannot be inferred from alignment. Gamma must obtain them by
native, causal, deterministic replay of each frozen option or by another exact
factorization whose interaction assumptions are proved. The following remain
mandatory:

- exact archive bytes under the jointly selected allocation;
- exact package and source growth;
- exact reconstruction and deterministic second archive;
- decimal-10GB peak memory;
- official runtime eligibility;
- distant and full-scope evidence where required.

Until those receipts exist, AF-1 is a mathematical candidate-family reduction
with zero Hutter score credit.

