# Bounded macro selection: input-cost decision

**Keep three JavaScript macros and four Python macros from this ranked menu.**
The measured winners save424 bytes (3,392 ideal binary presses) beyond the frozen
two-fragment profiles, or751 bytes beyond lexical shortcuts, across the same94
programs per language. This is a0.715% incremental input reduction. Dictionary
storage grows3,242 bytes relative to the two-fragment profiles; that growth was
reported separately and was not penalized by the selection objective.

No attempt was made to fill16 slots. The existing ranked menu supplies five JS
and four Python candidates. Their effects, fixed globals and operand schemas were
reviewed first; then all32 JS and16 Python subsets were evaluated algorithmically.
This menu is hand-designed; the winning subset and shortest source-aware streams
are selected algorithmically. No model chooses a program from a problem statement.

## Complete input comparison

All input totals include the version/language/profile/codebook-hash frame, binding
count, every identifier byte and length, fragment ID, explicit variant, indentation,
slot references, all lexical/raw fallback and END. Fixed constants and control
operators reside in the separately charged dictionary; there is no free binding,
constant, source-body or signature channel. One byte equals eight error-free binary
presses under this protocol, not a measured human action/time result.

| Language | Profile | Semantic/whole entries | Complete input bytes | Codebook bytes |
|---|---|---:|---:|---:|
| javascript | lexical | 0 | 35,426 | 10,769 |
| javascript | frozen_two_fragment | 2 | 35,292 | 12,220 |
| javascript | whole | 94 | 3,854 | 65,282 |
| javascript | selected | 3 | 35,032 | 13,427 |
| python | lexical | 0 | 24,223 | 10,507 |
| python | frozen_two_fragment | 2 | 24,030 | 11,999 |
| python | whole | 94 | 3,854 | 52,808 |
| python | selected | 4 | 23,866 | 14,034 |

The lexical and whole-solution baselines are the original frozen artifacts. The
new CMA2 profile is separate; CMA1 was not modified. Every selected profile still
fits256 slots:128 ASCII entries, two controls,123 JS or122 Python lexical shortcuts,
and three JS or four Python fragments. Whole-solution entries remain a valid
bounded representation baseline but explicitly store all94 bodies in their book.
No generalization or autonomous-solving result follows from their short inputs.

The [byte audit](byte-accounting.json) reconciles every stream byte. Exact canonical
UTF8 JSON measures codebook storage, including template text, constants and
contracts. The common codec implementation size is recorded separately in
[result.json](result.json). This experiment optimizes compact program input rather
than one-pass storage compression; including book storage makes the winners2,818
bytes larger than the prior two-fragment profiles for a single corpus pass.

## Per-macro decision and reuse

The marginal number removes one selected macro and reoptimizes the remaining
stream/book allocation, or adds one rejected macro and reoptimizes. These values
are conditional and need not add to the total improvement. Small and whole BFS
loops overlap; their nested occurrences cannot both encode the same source bytes.

| Language | Macro | Decision | Calls / distinct problems | Conditional input effect |
|---|---|---|---:|---|
| javascript | bfs_collect_one_level | reject | 0 / 0 | 2 bytes added if included |
| javascript | skip_adjacent_equal_values | keep | 4 / 2 | 16 bytes saved by keeping |
| javascript | whole_breadth_first_level_loop | keep | 2 / 2 | 168 bytes saved by keeping |
| javascript | bounded_integer_list_domain_guard | keep | 2 / 2 | 194 bytes saved by keeping |
| javascript | advance_linked_node_cursor | reject | 0 / 0 | 48 bytes added if included |
| python | bfs_collect_one_level | keep | 1 / 1 | 26 bytes saved by keeping |
| python | skip_adjacent_equal_values | keep | 4 / 2 | 67 bytes saved by keeping |
| python | whole_breadth_first_level_loop | keep | 2 / 2 | 7 bytes saved by keeping |
| python | bounded_integer_list_domain_guard | keep | 2 / 2 | 157 bytes saved by keeping |

The JavaScript small collector would add2 bytes once the larger traversal loop is
present, despite saving bytes on its own. The cursor step would add48 bytes after
identifier-table and sacrificed lexical-slot costs. Frequency alone therefore
does not justify admission. Python retains the small collector for zigzag103 and
the larger loop for ordinary102/bottom-up107. Duplicate skipping remains shared by
15/18, with paid direction variants. The bounded-list guard is reused by1512/1748.
Its351-byte combined marginal benefit is validation boilerplate compression, not
an algorithmic solving improvement.

