# Owned-vector semantic successor

This synthetic development extension removes repeated immutable-list copying
from the authored heap-sort and stable-unique recipes. It is an actual executable
semantic primitive, not a source-text fragment or a hidden whole-answer lookup.
No new problem qualification or autonomous solving is established.

## Version and ownership contract

The existing `typed_program.py`, `typed_recipes.py`, `typed_codec.py`, frozen
`typed_codec_v1.json`, targets, checkpoints and historical evidence are unchanged.
The additive successor comprises:

- [`typed_vector_program.py`](../../algsolve/synth/typed_vector_program.py):
  `algsolve.typed-program.vector.v1`, a standalone versioned interpreter.
- [`typed_vector_recipes.py`](../../algsolve/synth/typed_vector_recipes.py):
  heap-sort and stable-unique use an owned vector and one final snapshot.
- [`typed_vector_codec.py`](../../algsolve/synth/typed_vector_codec.py):
  a separately pinned descriptor, target/expansion binding and standalone adapter.

The runtime snapshot intentionally preserves the frozen predecessor rather than
changing its implementation beneath its source-hash-bound receipts. New targets
must explicitly use the successor schema. Neither old nor new interpreters accept
the other's schema. The successor is Python-only; no JavaScript equivalence is
implied. Future shared fixes must be reviewed for each version separately.

`vector.new` allocates a fresh lexical `vector_int` resource. `vector.append`
accepts one bounded integer, charges one operation before mutation and fails
before exceeding the 20,000-element capacity. `vector.snapshot` charges the
current length before allocation and returns an independent ordinary list. The
handle remains usable; later appends cannot change an earlier snapshot.

Resources cannot alias through ordinary bindings, appear inside values, cross
program inputs/outputs or be captured as recipe ports. They cannot occur in
pure expressions. All primitive calls retain explicit effect ordering, type and
scope checks. Each invocation gets fresh resources, including after failure.
Existing input-copy, integer, graph and execution budgets remain in force.

The amended heap-sort recipe has O(n log n) heap work and O(n) output building,
with O(n) owned storage. Stable-unique has expected O(n) map/queue/vector work
and O(n) owned storage. These are implementation complexity reviews, not proofs
that a named problem's complete bounds or interface are qualified.

## Evidence and representation costs

[`results.json`](results.json) retains code identities and ten matched synthetic
measurements at sizes 128, 256, 512, 1024 and 2048. Inputs are descending integer
lists; expected outputs come from `sorted` and insertion-preserving deduplication.
Every row passed. At 2048 elements:

- Heap-sort: 2,161,690 legacy charged operations versus 65,563 successor operations.
- Stable-unique: 2,143,247 versus 47,120 charged operations.

The operation counts include declared primitive work and interpreter dispatch,
not hardware instructions. Wall times are one local observation per arm/size,
including validation/setup, not a latency qualification. The measurement uses a
large explicit diagnostic budget to retain legacy costs beyond its ordinary
2,000,000-operation adapter budget.

The JSON codec reports exact target, descriptor, runtime, recipe and complete
standalone-source storage. The standalone package already embeds runtime,
recipes and target; constituent costs are not added twice. JSON sizes are not
6/7/8-bit input selections, and no human input-time measurement is claimed.
A separate fixed-codeword representation must account for its own operands,
framing and decoder before making such claims.

## Focused checks

From the Gamma root:

```sh
PYTHONPATH=projects/algorithm_solver python3 -m unittest \
  projects/algorithm_solver/tests/test_typed_vector.py \
  projects/algorithm_solver/tests/test_typed_program.py
python3 projects/algorithm_solver/findings/typed-vector-development-v1/measure.py
```

The 24 tests cover existing authored synthetic recipes and their expansions,
empty/duplicate/negative/extreme integers, snapshot independence, fresh calls,
wrong ports and effects, alias/escape rejection, lexical hygiene, operation
budget failure, 20,000-element success and 20,001-element input rejection,
capacity overflow before mutation, deterministic work growth, codec identity
and standalone synthetic replay. Adapter runtime names cannot be shadowed by
public arguments; noncanonical Python identifier spellings, normalized keywords
and collisions fail closed. They load no protected sources or cases.

Historical `typed-real-dev-v5` explicitly excludes sorting problem `lcd:912`
for quadratic output copying. This change addresses that mechanism but does not
remove its historical exclusion or qualify a new solution: fresh independently
sealed native tests, full input-bound and complexity review, source/interface
bindings and language-specific receipts remain necessary. The collection bound
also remains 20,000 and must not be mistaken for support of larger domains.

The allowed historical exclusion metadata provides no maximum length for
`lcd:912`; its catalogue index has no bound fields and `contract_path: null`.
The 20,000 capacity has therefore not been silently expanded or represented as
meeting that problem's complete input domain. A pinned permitted contract is
needed before choosing and validating a larger successor capacity.
