# Eight paired LeetCode solutions

Component: Algorithm Solver / dual-language catalogue authoring.
Intent: preserved. Original Python and JavaScript implementations use the same
ordered-positional `solve(...)` interface, plus `Solution` forwarding methods.
JavaScript also exports the corresponding LeetCode function name. No model,
network, external dependency, or shared mutable state is required by a solution.

| ID | Difficulty | Problem | Algorithm | Time | Auxiliary space |
| --- | --- | --- | --- | --- | --- |
| 802 | Medium | Find Eventual Safe States | Reverse topological elimination | O(V + E) | O(V + E) |
| 875 | Medium | Koko Eating Bananas | Binary search on speed | O(n log M) | O(1) |
| 1438 | Medium | Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit | Two monotonic queues | O(n) | O(n) |
| 2406 | Medium | Divide Intervals Into Minimum Number of Groups | Inclusive endpoint sweep | O(n log n) | O(n) |
| 871 | Hard | Minimum Number of Refueling Stops | Greedy maximum heap | O(n log n) | O(n) |
| 1547 | Hard | Minimum Cost to Cut a Stick | Interval dynamic programming | O(m^3) | O(m^2) |
| 2246 | Hard | Longest Path With Different Adjacent Characters | Iterative tree dynamic programming | O(n) | O(n) |
| 2416 | Hard | Sum of Prefix Scores of Strings | Compact counted trie | O(S) | O(S) |

Here M is the maximum pile, m is the cut count, and S is total string length.
The trie has at most 26 siblings per node; its constant-alphabet linear bound
includes those searches. Both implementations avoid recursion on deep graphs
and trees. Inputs, including nested arrays, are preserved; returned containers
never alias inputs. Integer domains and ASCII-only string requirements are
explicit in `assignment.public-safe.json`, rather than inferred from examples.

## Selection and authority

Base inspected: `7290ac480db36698b4c69e677f4f51172dd738bd`.
The eight are unused Medium/Hard replacement candidates from the committed
`literals/admission500-v1/evidence/gap-selection.json` inventory. That inventory
classified its candidates as pending, unclaimed and outside reserved families.
They are outside the frozen admitted 500 and the known protected66 metadata.
Current unpushed/private work cannot be inspected from this snapshot.
`selection.json` binds the metadata sources and limits of this selection.

The user explicitly requested eight unfinished problems, both language
implementations, tests consistent with Gamma, and one commit to main. Only public
problem descriptions were consulted. `assignment.public-safe.json` retains
canonical titles, official URLs, domain snapshots and interfaces; the prose,
implementations and small-input oracles in this batch are original. No upstream
solution or protected/private case payload is copied. The repository MIT license
applies to the original contribution; linked problem descriptions remain their
publishers' material.

## Run the focused checks

From the repository root, with Python 3.10+ and Node available:

```sh
python3 projects/algorithm_solver/catalogue/authored/leetcode-eight-v1/test_solutions.py
```

Missing Node is an error, not a silent JavaScript skip. Every case is checked
against an independently computed small-input answer or a declared boundary
expectation, in both languages. The runners also check the canonical and
forwarding interfaces, repeated calls, unchanged arguments, safe integer outputs,
and output non-aliasing. Expected answers stay in the parent process. These
processes are developer test runners, not security sandboxes or the canonical
Gamma judge.

Coverage includes exhaustive tiny directed graphs and windows, independent cut
orders and refueling subsets, relabeled trees, duplicate prefixes and inclusive
interval endpoints. Boundary cases include depth-100000 trees, length-100000
windows, 100000 intervals, 10000 large piles and one million string characters.
Finite checks do not prove all cases or complexity, and no LeetCode submission
or protected-population evaluation was performed.

The manifest follows the existing authoring-artifact interface. Inspect it with
Gamma's existing read-only tool, from `projects/algorithm_solver`:

```sh
python3 -m algsolve.authoring_variants \
  catalogue/authored/leetcode-eight-v1/manifest.json \
  --output /tmp/gamma-eight-authoring-variants.json
```

That tool must return eight problems and sixteen variants with unknown
qualification. It must not automatically promote these developer-tested sources
into the qualified serving catalogue. Independent judge/review and external
receipt bindings remain with the existing owners.

## Boundaries

No frozen population, oracle, historical failure, qualification threshold,
trained model, lookup admission, or qualification-count report is modified.
This batch adds source coverage and reproducible developer checks, not a new
catalogue authority, recognition result, or autonomous-solving claim. An
independent owner can later admit these exact source hashes through the normal
catalogue contracts. `verification.json` records only checks actually run.
