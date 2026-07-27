# FXCM Balanced-Minimum Tie Problem

## Status

This is an independent finite selection problem with a direct deterministic
FXCM transfer. It changes no table size and earns zero compression credit
without native replay.

## Given

Let `A >= 3` slots have integer priorities `p[0], ..., p[A-1]`. At most two
slot indices are protected. Let `E` be the nonempty set of unprotected slots
having minimum priority among all unprotected slots.

Write:

```text
m = |E|
```

and list `E` in increasing slot order:

```text
e[0] < e[1] < ... < e[m-1].
```

For a 16-bit checksum `h`, define:

```text
select(h) = e[h mod m].
```

## Questions

1. Prove that `select(h)` is always unprotected and has minimum eligible
   priority.
2. Prove that, as `h` ranges over all `2^16` checksum values, every member of
   `E` is selected either `floor(2^16 / m)` or `ceil(2^16 / m)` times.
3. Prove that the maximum selection-count imbalance between tied slots is one.
4. Give a deterministic constant-space algorithm using at most two scans of
   the `A` slots.
5. Prove by induction that encoder and decoder remain synchronized when they
   use this rule and begin with identical state.

## FXCM transfer

In `E1::get`, checksum hits retain the existing behavior. On a miss:

1. scan once to find the minimum eligible priority and count its ties;
2. compute `h mod tie_count`;
3. scan in canonical slot order to select that tied rank.

The current lowest-index tie rule is the matched control. The candidate changes
only replacement tie selection; table sizes, checksums, state transitions, and
arithmetic coding remain unchanged.
