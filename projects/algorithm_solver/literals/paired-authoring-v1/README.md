# Paired readable solution candidates

Owner: [Algorithm Solver charter](../../CATSCAN.md).

281 permitted development-fit problems have standalone Python and JavaScript
candidates: 6, 10, 11, 15, 18, 21, 22, 23, 24, 25, 28, 29, 34, 35, 40, 42, 51,
52, 54, 55, 58, 59, 61, 62, 64, 66, 67, 69, 71, 78, 79, 82, 84, 85, 86, 89, 90,
91, 93, 96, 103, 104, 106, 107, 111, 112, 115, 122, 123, 124, 127, 128, 148,
153, 252, 253, 347, 526, 532, 541, 546, 548, 551, 553, 554, 560, 564, 566, 567,
575, 576, 581, 582, 594, 599, 605, 611, 633, 643, 645, 647, 658, 665, 670, 674,
678, 686, 696, 704, 728, 733, 734, 738, 740, 744, 747, 762, 763, 771, 786, 806,
821, 824, 830, 832, 833, 837, 844, 845, 846, 849, 858, 859, 867, 868, 874, 893,
896, 897, 910, 914, 916, 917, 918, 922, 925, 929, 937, 941, 942, 945, 948, 949,
951, 955, 957, 966, 967, 971, 976, 977, 986, 991, 992, 1001, 1005, 1006, 1007,
1009, 1010, 1014, 1015, 1016, 1017, 1018, 1020, 1021, 1023, 1024, 1027, 1031,
1034, 1035, 1042, 1047, 1048, 1051, 1053, 1061, 1071, 1072, 1074, 1079, 1080,
1091, 1092, 1094, 1101, 1103, 1105, 1106, 1108, 1109, 1122, 1129, 1130, 1131,
1139, 1140, 1143, 1144, 1145, 1150, 1151, 1154, 1155, 1156, 1160, 1162, 1163,
1165, 1170, 1171, 1175, 1187, 1314, 1325, 1328, 1346, 1375, 1419, 1464, 1514,
1534, 1545, 1546, 1574, 1636, 1685, 1686, 1690, 1696, 1710, 1717, 1723, 1725,
1732, 1748, 1752, 1754, 1785, 1791, 1823, 1846, 1848, 1942, 1961, 1967, 1979,
2027, 2037, 2054, 2086, 2192, 2200, 2282, 2287, 2295, 2338, 2341, 2357, 2364,
2367, 2379, 2395, 2400, 2430, 2468, 2491, 2563, 2670, 2740, 2785, 2808, 2810,
2836, 2873, 2902, 2913, 2942, 3100, 3105, 3147, 3192, 3210, 3233, plus 1063, 1100, 1119, 1176 and 1180. The IDs are checked
against the already-public pinned development partition, not a new population.

The historical 500-problem JavaScript admission record is separate (see
[Milestones](../MILESTONES.md)). This inventory counts new paired alternatives,
not newly admitted problems or a fraction of M1/M2 completion.

These are newly authored, readable candidates. They do not replace the frozen
`style150-v1` one-line `solve` representation, its sources, or its qualification
receipts. They also do not publish the separately gated 80-rewrite set.

## Shared style and composition

- Python uses four-space indentation; JavaScript uses two spaces and explicit
  braces. Use descriptive role names and preserve the same algorithmic structure
  across languages rather than forcing identical syntax. Increment/decrement
  counters explicitly with += 1 / -= 1 in both languages.
- Each program is a complete `Solution` class plus any helpers it needs. Standard
  method names form the declared candidate interface. There is no top-level call,
  hidden helper import, generated implementation, or outside source expansion.
- Search candidates reuse the same fully included lower-bound helper, over
  half-open intervals. Range search uses an upper bound without target arithmetic.
- Tree traversals share iterative level queues and a head cursor. Retained queue
  entries count toward O(n) space; do not claim O(width) space or use quadratic
  front removal.
- Histogram problems reuse the same fully included monotonic-stack helper;
  equal heights coalesce and a virtual zero flush avoids mutating input arrays.
- Rolling DP states preserve dependency order and bound all intermediate integer
  counts, including decoding prefixes rather than just the final answer.
- Linked-list operations share a fully charged sentinel helper and preserve input
  node identity while explicitly relinking next edges. Shared merge tails are
  outside their declared disjoint-input domain.
- Backtracking uses choose/recurse/undo with fresh output copies and bounded
  recursion. Output costs remain explicit, not hidden as constant extra space.
- Sum searches share copied sorting and deduplicated k-sum with a two-pointer
  base case; meetings share sorted endpoints and half-open interval semantics.
- Graph traversals share fully charged cardinal-neighbor helpers, while union-find
  owns its parent/size invariants. Tree equivalence uses canonical structural IDs,
  not ambiguous serialized values or assumptions of unique node values.
- Frequency, prefix-sum and fixed-alphabet window loops use explicit count state.
  Reuse actual invariants, not a generic abstraction that hides different rules.
- JavaScript numeric assumptions are declared. No bitwise midpoint truncation or
  silent assumption that arbitrary Python integers behave like JS Number.
- Effects are part of each candidate's contract. Sidecars state which caller-owned
  arrays, grid cells, list links or tree edges may change, which identities survive,
  and whether returned containers are fresh or intentionally alias an input.
  There is no blanket nonmutation guarantee. Tree shape, list ownership, row
  identity and accepted alphabets remain explicit rather than inferred.
- Count every helper, class wrapper and eventual adapter in comparisons. Consistent
  source is a candidate mechanism, not evidence of reduced composition cost.

## Status and next gate

All sources are **unqualified candidates**. Static review, Python AST parsing,
JavaScript syntax checks and metadata checks do not establish runtime correctness,
predecessor equivalence, admission or an M1 result. No candidate was imported or
executed during authoring. The exact permitted private development package has now been transferred and
verified on dot; its mandatory isolated judge is still unavailable. The five new
pairs use those frozen interfaces as static development context, not execution
evidence. Earlier sidecars retain their historical authoring-time availability
statements; those statements are not current environment status.

Each `.semantics.json` states the intended interface, input/return domains,
mutation/aliasing, numeric assumptions, complexity and full source accounting.
These are author declarations, not independent qualification receipts. The
`manifest.json` binds the final candidate and sidecar bytes and records syntax-only
evidence. It is not automatically consumed by the approved corpus or serving lane.

Before promotion, bind each candidate to the frozen problem contract and actual
judge interface; charge any wrapper required to adapt the method entrypoint.
Execute independent cases in the existing isolated judge, checking return values,
types, mutation/aliasing, numerical boundaries and complexity obligations. Retain
failures. Only then compare source/dictionary arms under the unchanged M1 gates.
The final held-out 100 and protected 66 remain closed.

[Coverage and qualification gaps](GAPS.md) records unwritten definitions,
authored provenance questions, required inputs, execution and publication limits.
