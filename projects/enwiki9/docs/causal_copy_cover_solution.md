# Solution to Independent Problem CC-1

Status: `COMPLETE INTERNAL SOLUTION`

Index the end-sorted candidates from \(1\) through \(m\). Every optimal cover
using candidates at most \(i\) either excludes \(i\), with value \(F(i-1)\), or
includes \(i\). In the latter case all other selected targets must end by
\(s(i)\), so their optimal value is \(F(\pi(i))\). Hence

\[
F(i)=\max\{F(i-1),w(i)+F(\pi(i))\}.
\]

Set \(F(0)=0\). Binary search over sorted target ends computes every
\(\pi(i)\). Sorting costs \(O(m\log m)\), all searches cost
\(O(m\log m)\), and the recurrence and backtracking are linear.

On a recurrence tie, exclusion omits the greatest current candidate index.
Induction shows that the resulting selected-index indicator is
lexicographically least when read from greatest index downward. This makes the
maximum-weight cover canonical and, in particular, avoids a latest-order
inclusion whenever an equal optimum does not need it.

A certificate lists selected candidates and the claimed DP values. A verifier
checks candidate equality against the source word, target disjointness, every
predecessor, every recurrence, and the tie rule. After candidates and
predecessors are sorted, this is linear.

For decoding, scan target positions from left to right. At an unselected
position, consume the next literal. At a command start, append

\[
x_{u},x_{u+1},\ldots,x_{u+\ell-1}
\]

sequentially from the already reconstructed output. If source and target
overlap, every source symbol needed at copy step \(j\) either predates the
target or was reconstructed at an earlier copy step. Induction on output
position proves exact reconstruction.

Let \(B(c)\) be the ideal cost of the target and \(K(c)\) the command cost.
For disjoint targets, omitted ideal costs and command costs add, so total
saving is

\[
\sum_{c\in P}[B(c)-K(c)]=\sum_{c\in P}w(c).
\]

The interval recurrence therefore gives the exact ideal optimum over the
supplied family.

Finally, for any fixed cover \(P\), its value changes by at most
\(\sum_{c\in P}\eta(c)\). Comparing an old optimum under new weights and a new
optimum under old weights gives

\[
|\operatorname{OPT}(w)-\operatorname{OPT}(w')|
\le
\max_P\sum_{c\in P}\eta(c).
\]
