# FXCM Joint Budget Composition Problem

## Status

This is an independent finite resource-allocation problem. Its conclusion
licenses one source construction but earns zero compression credit without a
native exact gate.

## Given

All quantities are nonnegative integers measured in bytes.

- A baseline simultaneously resident arena payload `A0`.
- A semantics-preserving layout saving `S`.
- A mandatory capacity restoration costing `C`.
- A fungible arena whose capacity may grow in quanta of `Q`.
- A certified available memory margin `M`.
- A reserve `G` that must remain unused.

The composed static payload delta for `n` fungible quanta is

```text
Delta(n) = C - S + n Q.
```

The static admission condition is

```text
Delta(n) <= M - G.
```

The application instance uses:

```text
S = 111,820,800
C = 192,937,984
Q = 1,048,576
n = 24
```

Here `S` is the exact saving from 92-byte rather than 96-byte FXCM cells,
`C` restores the complete `idx13` table, and the 24 quanta add 24 MiB to the
PPMD arena.

## Questions

1. Prove that a feasible allocation exists exactly when `C - S <= M - G`.
2. When feasible, derive the largest admissible integer `n`.
3. Prove the unused residual margin after choosing that `n`.
4. Compute the exact static payload delta of the application instance.
5. State precisely what additional evidence is required before the
   construction can be called resource-eligible or compression-positive.

## Transfer reduction

The construction maps to a candidate with:

```text
CMIX_FXCM_CMC2_TIGHT=1
CMIX_FXCM_CMC2_IDX13_DIV=1
CMIX_PPMD_MEMORY_KB=44928
```

The theorem licenses only the requested-payload arithmetic. A guarded native
run must still measure peak RSS, exact archive bytes, deterministic re-encode,
and roundtrip reconstruction.
