# Solution: Budget-Preserving Capacity

For table `i`, feasibility gives

```text
m_i <= (a n_i) / b.
```

Since `m_i` is integral,

```text
m_i <= floor(a n_i / b).
```

The right side is feasible because the defining property of the floor gives

```text
b floor(a n_i / b) <= a n_i.
```

Therefore

```text
m_i* = floor(a n_i / b)
```

is the unique largest feasible value in coordinate `i`. The constraints are
separable, so `m*` dominates every feasible vector coordinatewise. It
therefore maximizes the sum and every objective that is nondecreasing in each
coordinate.

Because `n_i` is an integer,

```text
m_i* - n_i
  = floor(a n_i / b) - n_i
  = floor((a-b)n_i / b).
```

Euclidean division gives unique integers `m_i*` and `r_i` such that

```text
a n_i = b m_i* + r_i,  0 <= r_i < b.
```

Thus `r_i=(a n_i) mod b` is exactly the unused payload. A canonical
construction visits tables in their supplied order, computes one Euclidean
division per table, and emits `(m_i*,r_i)`. A verifier recomputes the
division, checks `m_i* >= n_i`, checks `b m_i* <= a n_i`, and checks that
`b(m_i*+1) > a n_i`.

## Frozen FXCM result

For `a=96` and `b=92`, the new capacities are:

```text
2188332 4376665 2188332 2188332 2188332 2188332
4274 547083 1094166 2188332 2188332 2188332
2188332 2188332 547083 34192 136770 547083
```

The exact totals are:

```text
old cells       27,955,200
new cells       29,170,636
added cells      1,215,436
old payload  2,683,699,200 bytes
new payload  2,683,698,512 bytes
slack                   688 bytes
```

No table exceeds its previous 96-byte-per-record payload budget. This is an
allocation theorem only and earns zero compression or resource credit.
