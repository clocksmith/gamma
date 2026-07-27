# Solution to Independent Problem SC-1

Status: `COMPLETE INTERNAL SOLUTION`

Fix \(k\). If a selected item has weight smaller than an unselected item,
exchanging them increases the benefit and leaves \(K(k)\) unchanged. Repeating
this exchange proves that an optimum selects the \(k\) largest weights. A fixed
item order breaks equal-weight ties.

Therefore the global optimum is obtained by sorting once, forming prefix sums,
and checking

\[
\sum_{j=1}^kw_{(j)}-K(k)
\]

for every \(0\le k\le n\). Sorting costs \(O(n\log n)\), and the scan is
linear. A certificate lists the sorted order, selected prefix length, prefix
sum, and all cardinality costs; direct verification checks adjacent order,
prefix sums, and the maximizing index.

There are \(\binom nk\) possible position sets. Their canonical enumerative
rank therefore requires and suffices with

\[
\left\lceil\log_2\binom nk\right\rceil
\]

fixed bits. Adding \(b\) literal bits per selected item and \(h\) framing bits
gives the stated cost.

During reconstruction, unrank the selected position set. Scan positions in
order. At a selected position, consume its supplied literal value; otherwise
consume the next symbol from the residual stream. Induction on position proves
exact reconstruction.
