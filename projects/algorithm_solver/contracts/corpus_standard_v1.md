# Corpus normalization standard v1

Machine authority: `corpus_standard_v1.json`. This first enforceable version is
qualified only for the six-problem pilot: 148, 153, 242, 300, 347 and 387. It is a
corpus preparation contract, not a new composer or mandatory shared runtime.
Do not bulk rename sources. Preserve every delivered/reference source and hash;
put formatting variants and algorithm successors in separate immutable attempts.

## External adapters and internal signatures

Keep the pinned `Solution` class, method name and positional argument order in
both languages. The external method is one return statement forwarding the same
arguments, in order, to a registered canonical internal function. Public short
names such as `nums`, `s`, `t` and `k` are explicit interface exceptions. They must
not leak into internal names merely for textual similarity.

The old JavaScript return harness explicitly resolves a free function; Python's
functional harness resolves a `Solution` method. W002 assignments specified
`Solution` in both languages. The pilot harness therefore takes an explicit
`free-function` or `solution-class` setting, with no fallback. Original JS is
measured through its original free-function interface; normalized JS uses the
class interface. Passing the former does not satisfy the latter. No historical
harness or receipt is rewritten.

| Role or helper | JavaScript | Python |
|---|---|---|
| sequence | `values` | `values` |
| lower included index | `leftIndex` | `left_index` |
| upper excluded index | `rightIndex` | `right_index` |
| probe index | `middleIndex` | `middle_index` |
| desired count | `resultCount` | `result_count` |
| lowercase frequencies | `countsByLetter` | `counts_by_letter` |
| first position >= target | `lowerBound(values, targetValue)` | `lower_bound(values, target_value)` |
| count lowercase text | `countLowercase(text)` | `count_lowercase(text)` |
| dense integer counts | `countBoundedValues(values, minimumValue, maximumValue)` | `count_bounded_values(values, minimum_value, maximum_value)` |
| sever bounded list run | `splitRun(startNode, runLength)` | `split_run(start_node, run_length)` |
| stable merge | `mergeRuns(leftHead, rightHead)` | `merge_runs(left_head, right_head)` |

The JSON contains the complete pilot role dictionary and helper contracts.
Helpers are self-contained source definitions; identical helper semantics and
argument order do not require importing a common library. Heap conventions are
specified as a future extension, not represented as already tested helper code.

Use half-open search intervals `[leftIndex, rightIndex)` / `[left_index,
right_index)`. The interval invariant, comparison and update rules still need
review: naming an interval does not prove it shrinks. In particular, the rotated
minimum search uses the lower midpoint of the *inclusive last candidate*,
`left + floor((right - left - 1) / 2)`, while lower_bound uses
`left + floor((right - left) / 2)`.

## Deterministic enforcement

JavaScript uses installed Babel parse, scope and generation tools. Python uses
`ast` plus explicit lexical binding resolution. No source code executes during
lint. Every internal binding has a source-hash-bound reviewed role mapping.
The checker validates the declared role's canonical spelling, helper definition
parameter order, positional call arity, external signature/adapter, and complete
mapping coverage. It rejects ancestor binding shadowing and stale/unknown maps.
Property names and string keys are not variable bindings. Closure references
resolve to their lexical binding; they are not renamed by spelling.

This version performs **no automatic variable renaming**. A reviewer must decide
which binding means which role, then author the normalized candidate. The checker
cannot infer a variable's meaning. Ambiguous mappings are unresolved work, not an
opportunity for blind text replacement. Exceptions require an explicit reviewed
policy extension; there is no unrestricted ignore switch.

Formatting is deterministic: Babel's noncompact output with two-space JS blocks,
and Python `ast.unparse` with four-space blocks. Reformatting must be idempotent.
Python comments require separate preservation review before its AST formatter;
do not silently strip reference commentary. JS comments are retained. Formatter
versions/tool hashes are part of the run seal. Static checks cover a bounded
syntax subset; unsupported scope features require extension before use.

Each candidate declares domain, integer/float semantics, string unit and
normalization, output ordering, mutation, aliasing, algorithm, complexity and
review rationale. The checker enforces declaration presence; their truth requires
semantic tests and review. Types must be annotated in Python; runtime types and
return values are checked by the judge, not inferred from an annotation.

## Semantic and complexity authority

Do not force identical algorithms. An algorithm replacement is an explicit
successor, not a style-only transformation. Freeze original and successor hashes,
run the same permitted public/independent cases, and observe mutation/aliasing
separately. Keep expected values outside the execution sandbox. Preserve failures,
out-of-domain cases, old comparisons and infrastructure failures.

The pilot declares lowercase ASCII for #242/#387 and bounded integers for #347
from their pinned statements. The #242 Unicode follow-up is not claimed. #347
allows any order, so its explicit unordered-distinct comparison is a separate
receipt from historical strict-order scoring. No test input or expectation is
edited. Cases outside the declared domain remain visible in the full results;
they prevent an unconditional all-existing-tests claim.

Complexity is reviewed from the implementation and problem requirement. Tests,
timing, lint and canonical names cannot prove asymptotic bounds. #347 uses direct
counts and frequency buckets, O(n + U) worst-case with U=20001 from its declared
value range; there is no comparison sort, hash-table worst-case assumption or
randomized quickselect. #300 uses O(n log n) tails; #148 uses stable bottom-up
merging with O(1) live auxiliary algorithmic state. Original algorithms remain.

Automatic indentation and whitespace rendering consume zero composition macro
slots. Whole-solution macros remain allowed within the 256-entry budget. Source
normalization, semantic coverage, autonomous solving and human effort are separate
measurements; this pilot establishes no new autonomous solve.

## Check a candidate

```sh
PYTHONPATH=projects/algorithm_solver python3 -m algsolve.corpus_standard \
  --source candidate.js --language javascript \
  --policy projects/algorithm_solver/contracts/corpus_standard_v1.json \
  --contract candidate-contract.json --mapping candidate.js.bindings.json \
  --semantics candidate.js.semantics.json
```

The Python command uses `--language python`. Original assignments/reservations
remain frozen. Apply `web_solver_assignment_v2.md` as a versioned supplement, not
an in-place replacement of historical packets.

## Reviewed profile and limits (v1.0.1)

Module bodies contain only unconditional named function declarations and the
single plain `Solution` adapter. Adapter methods must be ordinary instance
methods, not getters/setters. The adapter's internal call resolves to a registered
module function. Callable/class rebinding, adapter references/mutation, helper
property writes and starred/spread helper calls are rejected. Python validates
compilation without executing candidate code. Imports, exception bindings,
pattern matching, comprehensions, dynamic bindings and asynchronous/generator
constructs require a reviewed profile extension. JavaScript rejects function
expressions and object methods; its only arrow callback profile is the zero-arg
`Array.from` callback returning a fresh empty array for frequency buckets.

The pinned toolchain versions are in the JSON policy; source-hash-bound mappings
must be rechecked if a formatter version changes. These checks are a bounded
structural gate, not a security sandbox or general type checker. Role meaning,
helper behavior, numeric/string contracts, complexity and mutation/alias claims
still require review and isolated execution. A campaign ledger can enroll the
full eligible corpus without asserting this initial profile covers every entry.
