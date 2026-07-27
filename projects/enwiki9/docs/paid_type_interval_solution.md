# TI-1 Solution: Paid Ordered Type-Interval Coding

The length-\(N\), weight-\(E\) binary strings are in bijection with the
\(E\)-subsets of \(\{1,\ldots,N\}\). Ordering their one-positions
lexicographically gives \({N\choose E}\) ranks. Counting proves that every
injective fixed-length representation needs at least
\(\lceil\log_2{N\choose E}\rceil\) bits, and zero-padded binary ranks attain
the bound.

For the recurrence, assume inductively that \(D(t-1)\) is optimal on the
first \(t-1\) cells. An optimum on the first \(t\) cells either leaves cell
\(t-1\) uncovered, with value at most \(D(t-1)\), or has a unique last
selected interval \([a,t-1]\). All earlier selected intervals lie in
\(\{0,\ldots,a-1\}\), so their value is at most \(D(a)\). Conversely, every
branch in the recurrence combines an optimal prefix with a disjoint final
interval and is feasible. This proves equality by induction.

On equal values, skipping removes the final interval and therefore produces
an inclusion-minimal optimum. If interval branches tie above the skip value,
the least left endpoint is a fixed canonical rule. Stored predecessor
pointers reconstruct the selected family.

Before decoding outcomes, decode every descriptor, count, and rank. Unrank
each selected interval's binary sequence independently. During the global
left-to-right scan, compute the current cell before reading its outcome. If
the cell lies in a selected interval, consume the next bit from that
interval's unranked sequence. Otherwise consume the next residual baseline
outcome. Disjointness makes the source stream unique, while the stored
cardinalities detect underrun or unused bits. Thus temporal interleaving does
not impair exact reconstruction.

There are \(M(M+1)/2\) interval branches. Prefix sums provide each
\((N_I,E_I,C_I)\) in constant time, giving \(O(M^2)\) arithmetic operations.
The value and predecessor arrays use \(O(M)\) storage.
