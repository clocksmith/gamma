# Request 252: batch 4

17 original JavaScript/Python candidate pairs, authored against source base
`bc252ef318b165396288cd3f3d0ecbd4b84c03da`. All IDs passed the unchanged,
hash-pinned statement-access boundary before acquisition. Definitions, constraints,
and examples were read from the exact official LeetCode pages recorded in
`manifest.json`. No editorial implementations or private/protected cases were used.

These are **locally tested candidates, not catalogue-qualified solutions**.
Nothing here changes admission, source access, serving, or historical research gates.

## Interfaces and evidence

Every source exports/defines positional `solve`. Problem 3242 additionally exports
its native `NeighborSum` class. Its tape adapter receives `operations, arguments`
and returns one result per operation, including null for construction. Construction
snapshots the grid; operations do not mutate caller-owned inputs. Other source
contracts, argument order, complexity, correctness rationale, numeric limits,
mutation policy, provenance, source hashes, and public examples are in the manifest.

Run with Python 3 and Node.js, without network or package installation:

```sh
python3 projects/algorithm_solver/catalogue/authored/request-252-v1/batch4/test_batch4.py
```

The deterministic seed-25204 driver checks both languages against independently
constructed expected results, not merely against each other. It includes exhaustive
short vowel games and binary substrings; explicit graph BFS; all small investment
subsets, subsequences, spanning trees, and upgrade subsets; direct subtree XOR sets;
Miller-Rabin prime checks independent of candidate trial division; and selected
large closed-form shapes. It checks absence of input mutation and source syntax.
Expected values are not passed to the JavaScript subprocess.

`test-receipt.json` records 2,562 cases per language / 5,124 combined executions,
34 syntax checks, runtime versions, and exact source/test hashes. A tape counts as
one case even when it contains many native operations. Structured large cases include
40,000 binary characters, 100,000-node shortest-hop queries, a 50,000-node subtree
chain, and wide-integer products/path costs. These are bounded development checks,
not an exhaustive maximum-constraint qualification or performance claim.

## Important semantic details

- 3513 assumes its specified permutation of `1..n`, not an arbitrary integer array.
- 3534 sorts a copy of node identities; input values need not be sorted.
- 3562 uses only initial budget, never reinvested future profit, and a skipped parent
  does not transmit a discount from a grandparent.
- 3577 counts root-first orders, matching the official examples. JavaScript modular
  multiplication remains below `2^53` under the 100,000-element bound.
- 3590 supports parents whose numeric labels exceed their children, duplicate XORs,
  and long chains without recursion. XORs include the root's value.
- 3600 rejects mandatory cycles; mandatory edges cannot be upgraded.
- 3620 computes a real topological order, not numeric node order; zero-cost edges
  and valid paths scoring zero remain distinct from the no-path result `-1`.

Inputs outside the documented problem domain are not a qualified API surface.
Finite cases do not establish universal correctness or official judge acceptance.
