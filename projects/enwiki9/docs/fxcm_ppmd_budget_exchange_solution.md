# Solution: Exact Component-Budget Exchange

Subtracting the original component-B allocation from the budget inequality
gives

```text
u(q'-q) <= (a-b)N.
```

Because `q'-q` is integral,

```text
q'-q <= floor((a-b)N/u).
```

Equality is feasible by the defining property of the floor, so the unique
largest allocation is

```text
q' = q + floor((a-b)N/u).
```

Euclidean division gives

```text
(a-b)N = u floor((a-b)N/u) + r
```

for a unique residue `0<=r<u`. Hence `r=(a-b)N mod u` is exactly the unused
budget. Adding one more unit would cost `u-r>0` bytes beyond the budget, which
proves maximality.

A canonical construction performs one Euclidean division and emits the
quotient, residue, and `q'`. A verifier recomputes those integers and checks
the original inequality and failure of the inequality at `q'+1`.

## Frozen result

The tight-cell representation releases:

```text
(96-92) * 27,955,200 = 111,820,800 bytes.
```

This is exactly:

```text
111,820,800 / 1,024 = 109,200 KiB.
```

Therefore:

```text
q' = 20,352 + 109,200 = 129,552 KiB
residual budget = 0 bytes
```

The resulting static payload exchange is exact. It earns zero score and
resource credit before SLC archive identity and native codec gates.
