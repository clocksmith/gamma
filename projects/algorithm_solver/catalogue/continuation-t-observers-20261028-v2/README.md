# T official observer profile v2: same checks, lower interpreter cost

This successor to [T observer v1](../continuation-t-observers-20261028-v1/README.md) changes only the JavaScript observer's cost. v1 stays byte-for-byte unchanged. v2's checks, record schema, `native_route` (`official-t-v1`), packet schema, allowlists and host checker are those of v1. `harness.py`, `native_graphs.py`, `host_check.py`, `plan.py`, `prospective-plan.json`, `test_observers.py`, `test_observers.cjs`, `test_integration.py` and `test_planning.py` are byte-identical copies of the v1 files. Only `harness.cjs` and `native_graphs.cjs` differ.

## Why

In lane `continuation-t-qualification-20261028-v2`, JavaScript 234, 235 and 236 were SIGKILLed at about 3.01 s on their 100,000-node batches. The sandbox CPU cap is 3 s, and the Python versions passed. v1's own `local-helper-stress.json` already recorded about 3.07 s for the observer alone on a Mac. On the Linux executor, inside the protocol's own sandbox invocation, v1 is killed on every one of those batch shapes with a no-op program (`observer-cost-measurements.json`). The candidate never got the budget.

Phase attribution at 50,000 nodes (v1 survives there): build is 1.70 s of 2.37 s (235) and 1.64 s of 2.23 s (234); snapshots take 0.52–0.57 s; JSON parse and serialize take under 30 ms. A local profile at 100,000 nodes puts 1.76 s of 3.07 s in the class-guard closure alone. Three causes:

1. `Graph.construct` reruns the class/prototype guard after every constructor call. That is 100,000 guard calls, each reading all descriptors of the class, `Function.prototype`, `Object.prototype` and the class prototype (about 26 properties). The comparison allocated three `Reflect.ownKeys` arrays and a closure per property in the jitless interpreter: about 26 µs per call against about 2 µs for the native reads themselves.
2. Each snapshot called `data()` once per node and again for each child through `identify(child)`, so pool nodes were checked about 3 times per snapshot.
3. After the official call the harness took a full snapshot, then discarded it and took the same snapshot again.

## What v2 changes

The rule: v2 performs every operation that can reach candidate-controlled objects or code, in v1's order. It removes only repeated pure work, and v1's verbatim code still decides every failure.

- **Guard:** same objects and the same predicate. Descriptors are flattened once and compared with indexed loops; reads go through `Reflect.ownKeys` plus per-key `Object.getOwnPropertyDescriptor`. A guard still runs after every constructor call. If the fast check fails, the verbatim v1 guard runs and throws v1's error. If any object on the class chain is a Proxy, every guard call can run candidate code. The verbatim v1 guard is then used, and the Graph is marked non-plain, so snapshots take v1's path, each guard call counts as candidate-reachable work, and the harness runs v1's second guard and snapshot.
- **`data()`:** same checks, without per-call closures or descriptor-map allocation. A Proxy node, or any failing check, goes to the verbatim v1 `data()`.
- **Snapshot:** on a plain graph, the snapshot's guard runs once, outside any fallback, so its errors propagate exactly as in v1. Pool children are then identified by the identity table without repeating their own row's check in the same pure pass. A Proxy child, a Proxy pool node, a Proxy class chain, or any node-pass error uses the verbatim v1 snapshot, so the thrown error and trap order are v1's.
- **Harness:** the post-call snapshot is reused as the final `after` only on a plain graph (no Proxy node or class chain) when nothing that could run candidate code happened since it began: no Proxy reached, and on the `clone(value)` branch no object, function or bigint result. Otherwise the second guard and snapshot run as in v1.
- `build`, `object`, `linked`, export guards, MyQueue traces and scalar routes keep v1's logic.

## Independent review correction

An independent review found that the first v2 draft diverged from v1 when the exported node constructor, or any object on its prototype chain, was a Proxy. The draft used v1's guard there but left the Graph marked plain. It therefore swallowed a throwing guard trap inside the fast snapshot (v1 errors) and skipped v1's second guard and snapshot after candidate code had run in a trap (v1 rejects, or records a mutated value). This version marks such graphs non-plain, routes them through v1's code, and never swallows guard errors. The review's reproducers are now fixed tests; against the draft bytes they fail, along with 296 random T cases.

## Equivalence evidence

