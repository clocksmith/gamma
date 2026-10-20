# Web-solver assignment supplement v2: consistent composition sources

Append this supplement to the existing problem packet. Keep its batch identity,
IDs, exact external method signatures, statements and reservations. Do not work
on another owner's outstanding batch. Existing submissions remain immutable;
return a separately named normalization attempt linked to the original hash.

For each assigned problem return self-contained JavaScript and Python candidates
when both languages are requested, plus a semantic declaration and binding-role
review. Preserve the external `Solution` class, exact method and argument order.
Use a thin external adapter that forwards once to a canonical internal function.
Internal JS uses descriptive camelCase; Python uses matching descriptive
snake_case. Use multiline two-space JS and four-space Python. Do not compress
several control statements onto one line or rename identifiers by text replacement.

Use these shared concepts consistently: `values`; `leftIndex`/`left_index`;
`rightIndex`/`right_index` (excluded upper bound); `middleIndex`/`middle_index`;
`targetValue`/`target_value`; `resultCount`/`result_count`;
`countsByLetter`/`counts_by_letter`; `frequencyCount`/`frequency_count`;
`headNode`/`head_node`, `tailNode`/`tail_node`, `currentNode`/`current_node`.
Exact external short names (`nums`, `s`, `t`, `k`) remain only in the adapter.

Existing helper contracts:

- `lowerBound(values, targetValue)` / `lower_bound(values, target_value)`:
  first index with value >= target, or length; sorted nondecreasing input;
  half-open bounds; no mutation.
- `countLowercase(text)` / `count_lowercase(text)`: fresh26-entry frequency
  array for declared lowercase a..z inputs only.
- `countBoundedValues(values, minimumValue, maximumValue)` /
  `count_bounded_values(values, minimum_value, maximum_value)`: fresh dense exact
  counts at value-minimum for a declared finite inclusive integer range.
- `splitRun(startNode, runLength)` / `split_run(start_node, run_length)`:
  sever a positive-length list run and return the remainder head.
- `mergeRuns(leftHead, rightHead)` / `merge_runs(left_head, right_head)`:
  stable ascending merge of disjoint sorted runs, reusing input nodes, returning
  head and tail. Do not replace node identity with copied values.

Prefer these helpers only where their contracts fit. For other patterns propose
a named helper, exact ordered arguments, return/mutation/alias contract, and role
mapping for review. Do not invent a near-synonym for an existing semantic role or
force a different algorithm solely to share helper text. No shared runtime
dependency is required. Algorithm successors must be labelled separately from
formatting/renaming changes.

Provide: input domain; exact numeric representation and overflow handling;
string units/normalization; permitted result ordering; mutation; returned/input
aliasing; algorithm; time/space bounds and reasoning; explicit exceptions.
Respect each problem's complexity requirements, including follow-ups when they
are the requested target. Do not substitute randomized expected-time reasoning
for a required worst-case bound. Do not silently narrow the domain or change an
expected output to make a test pass.

List every internal variable/helper binding and its semantic role, identifying
its function/scope, including captured values. The coordinator will bind that
review to source hashes and AST binding IDs. Semantic role inference is a human
review step. Unreviewed/ambiguous bindings remain blocked. Properties, node fields,
string keys and public signatures are not variables to rename.

For example, the required external `findMin(nums)` stays unchanged:

```javascript
class Solution {
  findMin(nums) {
    return findRotatedMinimum(nums);
  }
}
```

```python
class Solution:
    def findMin(self, nums: list[int]) -> int:
        return find_rotated_minimum(nums)
```

Do not claim independent qualification, repository execution or completed corpus
coverage. The coordinator applies deterministic syntax, format/idempotence,
interface, helper and reviewed-role checks, then isolated semantic and mutation
tests against unchanged permitted cases. Lint is not correctness or complexity
proof. Automatic indentation consumes no composition vocabulary slots; whole
solutions may still be macros within the256-entry budget.