[Detailed attribution](macro-attribution.json) includes singleton gains, available
versus selected occurrences, actual instruction bytes, covered source bytes and
binding arities. [Binding examples](binding-examples.json) show real retained names,
ordered macro calls and full-program costs. Source code and dictionary bodies stay
private in `runs/corpus-macro-selection-128-v1`.

## Human interpretability, reported separately

- **Duplicate skipping:** one sorted-array operation, three binding operands and
  two direction variants. Requires understanding the post-emission pointer state.
- **Whole BFS traversal loop:** one traversal concept, but seven JS/five Python
  identifier operands and language-specific frontier mutation. It contains the
  smaller collector, so learning both introduces overlapping granularity.
- **Single-level collector:** six JS/four Python operands. Useful independently
  in zigzag traversal, but its JS use does not earn its slot in this chosen menu.
- **Bounded-list guard:** two identifiers and three fixed numeric bounds
  (0,20,000,1,000,000). TypeError/ValueError and integer-versus-boolean semantics
  remain language-specific and fixed; this is not a general validation macro.
- **Cursor step:** easy one-binding concept but input-inefficient here; rejected.

These are inspectable complexity proxies, not measured learnability scores. The
[input/concept frontier](input-complexity-frontier.json) exposes the tradeoff:
Python's best three-macro menu needs23,873 bytes, only7 more than the four-macro
winner, and omits the larger BFS loop. A human-facing pilot may prefer that simpler
menu, but no human preference is asserted or deployment made. The measured
input-optimal decision remains three JS/four Python; stop this candidate set here.

## Selection algorithm and semantic limits

Each global subset sacrifices exactly one lexical slot per semantic entry, using
the same frozen lexical priority. Within each program, exhaustive enumeration of
binding-name unions charges only candidate tables that could be needed. Dynamic
programming then finds the shortest cover by registered fragment occurrences,
lexical entries and explicit raw escapes, with no overlap. The minimum is exact
within this finite registered-occurrence/lexical model; it is not a global optimum
over possible vocabularies, variable renamings, algorithms or source formatting.
The search is bounded to at most12 candidate occurrences per program.

Exception classes and builtins (`TypeError`, `ValueError`, `type`, `all`) were
explicitly fixed in the guard template, not treated as arbitrary binding holes.
The whole BFS loop preserves JS frontier-array identity via splice and Python
deque consumption. The node step rebinds a cursor; it does not relink nodes.
Original algorithms, public interfaces, mutation and alias behavior are retained
through exact byte reconstruction. This does not qualify arbitrary new parameter
bindings: semantic preconditions and fresh-name requirements still come from the
reviewed source contexts, not a newly invented general type/scope framework.

## Verification and remaining fallback

All4,512 subset/source combinations reconstruct their original bytes. The188
winning source streams also pass canonical encode-decode-encode identity checks.
Three independent exhaustive path-enumeration controls verify shortest costs on
small overlapping-fragment examples with actual used-binding table costs.
26 malformed-stream/operand controls pass, including unknown distinct bindings,
wrong versions, noncanonical lengths, invalid variants, duplicate names, aliased
operand slots and indentation bounds. A metadata-construction failure before
selection was retained as `failed-attempt001`; it changed no source or stream.

Seven reconstructed pairs pass610 existing independent cases and17 public examples
per language.28 additional invalid-input guard executions retain the expected
language-specific exceptions. Expected outputs never enter candidate sandboxes.
The original188 source hashes, all six baseline books and production recognition
catalog remain unchanged. No protected data, training or new dependency was used.

The chosen menus make17 fragment calls across seven problem pairs, covering2,819
of106,839 source bytes. **104,020 source bytes (97.36%) remain lexical/raw fallback,
and zero complete programs use semantic fragments alone.** This is a bounded
representation experiment and a measured stopping decision, not autonomous2a/2b
success or evidence that a complete learnable256-entry language has been found.

## Reproduction

The immutable run contract, candidate menu, all48 books/streams/subset results,
validation receipts and exact executed tooling are retained in the private run.
Tracked scripts reproduce the selection on128 with existing Python/Babel/Node.
Execution order is prepare, run, validate, package. Scripts pin the workspace and
run name; use a new output name for a replay and retain parent hashes rather than
overwriting artifacts. Selection consumed2.36 seconds measured wall time; execution
checks ran serially under one CPU and1,536MiB. Unrelated serving jobs stayed active.
