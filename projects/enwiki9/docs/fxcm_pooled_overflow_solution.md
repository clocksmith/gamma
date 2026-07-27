# PO-1 Solution: Pooled Overflow for Uneven Buckets

## 1. Required overflow

Bucket \(i\) can retain

\[
\min(n_i,a)
\]

entries privately. Its excess is

\[
(n_i-a)_+=\max(0,n_i-a).
\]

Since an overflow slot stores one excess entry and may serve any bucket, the
minimum pool size that retains every entry is

\[
\boxed{
R_a(n)=\sum_{i=1}^{B}(n_i-a)_+.
}
\]

Necessity follows because no excess entry fits privately. Sufficiency follows
by assigning one distinct overflow slot to every excess entry.

## 2. Maximum retained count

The private arrays retain

\[
L_a(n)=\sum_{i=1}^{B}\min(n_i,a).
\]

There are \(R_a(n)\) excess entries, of which the pool retains at most
\(\min(P,R_a(n))\). Therefore the exact optimum is

\[
\boxed{
L_a(n)+\min(P,R_a(n)).
}
\]

It is attained by filling private slots first and assigning pool slots to any
fixed ordering of the excess entries.

## 3. Global slot optimality

Let

\[
N=\sum_i n_i.
\]

Every entry is either private or excess, so

\[
N=L_a(n)+R_a(n).
\]

Using \(K=aB+P\), note first that \(L_a(n)\le aB\). Then

\[
\begin{aligned}
L_a(n)+\min(P,R_a(n))
&=
\min(L_a(n)+P,L_a(n)+R_a(n))\\
&=
\min(L_a(n)+P,N).
\end{aligned}
\]

If some private slots are unused, then \(L_a(n)<aB\). Those unused slots occur
only in buckets with \(n_i<a\), while excess occurs elsewhere. The physical
model in the problem does not allow an unused private slot to change owners.
Consequently the expression need not equal \(\min(N,K)\) for arbitrary
\(a,B,P,n\).

An explicit counterexample is

\[
B=2,\quad a=2,\quad P=0,\quad n=(0,4).
\]

Here \(K=4=N\), but private allocation retains only two entries.

Thus clause 3, as posed, is false.

The corrected globally pooled model must permit all \(K\) slots, including the
nominal private slots, to be reassigned among buckets. Under that stronger
model, no bucket-specific constraint remains, and the exact optimum is

\[
\boxed{\min(N,K).}
\]

For the original private-plus-overflow model, the exact answer remains

\[
\boxed{
L_a(n)+\min(P,R_a(n)).
}
\]

This distinction is operationally important: a small overflow pool does not
magically reclaim unused slots embedded in fixed private cells.

## 4. Uniform unpooled allocation

With \(k\) fixed slots per bucket and no pool, the retained count is

\[
\boxed{
U_k(n)=\sum_i\min(n_i,k).
}
\]

It loses entries exactly when some bucket is overloaded:

\[
U_k(n)<N
\quad\Longleftrightarrow\quad
\exists i:\ n_i>k.
\]

It can lose entries even when its total slot count is sufficient:

\[
kB\ge N
\]

and

\[
\max_i n_i>k
\]

may hold simultaneously. Equivalently, the representation has stranded free
capacity:

\[
\sum_i(k-n_i)_+>0
\]

while another bucket has excess.

The private-plus-overflow layout retains all entries exactly when

\[
\boxed{P\ge R_a(n).}
\]

## 5. Canonical allocation

Order buckets by identifier and entries within each bucket by the frozen entry
order.

1. Put the first \(\min(n_i,a)\) entries of bucket \(i\) in its private slots.
2. List all remaining entries in bucket-major order.
3. Put the first \(\min(P,R_a(n))\) listed entries in overflow slots
   \(0,\ldots,P-1\).
4. Drop the remaining excess entries.

The allocation is finite, deterministic, and reconstructible from the bucket
contents and the frozen orders. An overflow record must identify its owning
bucket unless the physical index itself encodes ownership.

## 6. Weighted entries

Let entry \(e\) have nonnegative weight \(w_e\). Private and overflow placement
now interact: assigning a low-weight entry privately may displace a high-weight
entry from the limited overflow pool.

An exact finite optimizer enumerates, for each bucket, every subset of at most
\(a\) private entries. For each resulting choice:

1. collect all unselected entries;
2. retain the \(P\) greatest-weight remaining entries in overflow, resolving
   ties canonically;
3. sum private and overflow weights;
4. retain the lexicographically first maximum.

Because every bucket has at most \(A\) entries, the number of private choices is
at most

\[
\prod_{i=1}^{B}
\left(
\sum_{j=0}^{a}\binom{n_i}{j}
\right),
\]

which is finite. This proves existence and gives a constructive exact
algorithm, though not necessarily an efficient one.

If private placement is fixed by entry order, the optimum overflow selection is
simply the \(P\) highest-weight excess entries.

## 7. Transfer boundary

PO-1 proves allocation facts about abstract equal-sized slots. A cmix21
implementation must additionally count:

- overflow owner identifiers;
- per-bucket heads or ranges;
- links, indexes, and alignment;
- lookup and update instructions;
- extra source and package bytes;
- changed replacement and eviction behavior;
- cache locality and runtime;
- complete prediction feedback.

The false clause in the original problem is itself useful: fixed private cells
leave stranded capacity, so a valid implementation must either pay for a
sufficient overflow pool or redesign all slots as globally assignable.

Before implementation, Gamma must measure the actual overflow-demand
distribution

\[
R_a(n)
\]

on causal mature traces. Without that measurement, pooled overflow is only a
representation proposal with zero compression credit.

