# Slack-Funded Capacity Restoration Problem

## Problem

A baseline has `N` records of width `a`, including a designated table whose
capacity was reduced from `2M` to `M`. A compact observationally equivalent
representation has width `b<a`. Restoring the designated table adds `M`
records.

Prove:

1. The compact baseline releases exactly `(a-b)N` payload bytes.
2. Restoration costs exactly `bM` payload bytes.
3. The restored compact construction differs from the original baseline by
   `Delta=bM-(a-b)N` payload bytes.
4. If an independently certified resource headroom `H` upper-bounds every
   unmodeled difference and satisfies `H>=max(0,Delta)`, then the restoration
   fits the same resource ceiling.
5. Give a canonical finite verifier for the payload calculation.

## Frozen FXCM instance

Use:

```text
N = 27,955,200
a = 96
b = 92
M = 2,097,152
```

The designated table is ContextMap2 index 13, currently compiled with divisor
two. The construction restores its divisor to one without changing any other
table cardinality or index rule.

## Transfer boundary

The headroom implication is conditional. Static payload is not measured RSS,
and no current process sample is a terminal resource certificate. Native RSS,
archive, roundtrip, determinism, and runtime remain authoritative.
