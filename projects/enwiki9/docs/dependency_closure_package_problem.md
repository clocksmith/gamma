# Dependency-Closure Package Problem

## Problem

Let `G=(V,E)` be a finite directed graph. An edge `(u,v)` means that including
artifact `u` requires artifact `v`. Let `R` be a finite set of required roots.
A package `S` is dependency-closed when:

```text
R is a subset of S
```

and every edge leaving a vertex in `S` ends in `S`.

Prove:

1. The vertices reachable from `R`, including `R`, form a dependency-closed
   package.
2. Every dependency-closed package containing `R` contains that reachable
   set.
3. The reachable set is the unique inclusion-minimal valid package.
4. If every artifact has strictly positive cost, it is also the unique
   minimum-cost valid package.
5. Give a canonical traversal, package listing, and finite verifier.

## Frozen NC5 instance

The root is the CPU `nncp` build. Its dependency graph closes over:

```text
Makefile VERSION
nncp.c
cmdopt.c cmdopt.h
cp_utils.c cp_utils.h
arith.c arith.h
preprocess.c preprocess.h
cutils.c cutils.h
list.h
libnc.h libnc.so
```

CUDA libraries, documentation, changelogs, and an already-built executable
are not reachable build dependencies. Serialize the closure with sorted names,
zero timestamps, numeric owner/group zero, and gzip compression.

## Transfer boundary

This problem proves package closure, not codec quality or contest eligibility.
The final submission must additionally count launch wrappers and any required
framing, and must pass native build, decode, runtime, memory, and score gates.