- `test_equivalence.cjs` runs v1 and v2 side by side on seeded synthetic inputs. It requires equal record JSON or error string, and an equal ordered log of candidate-observable events (Proxy traps, `toJSON` calls, constructor calls). The inputs cover valid and corrupted wires and the adversarial programs listed below.
  - Results: 9,002 cases per seed for seeds 20261028 and 7, 0 mismatches, on Node v22.20.0 locally and on the executor's `/usr/bin/node` v22.22.1. A further 3,002 cases per seed pass under `--jitless` on both.
  - Adversarial programs: Proxy nodes, Proxy children and results; transient and persistent prototype edits; edits to `Object.prototype` and `Function.prototype` values, attributes and writability between constructor calls; cycles and aliases; external nodes; descriptor, accessor and prototype mutations; frozen nodes; export replacement; `toJSON` side effects; bigint and symbol results. Also a Proxy on the constructor's chain or on its prototype's chain, with every chain trap logged; armed by the official call, the trap throws once, keeps throwing, or mutates a node. Plus off-chain Proxy children with list or primitive results.
- `test_stdout_equivalence.cjs` runs both observers through `main()` with the protocol's JavaScript flags on 10 packets, including 100,000-node 235/236 trees, a two-call 100,000-node 234 batch and the independent review's three reproducers. In those reproducers, a Proxy `Function.prototype` on `ListNode` is armed by `isPalindrome`; it (A) rejects from the 4th armed guard, (B) throws only at the 3rd, or (C) sets `head.val=9` at the 4th. stdout is byte-identical on Node v22.20.0 and v22.22.1. The executor's v2 stdout hashes at 50,000 nodes equal v1's.
- **Mutation sensitivity:** these 11 deliberately broken v2 copies each produced 50–952 mismatches at 600 cases per route:
  - guard dropped after construct
  - snapshot always reused
  - mark taken after the first snapshot (a real bug found and fixed during development)
  - no v1 rerun on a fast snapshot-row failure
  - no v1 rerun on a fast `data()` failure
  - guard ignores enumerable, writable or value
  - no Proxy fallback in `data()`
  - Proxy child not aborted
  - Proxy class chain not marked on the Graph
- v1's 18 synthetic JavaScript tests and the cross-language host integration (`test_integration.py`) pass unchanged against v2.

**Scope of the equivalence claim:** it holds for programs that do not replace JavaScript intrinsics that v1 itself uses without guarding them, such as `Map.prototype.get`, `Array.prototype.map` or `Object.getOwnPropertyDescriptor`. v1 and v2 call those intrinsics different numbers of times, so a program that replaced them could tell the two apart. This is the same reviewed-source, not hostile-source tamper-resistance, scope that v1 declares. Within it, the claim rests on the argument above plus finite tests; the tests are not a proof.

## Cost (Linux executor, protocol sandbox, unchanged limits, no-op synthetic program)

From `observer-cost-measurements.json` (5 repetitions, median process CPU):

| Batch | v1 | v2 |
|---|---|---|
| 235 chain [3, 100k, 3] | SIGKILL at 3.01 s ×5 | 1.22 s |
| 235 balanced [3, 100k, 3] | SIGKILL ×5 | 1.19 s |
| 236 complete [3, 100k, 3] | SIGKILL ×5 | 1.18 s |
| 234 list [100k, 100k] | SIGKILL ×5 | 2.11 s |
| 235 chain [100k] | SIGKILL ×5 | 1.19 s |
| 234 list [100k] | SIGKILL ×5 | 1.06 s |
| 235 chain [50k] | 2.35 s | 0.61 s, stdout identical |
| 234 list [50k] | 2.28 s | 0.59 s, stdout identical |

These figures include node startup (about 60 ms). The 234 large-repeat batch observes two 100,000-node lists in one process, so about 0.9 s of the 3 s remains for two candidate calls. Single-large batches leave about 1.8 s.

The floor that remains is the per-construct guard. v1 detects a class or prototype change made by any one of the constructor calls, even if a later call restores it, and keeping that guarantee means reading about 26 descriptors after every construction. Removing that floor would need a different guard guarantee or a different batch plan for 234. Either is an owner decision and not part of this profile.

## Not changed or granted

No CPU, wall, memory, output, process or file cap changes. The source review receipts bind v1 observer hashes, so a new independent observer review is required before any controller can dispatch with v2. This profile grants no review, admission, qualification, catalogue change or publication. `measure_observer_cost.py` and `phase_probe.cjs` are measurement tools, not execution helpers. No numbered candidate source was read or executed.
