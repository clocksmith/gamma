# BF-1 Solution: Amortized Prior-Block Fibers

Equality of fixed-length block contents is an equivalence relation, so its
classes form the unique disjoint partition.

For fixed cardinality \(k\), all candidate sets pay the same descriptor and
rank prices. If a selected block has smaller cost than an unselected block,
exchanging them increases the saving. Repeated exchanges prove that the
top-\(k\) costs are optimal. Sorting by decreasing cost and then increasing
index makes the choice canonical.

Let \(P_k\) be the prefix sum of those sorted costs. The best nonempty class
value is

\[
\max_{1\le k<m}\left(P_k-d-
\left\lceil\log_2{B-1\choose k}\right\rceil\right).
\]

Compare it with the empty value zero. Prefer the empty choice on a zero tie,
and otherwise the least \(k\) attaining the maximum. This is the deterministic
inclusion-minimal class optimum.

Different content classes contain disjoint block positions, and their stated
prices do not interact. Therefore summing the independent class optima is
globally optimal for this code family.

Decode every selected target subset first. Scan aligned block positions.
An unselected position consumes one literal block. A selected target copies
the already decoded first class occurrence. The first occurrence cannot be a
target, and every copied block has identical contents. Finally append the
literal tail. Induction over block positions proves exact reconstruction.

Hashing blocks constructs classes in expected \(O(B)\) time. Sorting all
class targets costs \(O(B\log B)\) in the worst case. Prefix scans are linear.
The representation and reconstruction use \(O(B)\) storage.
