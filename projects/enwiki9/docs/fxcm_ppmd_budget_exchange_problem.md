# Exact Component-Budget Exchange Problem

## Problem

Component A contains `N` records of `a` bytes. An observationally equivalent
representation uses `b<a` bytes per record. Component B currently has `q`
integer allocation units, each costing exactly `u` bytes. All other payload
terms are fixed.

Choose the largest integer `q' >= q` such that replacing A and enlarging B
does not increase their combined payload:

```text
bN + uq' <= aN + uq.
```

Prove:

1. The unique largest feasible allocation is
   `q'=q+floor((a-b)N/u)`.
2. Its residual unused budget is `(a-b)N mod u`.
3. No larger allocation can satisfy the budget.
4. Give a canonical construction and finite verifier.

## Frozen FXCM/PPMD instance

Use:

```text
N = 27,955,200 ContextMap2 cells
a = 96 bytes
b = 92 bytes
q = 20,352 KiB
u = 1,024 bytes per KiB
```

Report the exact new PPMD allocation.

## Transfer boundary

The theorem concerns declared payload bytes only. It does not prove allocator
overhead, measured RSS, archive improvement, runtime eligibility, or
observational equivalence of the compact representation. The latter is a
separate SLC antecedent, and all physical claims require native receipts.
