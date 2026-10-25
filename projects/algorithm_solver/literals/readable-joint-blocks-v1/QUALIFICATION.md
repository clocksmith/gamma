# Shared breadth traversal qualification contract

This three-problem pilot checks a source-side mechanism and the comparison harness.
It cannot qualify the frozen 500-problem M1 population. JavaScript and Python are
separate arms. The original six public readable-v1 programs remain unchanged.

## Sources, interfaces, and effects

`variants.py` emits two complete source choices per language/problem: original
and shared-breadth. Every successor stores its entire shared queue generator,
caller, callback, bindings, constants, syntax and official `Solution` wrapper.
There is no decoder substitution, runtime-injected helper, problem-ID dispatch,
lookup table, or source escape. The helper deliberately does not own discovery:
the caller's neighbor generator marks before yielding, preventing duplicate work.

- #547: symmetric binary adjacency matrix, nonempty and square, diagonal ones.
  Return connected-component count; preserve input values and ordered identities.
  Matrix scanning remains O(n squared) time, O(n) auxiliary space.
- #841: nonempty room-key lists with in-range integer destinations. Return whether
  all rooms are reachable from room zero; preserve values and ordered identities.
  Time remains O(V+E), auxiliary space O(V). Duplicate/self edges are tested too.
- #1091: nonempty square binary matrix. Return shortest eight-neighbor path length
  or -1. Preserve shape, ordered row/outer identities and existing ones; allow only
  zero-to-one discovery marking. Final matrix must exactly equal the predecessor,
  including early target termination and row-major neighbor order. Time and space
  remain O(n squared). Intermediate write-event timing is not a claim.

No claim of improved execution time follows: generators/callbacks may add overhead.
Integer indexes and result counts remain exactly representable in both languages
at the public problem bounds. No strings, Unicode normalization, exceptions outside
the stated domain, or arbitrary user-defined containers are admitted.

## Fresh correctness gate

Before dictionary fitting, record candidate/runner/oracle hashes and deterministic
case-generation seed in a new immutable run directory. Expectations stay in the
host comparator, not the candidate sandbox. Execute predecessors and successors
under the same isolated no-network, read-only runtime with bounded CPU and memory.
If that isolation is unavailable, fail closed and report a blocked qualification;
do not mark successors eligible from syntax checks or host execution.

Independent oracle mechanisms are union-find for components, iterative fixed-point
reachability for rooms, and priority-queue shortest distances for the grid. Test
exhaustive small legal inputs, seeded larger inputs, public samples, declared-bound
inputs and alias/effect controls. Retain every failing case and source identity.
Successful finite tests supply development evidence, not proof or corpus admission.

The grid with aliased input rows is an explicit predecessor-effect compatibility
control, not independent shortest-path evidence: mutation through one row can mark
another row's target before it is enqueued. It has no nonmutating oracle expectation.
The successor must match the predecessor's scalar result and final grid while
preserving identities. Independent-oracle and compatibility counts are separate.

No final-100 source/test, protected-66 source/test, model, training, private original
test, download, recognition artifact, deployment or BITS publication is involved.

## Versioned dot runtime continuation (2026-10-25)

The owner explicitly approved a pinned Node runtime mount. New runs may select
`--node-runtime` with the approved executable. The versioned `pinned_runtime`
adapter snapshots and hashes that executable, then directly executes it from one
read-only `/runtime/node` mount. The original sandbox, no-network namespaces,
read-only task files, private temporary directory, resource limits, host-only
expectations and process-group cleanup remain unchanged. Runtime bytes, dependency
closure and adapter identity are frozen before candidate execution. No ELF-loader
permission workaround is used. Historical blocked receipts remain unchanged.

`--language python` or `--language javascript` creates a language-scoped prerequisite
receipt containing only that language's sources. It cannot satisfy the paired
comparison gate. The default still requires both languages and all twelve rows.
