# Paired readable solution candidates

Owner: [Algorithm Solver charter](../../CATSCAN.md).

Fifteen permitted development-fit problems have standalone Python and JavaScript
candidates: 34, 35, 62, 64, 71, 84, 85, 91, 104, 111, 347, 560, 567, 704 and 733. The IDs are checked
against the already-public pinned development partition, not a new population.

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
- Frequency, prefix-sum and fixed-alphabet window loops use explicit count state.
  Reuse actual invariants, not a generic abstraction that hides different rules.
- JavaScript numeric assumptions are declared. No bitwise midpoint truncation or
  silent assumption that arbitrary Python integers behave like JS Number.
- Effects matter: flood fill preserves and returns the input image; other inputs
  remain unmodified. Tree shape, image row identity and accepted string alphabet
  are explicit in each sidecar.
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
