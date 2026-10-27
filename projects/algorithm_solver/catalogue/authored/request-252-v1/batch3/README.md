# Batch 3: 17 original JavaScript/Python candidate pairs

Base: `bc252ef318b165396288cd3f3d0ecbd4b84c03da`.
All assigned IDs have one original implementation in each language. These are
**development-tested candidates, not catalogue-qualified or admitted sources**.
Source-acquisition eligibility does not confer qualification or serving rights.

Run from this directory with Python 3.11+ and Node 18+:

```
PYTHONDONTWRITEBYTECODE=1 python3 test_candidates.py
```

Observed: **1,760 cases per language, 3,520 functional assertions, 34 syntax
checks**, and 3,520 input-immutability checks. Each ID has official public examples
and 100 independently generated bounded-oracle cases (seed 25203). Selected
structured cases exercise deep trees, large exact counts, maximum-length strings,
noninvertible product residues, recharge-on-last-energy behavior, empty outputs,
and overflow-sensitive area/component sums. The script records hashes and counts
in `test-results.json`; expected outputs are not sent to the Node candidate process.
This is a local development harness, not an approved sandbox judge receipt.

`manifest.json` supplies exact ordered arguments, domains/results, algorithms,
complexity, effects, primary-definition URLs, private acquisition-response hashes,
independent-oracle descriptions, and implementation hashes. Full statement text
and external implementation code are not included. Official definitions supplied
all 17 contracts; no fallback definition provider was required.

## Interfaces and resource limits

- All JavaScript modules export `solve`; all Python files define `solve`.
- 3508 also exports the native online `Router` class. Its uniform interface is a
  constructor-first operation tape with public method names and null/None for the
  constructor. Duplicate additions are rejected before eviction. Auxiliary FIFO
  and per-destination timestamp storage compact as packets leave.
- All candidates preserve caller arrays/strings. 3525 updates persist inside one
  invocation, without changing caller `nums` or `queries`.
- 3518 uses rank-capped multinomial arithmetic, not unsafe full factorials. All
  JavaScript integer arithmetic stays exact under the official input bounds;
  3583 reduces after each center contribution. Full numeric limits are explicit
  in each manifest contract.
- 3552 has a growable typed circular deque in JavaScript; 3568 uses BFS levels and
  a packed energy-dominance table. Neither relies on recursive graph traversal.
- The test script has a 90-second Node process timeout and a 384 MiB Node old-space
  cap. Large tests are selected shapes, not a comprehensive performance campaign.

## Boundaries

`pre-open-authorizations.json` records 34 successful statement-access gate receipts
before the first definition acquisition. The reviewed existing policy remains
unchanged. No reserved/exterior identity was read, activated or implemented by this
batch. Catalogue and serving registries, qualification gates, source-access policy,
original sources, and the repository component intent are preserved.
