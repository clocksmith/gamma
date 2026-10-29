# S official observer profile v2: same checks, lower interpreter cost

This successor to [S observer v1](../continuation-s-observers-20261028-v1/README.md) changes only the JavaScript observer's cost. v1 stays byte-for-byte unchanged. v2's checks, record schema, `native_route` (`official-s-v1`), packet schema, allowlists and host checker are those of v1. `harness.py`, `native_graphs.py`, `host_check.py`, `plan.py`, `prospective-plan.json`, `test_observers.py`, `test_observers.cjs`, `test_integration.py` and `test_planning.py` are byte-identical copies of the v1 files. Only `harness.cjs` and `native_graphs.cjs` differ.

## Why

In lane `continuation-s-qualification-20261028-v2`, JavaScript 222 was SIGKILLed at about 3.02 s on its large-repeat batches for cases 135, 136 and 137: two 50,000-node complete trees per process, under a 3 s CPU cap.

This is the same observer-cost cause as T 234/235/236. On the Linux executor, inside the protocol's own sandbox invocation, a no-op program with v1 is killed on all five synthetic [50k, 50k] batches. A single 50,000-node call costs v1 2.59 s CPU on its own: build 1.77 s, three snapshots 0.72 s, JSON 22 ms (`observer-cost-measurements.json`). The batch needs two such calls.

The mechanism is shared with T: a class guard after every constructor call, a repeated `data()` check of each child in every snapshot, and a discarded duplicate post-call snapshot. S v1 also allocated three flag arrays per node.

## What v2 changes

The change is the same as [T observer v2](../continuation-t-observers-20261028-v2/README.md#what-v2-changes), including the independent-review correction for a Proxy class chain. v2 performs every operation that can reach candidate-controlled objects or code, in v1's order, and removes only repeated pure work. A Proxy, or any failing check, goes to the verbatim v1 code embedded in `native_graphs.cjs`, so the error text and trap order are v1's.

Two S-specific points:

- The per-node flag record keeps v1's `{field:[writable,enumerable,configurable]}` shape, because the verbatim v1 `data()` may read it.
- The post-call snapshot is reused only on the `clone(value)` branch (199, 222) when the result is not an object, function or bigint, or on the `linked(value)` branch (203, 206). In both cases no Proxy may have been reached.

## Equivalence evidence

- `test_equivalence.cjs` is the same file as in T v2, including the class-chain Proxy modes; it selects the S routes 199/203/206/222 from its directory name. It runs 6,003 cases per seed for seeds 20261028 and 7, with 0 mismatches in record or error string and in the ordered Proxy-trap, `toJSON` and constructor event log. This holds on Node v22.20.0 and on the executor's v22.22.1, and a further 2,003 cases per seed pass under `--jitless`.
- `test_stdout_equivalence.cjs` gives byte-identical `main()` stdout on 6 packets. They include a two-call 50,000-node 222 batch, 10,000-node 203, 5,000-node 206, and the review's S222 reproducer, a Proxy `Function.prototype` on `TreeNode` that rejects from the 4th armed guard. The draft observer failed that reproducer and 198 random S cases.
- **Mutation sensitivity:** the same 11 deliberately broken v2 copies listed in [T observer v2](../continuation-t-observers-20261028-v2/README.md#equivalence-evidence) each produced 14–648 mismatches in S.
- v1's 17 synthetic JavaScript tests and the cross-language host integration pass unchanged against v2.
- The equivalence scope is the same as T's: programs that do not replace JavaScript intrinsics that v1 itself uses without guarding them. Tests are finite evidence.

## Cost (Linux executor, protocol sandbox, unchanged limits, no-op synthetic program)

| Batch | v1 | v2 |
|---|---|---|
| 222 complete [50k, 50k] | SIGKILL at 3.02 s ×5 | 1.23 s |
| 222 complete [50k] | 2.59 s | 0.69 s, stdout identical |

The remaining floor is the per-construct guard, as explained in the T v2 README.

## Not changed or granted

No cap changes. The S source review and the separate observer review bind v1 observer hashes, so new independent reviews are required before any controller can dispatch with v2. The profile grants no review, qualification, catalogue change or publication. No numbered candidate source was read or executed.
