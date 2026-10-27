# Batch 2 candidate checkpoint

61 original JavaScript/Python pairs (122 source files), based on commit `62f8d1e2b375ab1c576a412be06adeddb5bcbffe`. All 61 identities passed the existing configured boundary gate before problem definitions were opened. There are no unresolved identities or unsupported contracts in this batch.

These are authored candidates, not admissions or independently qualified solutions. The manifest records ordered argument names, complexity, adapters, source hashes, exact contract URLs and test counts for each ID. The official LeetCode contract is supplemented by identity-bound publicly accessible doocs definition documentation (CC-BY-SA-4.0 upstream documentation). No downloaded statement body, editorial, or copied implementation is included.

## Interfaces

JavaScript exports `solve` with `module.exports`; Python exports `solve`. Arguments are positional and are not mutated. Stateful design problems use explicitly documented operations/arguments tapes, returning null/None for constructors and void operations. Tree problems use nullable breadth-first serialized arrays; linked-list problem 3063 uses a value-array adapter and returns frequency values in first-occurrence order. These adapters do not claim native object-identity qualification.

## Reproduce

From repository root:

```sh
python projects/algorithm_solver/catalogue/authored/request-506-v1/batch2/test_candidates.py
```

Requires standard-library Python and Node, with no downloaded dependencies. The deterministic run checks 1,772 cases in both languages (3,544 executions), 61 Python syntax compilations and 61 Node syntax checks, and input non-mutation. Every ID has independent bounded oracle checks. Public-example/hand-checked fixtures, independent oracles, cross-language parity, maximum-shape checks and numeric edges are separately counted. Selected large cases exercise 100,000-node trees, 100,000-element arrays, 30,000-character substring counts, 1,000-by-1,000 dynamic-programming work and JavaScript integer precision boundaries. The checks are not a complete proof or hidden-judge execution. Source, fixture and test-script hashes bind the receipt to this exact checkpoint.

`cases.json` is executable test data with contract/interface metadata; `manifest.json` is the per-ID disposition and evidence index; `test-results.json` is the reproducible local receipt. `access.json` records the pre-open boundary configuration; `contract-provenance.json` records definition URLs and acquired-definition hashes, not statement bodies.
