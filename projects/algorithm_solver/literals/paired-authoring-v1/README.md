# Paired readable solution candidates

Owner: [Algorithm Solver charter](../../CATSCAN.md).

119 permitted development-fit problems have standalone Python and JavaScript
candidates: 6, 11, 15, 18, 21, 22, 24, 25, 28, 34, 35, 40, 42, 51, 52, 54, 55,
58, 59, 61, 62, 64, 66, 67, 69, 71, 78, 79, 82, 84, 85, 86, 89, 90, 91, 93, 96,
103, 104, 106, 107, 111, 112, 115, 122, 123, 124, 127, 128, 148, 153, 252, 253,
347, 526, 532, 541, 551, 553, 554, 560, 566, 567, 575, 576, 581, 582, 594, 599,
611, 633, 643, 645, 647, 658, 670, 674, 678, 696, 704, 728, 733, 738, 740, 744,
747, 832, 844, 867, 874, 897, 951, 977, 986, 1001, 1020, 1021, 1024, 1034, 1042,
1047, 1061, 1074, 1080, 1091, 1094, 1101, 1109, 1129, 1130, 1139, 1145, 1162,
1314, 1325, 1514, 1791, 2192, 2282. The IDs are checked
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
- Effects matter: flood fill preserves and returns the modified input image;
  linked-list candidates relink original nodes. Tree pruning/relinking candidates
  change declared original edges, border coloring updates declared cells, and
  shortest-path discovery preserves the public predecessor's input markings.
  Other candidates leave inputs unchanged. Tree shape, list ownership, row identity and accepted alphabets are
  explicit in each sidecar.
- Count every helper, class wrapper and eventual adapter in comparisons. Consistent
  source is a candidate mechanism, not evidence of reduced composition cost.

## Status and next gate

All sources are **unqualified candidates**. Static review, Python AST parsing,
JavaScript syntax checks and metadata checks do not establish runtime correctness,
predecessor equivalence, admission or an M1 result. No candidate was imported or
executed during authoring. The original private source/case/receipt package is
absent on dot and its mandatory isolated judge is currently unavailable.

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
