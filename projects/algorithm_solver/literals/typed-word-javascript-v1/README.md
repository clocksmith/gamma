# Typed semantic words: JavaScript backend v1

The existing 6/7/8-bit semantic packets now have a deterministic, standalone
JavaScript backend. It compiles the decoded primitive graph, rather than looking
up an answer, spelling source, or generating a new algorithm. Recipes have
already been expanded and charged by the frozen packet codec.

This closes the Python-only execution gap for authored development graphs. It
does **not** establish dual-language catalogue qualification, 1,000-solution
coverage, autonomous composition, unseen generalization or human fluency.

## Components and preserved contracts

- [`typed_word_javascript.py`](../../algsolve/synth/typed_word_javascript.py)
  decodes and validates a packet before emitting a standalone ES module.
- [`typed_word_javascript_runtime.mjs`](../../algsolve/synth/typed_word_javascript_runtime.mjs)
  provides the arithmetic, collection and resource primitives embedded in each
  emitted module. It has no imports, I/O, source evaluation or answer table.
- The frozen [`typed_word_codec.py`](../../algsolve/synth/typed_word_codec.py),
  `typed_program.py`, `typed_vector_program.py`, historical receipts and packet
  identities remain unchanged. Both `base-v2` and `vector-v1` are supported.

All 53 base entries and 57 vector entries remain unchanged at every width.
Seven/eight-bit selections do not yet add richer operations. The backend adds
no hidden binding, constant, source or recipe channel to packets.

The compiler only accepts canonical graphs from the existing decoder. Binding
names are its hygienic `b0`, `b1`, ... indices, not user-supplied source strings.
The emitted module contains ordinary lexical declarations, branches, loops and
explicit primitive calls. It exports `solve(positionalInputs, budget=100000)`
and a frozen provenance descriptor. `emit(packet)` returns `(source, receipt)`.
It does not execute the source or invoke a native judge.

## JavaScript value and ownership contract

- Every language integer is a **BigInt**, with magnitude less than `2^128`,
  matching Python's bounded integer domain. Number values are rejected rather
  than silently rounded. Booleans are distinct from integers; unit is `null`.
- Lists and tuples are JavaScript arrays checked against the complete static
  type. Nested values and tuple arity are checked. Collection capacity is 20,000.
- Every invocation checks its ordered input arity, validates values and copies
  input arrays. Results cannot mutate caller inputs or another invocation.
- Mutable scalar cells compile to lexical `let`; immutable bindings compile to
  `const`. Branch and loop locals cannot escape their validated scopes.
- DSU, heap, queue, map and vector handles are fresh branded resources. They
  cannot cross program boundaries or alias through ordinary values. Snapshots
  are independent arrays; appending to a vector cannot change old snapshots.
- Heap operations are binary-heap O(log n). Queue operations are amortized O(1),
  with consumed storage reclaimed. DSU preserves union-by-size without path
  compression. Reverse sorting remains stable for equal keys.

Statements, expressions, loop iterations and primitive work receive the same
declared operation charges as the Python interpreter. Budgets are integer
Numbers from 1 to 2,000,000. Capacity and charged mutation checks happen before
mutation, and failures do not leak state into a later call. These charges are
research work units, not equal wall time or machine-instruction counts.

This BigInt interface is not an ordinary LeetCode Number interface. Any native
problem adapter must separately define integer conversion, return serialization,
domain and complexity requirements, and obtain fresh language-specific receipts.

## Fully charged storage

Each receipt reports:

1. The existing packet's exact selections, operand/control words, frame, padding
   and total bits.
2. Dictionary, Python decoder, Python runtime, package initializers, JavaScript
   emitter and JavaScript runtime source bytes needed to produce JavaScript
   from that packet.
3. Exact standalone emitted-source bytes, already including its JavaScript
   runtime, plus a SHA-256 of that complete source.

The packet-with-emission-toolchain package and the standalone module are
**alternative representations**, not two costs to add together. Batch receipts
charge shared toolchain source once, each profile's dictionary/runtime once,
and each packet once. A batch of standalone modules pays for the runtime in
each module; no unimplemented shared-module optimization is credited.

Receipts bind packet, dictionary, Python runtime/decoder/package initializers,
JavaScript runtime/emitter and output hashes. Python/Node binaries and standard libraries
are external environment dependencies, not measured deployment bytes. Search,
emission latency, keystrokes, navigation and human time are not measured.

## Reproducible evidence

Run from the repository root:

```sh
PYTHONPATH=projects/algorithm_solver python3 -m unittest \
  projects/algorithm_solver/tests/test_typed_word_javascript.py \
  projects/algorithm_solver/tests/test_typed_word_javascript_primitives.py \
  projects/algorithm_solver/tests/test_typed_word_codec.py \
  projects/algorithm_solver/tests/test_typed_vector.py \
  projects/algorithm_solver/tests/test_typed_program.py
python3 projects/algorithm_solver/literals/typed-word-javascript-v1/measure.py
```

[`synthetic-evidence.json`](synthetic-evidence.json) records 12 explicitly authored
graphs at all three widths, 36 Python/JavaScript expected-result checks. The
graphs include 128-bit constants, mutable accumulation, map default behavior,
independent vector snapshots, minimum/maximum forests, component counts, rejected
edge weights, heap sort, stable unique and two different sort/unique compositions.
These are 12 graph fixtures, **not 12 independently qualified problems**.

Focused tests additionally cover deterministic emission, every pure/effect
operation, alpha-renaming, lexical scope, exact budget exhaustion, numeric
overflow, malformed packets, input preservation, fresh repeated calls, empty
resources, 20,000/20,001 capacity limits, full-map overwrites, queue drain/refill,
stable scalar sorting and 160 seeded differential recipe inputs. Direct primitive
tests retain independently reproducible boundary and budget-mutation probes.

Only authored synthetic graphs and test inputs are executed by these software
tests. They do not load corpus sources or private cases, alter protected
reservations, produce native qualification receipts, or replace the judge.

Local verification: 52 focused unit tests passed across the JavaScript backend,
packet codec and existing typed runtimes. This includes 597 direct pure-operation
cases and 18 effect traces with exact budget/failure-state comparisons. Python
syntax and Node syntax checks passed; the 36-row receipt replay was byte-identical.
The broader `tests/test_algorithm_solver_lane.py` command could not start because
this environment has no pytest. No replacement test framework or native-judge
workaround was used, and no broad lane/release acceptance is claimed.

## Remaining qualification work

The existing dot native-judge attempt remains blocked by Bubblewrap's
`NETLINK_ROUTE` setup failure. This backend does not retry, weaken or replace
that boundary. Native judge/lane acceptance, pinned problem interfaces and
independently sealed native tests are still required before any catalogue
coverage can be promoted. No JavaScript/Python source-qualification claim or
M1–M6 completion follows from these development checks.

Component intent is preserved: additive research backend and explicit evidence,
with no change to Gamma's protected populations, production authority, native
sandbox policy or publication boundaries.
