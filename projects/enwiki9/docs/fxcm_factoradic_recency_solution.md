# Solution to FRT-1: Factoradic Recency Tie-Breaking

## 1. Canonical ranking

Write \(f_i=(A-1-i)!\). At position \(i\), let \(d_i\) be the index of
\(\pi_i\) in the increasing list of ways not used at earlier positions. Then

\[
0\le d_i\le A-1-i
\]

and define

\[
\boxed{\operatorname{rank}(\pi)=\sum_{i=0}^{A-1}d_i(A-1-i)!}.
\]

Conversely, for \(0\le r<A!\), repeatedly set

\[
d_i=\left\lfloor\frac r{(A-1-i)!}\right\rfloor,
\qquad
r\leftarrow r\bmod (A-1-i)!,
\]

and remove the element at index \(d_i\) from the increasing available list.
The mixed-radix bounds make every removal legal. Euclidean division recovers
exactly the original digits, so rank and unrank are mutual inverses. This is
the lexicographic enumeration of \(S_A\).

## 2. Minimum fixed width

There are exactly \(A!\) states. An injective \(b\)-bit representation
requires \(2^b\ge A!\), hence

\[
b\ge\lceil\log_2(A!)\rceil.
\]

Binary encoding of the rank attains this bound. Therefore

\[
\boxed{b_{\min}=\lceil\log_2(A!)\rceil}.
\]

## 3. Move-to-front state machine

For access to way \(j\), remove \(j\) from its unique position in \(\pi\),
shift the preceding prefix right by one position, and insert \(j\) at position
zero. Call the resulting permutation \(F_j(\pi)\). The integer transition is

\[
\boxed{T(r,j)=\operatorname{rank}(F_j(\operatorname{unrank}(r)))}.
\]

Every operation is a function on a finite domain, and rank/unrank are
bijections, so \(T\) is deterministic and closed on \(\{0,\ldots,A!-1\}\).

## 4. Priority-compatible LRU replacement

Let \(m=\min_i p_i\) and \(M=\{i:p_i=m\}\). The set is nonempty. Scan
\(\pi\) from position \(A-1\) toward zero and select the first member of
\(M\). This is the unique member of \(M\) with greatest recency position and
therefore its least-recently used member. Since selection is restricted to
\(M\), the rule never replaces a way whose priority exceeds the minimum.

## 5. Stack-distance invariant

Initially the fixed permutation defines the order among never-accessed ways.
Assume the order is recency-correct before an access to \(j\). Move-to-front
places \(j\) ahead of every other way. It preserves the relative order of all
other ways, whose last-access times did not change. Thus the order remains
recency-correct by induction. A way at position \(r\) has exactly the \(r\)
ways preceding it accessed more recently, proving the claim.

## 6. Direct costs

Using an array-backed available list:

- rank performs at most \(A(A+1)/2\) equality inspections and \(A\)
  multiply-adds;
- unrank performs \(A\) divisions/remainders and at most
  \(A(A-1)/2\) element shifts;
- move-to-front performs at most \(A\) comparisons and \(A-1\) shifts;
- minimum-priority/LRU selection performs \(A-1\) priority comparisons and at
  most \(A\) membership checks.

For fixed \(A=10\), all costs are fixed constants. Faster tables or specialized
code do not alter the theorem.

## 7. Ten-way FXCM layout

\[
10!=3,628,800,
\qquad
2^{21}=2,097,152<10!<4,194,304=2^{22}.
\]

Hence exactly 22 bits are necessary and sufficient, and a 32-bit field is
ample.

The existing logical fields occupy:

\[
20\text{ checksum bytes}+1\text{ shared byte}+70\text{ state bytes}=91
\text{ bytes}.
\]

Their two-byte-aligned record size is 92. A four-byte field begins at the next
four-byte-aligned offset, 92, and ends at 96. The resulting record has size and
alignment

\[
\boxed{\operatorname{offset}(\text{rank})=92,\quad
|\text{record}|=96,\quad \operatorname{align}=4}.
\]

It therefore fits exactly in the already allocated 96-byte B2 cell and changes
neither bucket count nor dominant allocation.

## 8. Certificate and transfer

A finite certificate binds \(A\), factorials, rank byte order, initial rank,
cell offsets, transition code, and the priority/LRU rule. A verifier checks:

- \(\operatorname{rank}(\operatorname{unrank}(r))=r\) for every
  \(0\le r<A!\);
- representative or exhaustive move-to-front transitions;
- selected ways belong to the minimum-priority set and are latest in the
  reverse recency scan;
- scalar sizes, member offsets, record size, and alignment.

For encoder/decoder synchronization, induct on coded events. Equal prior state
and decoded history yield equal bucket, priorities, rank, hit/replacement way,
probability, update, and next rank. Thus both sides remain synchronized and
lossless. The archive may differ from B2 because tie eviction changes future
predictor state.

The native candidate is fail-closed:

1. compressed package growth must be at most 8,192 bytes over B2;
2. exact 250K roundtrip, deterministic replay, and decimal-memory guard pass;
3. the frozen 1M archive must beat B2 by at least 8 bytes;
4. exact 10M counted total must improve by at least 128 bytes before transfer;
5. all mandatory distant scopes must remain source-counted positive;
6. only complete full-corpus replay can receive Hutter score credit.
