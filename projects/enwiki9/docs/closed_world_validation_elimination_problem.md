# Closed-World Validation Elimination

## Status

`CWVE-1` is an independent finite-program problem. It concerns validation of
an immutable internal package object, not validation of external input bytes.

## Definitions

Let a deterministic wrapper \(W\) contain an immutable byte object \(A\) whose
bytes and hash are part of the counted package. Before using \(A\), the wrapper
evaluates pure predicates

\[
P_1(A),\ldots,P_k(A)
\]

and aborts if any predicate is false. Assume every predicate is total, has no
side effects, and evaluates true on the unique packaged object \(A\).

Let \(W'\) be obtained by deleting those predicate evaluations and false
branches while preserving the successful-path operations and their order.
External corpus input, archive input, arithmetic checks, and output checks are
outside the removable predicate set.

## Questions

1. Define the closed-world state relation between \(W\) and \(W'\).
2. Prove a trace bisimulation on the unique package object \(A\).
3. Extend the proof to bounds and path-safety checks when a finite certificate
   proves every checked relation on \(A\).
4. State why the theorem does not license removing checks on external input or
   mutable package objects.
5. Give a finite validation-elimination certificate.
6. Derive exact package-score transfer when all successful-path outputs and
   every other package byte agree.
7. State the native evidence still required for a compression candidate.

## Frozen intended instance

The internal object is the exact `269455`-byte migrated FCF/BPDQ B2 closure.
The removable checks cover its FCF magic, bounds, unique safe member paths,
trailing position, BPDQ header, record nonemptiness, and prefix lengths. The
source closure remains immutable and hash-bound. Corpus and archive bytes
remain external and are not trusted by this theorem.

