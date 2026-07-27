# Solution: FXCM Joint Budget Composition

## 1. Feasibility

For every integer `n >= 0`,

```text
Delta(n) = C - S + n Q >= C - S
```

because `Q >= 1`. Therefore no allocation is feasible when

```text
C - S > M - G.
```

Conversely, if `C - S <= M - G`, choosing `n = 0` satisfies the admission
condition. Hence feasibility is equivalent to

```text
C - S <= M - G.
```

## 2. Largest fungible allocation

Assume feasibility. Rearranging the admission condition gives

```text
n Q <= M - G - C + S.
```

Since `n` is a nonnegative integer and `Q` is positive, the largest admissible
value is

```text
n* = floor((M - G - C + S) / Q).
```

This value is feasible by the definition of the floor. Increasing it by one
would require more than the available margin, so it is maximal.

## 3. Residual

Define

```text
R = M - G - Delta(n*).
```

Euclidean division gives

```text
0 <= R < Q.
```

Thus the maximal quantized allocation leaves a nonnegative residual smaller
than one allocation quantum.

## 4. Application arithmetic

The restored `idx13` table minus the tight-cell saving costs:

```text
192,937,984 - 111,820,800 = 81,117,184 bytes.
```

The PPMD increase costs:

```text
24 * 1,048,576 = 25,165,824 bytes.
```

Therefore the joint static payload delta is:

```text
81,117,184 + 25,165,824 = 106,283,008 bytes
```

or exactly:

```text
106,283,008 / 1024 = 103,792 KiB.
```

The PPMD arena grows from `20,352 KiB` to:

```text
20,352 + 24,576 = 44,928 KiB.
```

## 5. Transfer boundary

The proof establishes exact static requested-payload arithmetic only. It does
not establish:

- allocator and page-rounding overhead;
- process-tree or single-process peak RSS;
- archive improvement;
- deterministic arithmetic-coder behavior;
- exact reconstruction;
- source-package cost;
- runtime eligibility.

The candidate receives zero score credit until a native guarded gate supplies
all applicable receipts. Final eligibility still requires complete full-corpus
execution under the official resource rules.
