# Solution to MV-2: Exact Capacity Allocation

For \(k=0,\ldots,n\), define \(F_k(r)\) as the minimum penalty attainable
using tables \(0,\ldots,k-1\) with exact total allocation \(r\). Initialize

\[
F_0(0)=0,\qquad F_0(r)=+\infty\quad(r\ne0).
\]

The exact recurrence is

\[
F_{k+1}(r)=
\min_{\substack{d\in D_k\\R_k(d)\le r}}
\left(F_k(r-R_k(d))+L_k(d)\right).
\]

Store, on ties, the predecessor producing the lexicographically first divisor
prefix. The optimum is the least finite \(F_n(r)\) over \(r\le B\), again
breaking ties lexicographically. Induction on \(k\) proves that every legal
prefix occurs in exactly one recurrence branch and every branch is legal.
The construction is finite because all domains and the reachable allocation
set are finite.

A state \((r,l)\) is dominated when another state \((r',l')\) has
\(r'\le r\) and \(l'\le l\), with at least one strict inequality. A dominated
state cannot improve any extension because all later allocations and penalties
are added componentwise. Deleting dominated states therefore preserves every
optimum. Replacing \(L_i\) by \(\overline L_i\) gives the exact separable
worst-case solution for interval penalties.

For binary divisors, enumerate subsets in lexicographic order or apply the same
recurrence with choices `full` and `half`. Restrict terminal states to savings
at least \(S\); the first minimum-penalty terminal witness is exact. If
penalties have not been measured, the recurrence still certifies allocation
feasibility but makes no compression claim.

## FXCM calculation

`ContextMap2::Init` doubles each nominal \(m_i\), then allocates 128-byte cells
plus a fixed 16,384-byte alignment allowance. Halving an index therefore saves
exactly its nominal \(m_i\).

The additional subset has nominal sizes:

\[
\begin{array}{c|rrrrrrrrrrr}
i&5&7&8&9&10&11&12&14&15&16&17\\
\hline
m_i\text{ (MiB)}
&128&32&64&128&128&128&128&32&2&8&32.
\end{array}
\]

Their sum is

\[
128+32+64+4(128)+32+2+8+32=810\text{ MiB},
\]

or exactly

\[
810\cdot2^{20}=849,346,560\text{ bytes}.
\]

Since

\[
849,346,560>737,487,872,
\]

the subset exceeds the required allocation reduction by 111,858,688 bytes.
Including the reference index-13 cut, total saving against all-full capacity is
\(1,066\) MiB. This proves allocation feasibility only. Exact archive,
roundtrip, determinism, resident memory, and runtime remain execution
obligations.
