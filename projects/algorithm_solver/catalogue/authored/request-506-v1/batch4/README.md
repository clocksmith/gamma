# Request 506 — batch 4 candidates

61 problem IDs, each with an original JavaScript and Python implementation (122 source files). These are **authored, locally tested candidates**, not admitted/qualified solutions or official judge acceptances.

Base: `62f8d1e2b375ab1c576a412be06adeddb5bcbffe`.

## Run the bounded local tests

```sh
python projects/algorithm_solver/catalogue/authored/request-506-v1/batch4/test_batch4.py
```

The deterministic suite uses seed 50604 and covers all 61 IDs with public examples and independent small-input oracle checks. It runs both languages, writes `test-receipt.json`, and requires Python 3 and Node.js (modern BigInt/Array.at support). It does not access the network or any protected corpus. The manifest records exact source hashes, positional parameters, complexity, adapters, definition sources, and per-ID test counts. Generated local cases are not private/hidden judge material.

The tests intentionally use alternative formulations: exhaustive subsets/permutations, shortest paths over tiny operation states, independent matching by exhaustive vertex covers, simple state machines, direct game minimax, and Bellman–Ford/reference reachability. A finite pass is not a soundness proof. No algorithm is represented as having completed a Gamma milestone.

## Contracts and provenance

All sources expose positional `solve(...)`; JavaScript exports it through `module.exports`. Linked lists are values in next-pointer order; trees use queue-based level-order arrays with null child markers. Design exercises accept `operations, arguments` and return a result per operation, including null for constructors/void operations. Problem 2782 accepts the original equality oracle object, with a documented category-label array adapter for JSON tests only. Native platform integration is not qualified.

Problem 2408 follows the **current public SQL class API** (`ins`, `rmv`, `sel`, `exp`), not SQL query text or the older `insertRow` API. Problem 2900 follows the current `words, groups` signature.

Only permitted metadata-gated identities were opened. `boundary-revalidation.json` is a final metadata-only recheck of both languages, not a new authorization, admission, publication receipt, or case-access grant. The boundary gate's current policy pins are preserved.

Where the official premium page did not expose a definition, the identity-bound public doocs/leetcode documentation supplied only the problem statement/constraints/examples; the manifest identifies those URLs, snapshot hashes and CC-BY-SA-4.0 documentation provenance. No editorial implementation was consulted or copied, and raw third-party definitions are not bundled. Implementations and oracle code were authored for this patch.

## Limitations

- No hidden judge, model calls, protected examples, benchmark campaign, admission or frozen confirmation.
- Numbers are used only within each problem's stated integer bounds; problem 2912 uses BigInt for JavaScript modular products, and 3181 uses a BigInt bitset. These return JSON-compatible numeric results.
- The O(n log n) follow-up for 2263 is not claimed: this candidate uses the stated bounded value domain.
- High-risk JavaScript sources (1977, 2107, 2123, 2184, 2378, 2408, 2819, 2912, 3112, 3212) were manually expanded and commented, then retested. No formatter download or ad-hoc automated transformation was used.
