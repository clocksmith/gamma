# Requested IDs589–725:39 original Python/JavaScript candidate pairs

Component: Algorithm Solver candidate authoring. Intent preserved. No admission,
qualification, training, serving-policy change, or protected benchmark-case access.

This cohort follows `authored/continuation-l-20261028-v1/` layout. Its exact39 IDs
are in `contracts.json`, with78 standalone sources,78 semantics records, official
interfaces and source-response hashes. No existing candidate source was imported.
Only official public definitions/stubs and source-access metadata were read.
Full official responses remain in ignored local
`projects/algorithm_solver/data/authoring/continuation-data-structures39-20261028-v1/`.

## Interfaces and effects

Function problems expose module-level `solve` in official positional parameter
order, plus Python `Solution` methods and JavaScript named official wrappers.
Class problems expose the official constructor/methods and an operation-trace
`solve(operations, arguments)` adapter (`args` in strict JavaScript). Constructor
and method argument order is preserved; void results normalize to null.

Development adapters build native binary/N-ary/list/Employee objects. The official
metadata's manual placeholder types for589/590/690 are retained and explicitly
annotated rather than treated as executable scalar interfaces. C-only size
parameters in703/710 are not Python/JavaScript arguments.

Inputs remain unchanged.617/623/654/701/725 allocate fresh output nodes;652 and700
may return existing unchanged subtree roots.701 comparison checks strict BST
ordering and exact contents, allowing the official freedom in resulting shape.
652 compares distinct subtree shapes without ordering;721 compares account groups
without ordering.637 uses absolute tolerance1e-5.710 checks output support and an
exhaustive small-domain injected-ticket bijection, not matching random sequences
or claiming empirical RNG quality. Its uniformity argument assumes uniform RNG.

705/706 use direct-address byte/int arrays, respecting the prohibition on built-in
hash tables.707 uses owned linked nodes. Inputs are never sorted or rewired in place.
Deep-tree algorithms use explicit stacks/queues. Numeric operations stay within
exact Number integers, except679, which deliberately uses BigInt rational arithmetic
matching Python Fraction.662 normalizes positions each level.

## Independent development checks

`oracles.py` imports no candidates. It uses bounded exhaustive models, separate
representations and independent structural/analytic maximum cases. Examples include
all course subsets, list Cartesian products, literal subtree shapes, full printing
state BFS, Floyd-Warshall, expression-tree enumeration, graph distances, nonoverlap
triples, coordinate-cell simulation and literal class-state models. Large cases use
explicit constructions, matrix powers or Euler pentagonal coefficients; they do
not pretend to run an exponential oracle over maximum inputs.

Every ID has a maximum-domain case.655 uses1023 nodes at depth10 because a binary
tree cannot simultaneously attain the statement's1024-node ceiling and depth10.
The623 deepest-row fixture was corrected by explicit node-table construction after
the first development run exposed a missing serialized null. A small regression
retains that case. No candidate or tolerance was changed to fit that fixture.

The initially selected folder collided with a concurrent task for different IDs.
Only this task's files were moved here; the other task's references were preserved.
`pre-source-reference-freeze.json` retains the original historical freeze hashes;
`reference-recovery.json` explains reconstruction after candidate drafting. The
reconstructed reference files must not be described as the original frozen bytes.

Run from the cohort directory:

```bash
python3 -m unittest discover -s . -p 'test_*.py'
python3 build_metadata.py
shasum -a 256 -c SHA256SUMS
```

`checks.json` records actual local development results. The Node vm harness is not
a security or qualification boundary. Passing finite tests does not qualify sources,
recognition, complexity, official judge behavior or production serving. All78
variants retain qualification status unknown and no preferred variant is promoted.

`build_metadata.py` refreshes semantic source hashes, the authoring catalogue,
manifest and SHA256SUMS. Generated expected packets stay out of Git. Unrelated
cohorts and frozen catalogue universes are unchanged.
