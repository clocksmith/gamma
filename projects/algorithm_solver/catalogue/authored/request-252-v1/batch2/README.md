# Batch 2: seventeen requested candidate pairs

This batch supplies 17 original JavaScript/Python pairs against source base
`bc252ef318b165396288cd3f3d0ecbd4b84c03da`. All IDs were admitted for source/statement
access by the existing hash-pinned boundary before definitions were opened.
This is development-tested candidate work, not catalogue admission, semantic
qualification, hidden-judge acceptance, recognition qualification or serving.

Run `python3 batch2/test_candidates.py` from the request directory (or invoke
that script by absolute path). Python 3 and Node.js are the only requirements.
The deterministic seed is 252002. The test run covers **995 cases per language**,
**1,990 value assertions**, **1,990 input-mutation checks**, **six native-interface
assertions** and **34 syntax checks**. Exact counts, runtimes and hashes are in
`test-results.json`; the harness keeps expected outputs outside the JavaScript
runner. These are local development checks, not a claimed sandbox-judge run.

Each ID has public examples and 55 separately derived bounded oracle cases.
Oracles enumerate subsequence covers, ordered sequences, swap paths, edge-weight
assignments, doubling subsets, disjoint swap matchings/partitions, parity BFS,
removal candidates or simple direct models as appropriate. Large structured tests
cover 100,000-element inputs, a 100,000-node chain without recursion, exact values
beyond signed 32-bit range, a 1,500-element GCD case, 100-character edit cases and
the maximal magical-sequence dimensions. Finite evidence is not universal proof.

## Interfaces and provenance

All JavaScript modules export `solve`; Python modules define `solve`.
`manifest.json` binds argument order, constraints, effects, numeric/Unicode limits,
complexity, source hashes and definition provenance for every ID.

- **3217:** `solve(nums, head_values)` is a value-array transport adapter. The
  native `modifiedList(nums, head)` and `ListNode` are retained and tested
  separately for survivor identity and pointer rewiring. Only the native call
  mutates node links; array inputs are unchanged.
- **3484:** the native `Spreadsheet(rows)` and its methods remain available.
  `solve(operations, arguments)` uses a fresh instance and emits null for void
  operations. Only valid constructor/method tapes are in contract.
- **3539:** JavaScript uses BigInt for all modular products, returning a reduced
  Number; this prevents silent loss of integer precision.

Official LeetCode definitions supplied the public contracts except 3231 and 3237,
whose official definitions were premium/unavailable. Their exact-ID-bound public
doocs definition portions were consulted, with upstream CC-BY-SA-4.0 provenance,
URLs and acquired-byte/definition hashes in `contract-provenance.json`. Full
statements, editorials and upstream solution implementations are not redistributed.
The implementations are original; no dependency, policy, admission, publication
or qualification changes are included. Component intent and boundaries are preserved.
