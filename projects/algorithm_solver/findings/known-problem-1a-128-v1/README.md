# Goal 1a: exact stored-answer recovery on 128

The multiline public-example parser now returns three previously abstained known
solutions correctly. No solution, requirement threshold, comparator, reference
selection, or protected reservation changed. This is a Goal 1a exact-known-input
improvement, not the 16-case informal Goal 1b result.

## Coverage and acceptance

The original full index is present: **3,353 entries**. The current protected
closure contains 66 keys, 65 of which are present in this index, leaving
**3,288 eligible entries**. Protected records were excluded before constructing
queries, recovering examples, or loading independent tests. The frozen run
contract's `protected_excluded: 66` counts closure keys; the actual excluded
index-entry count is 65. This distinction does not change selected cases.

The metadata-only exact identity census correctly resolves **3,288/3,288** eligible
indexed statements/interfaces. This is identity evidence, not executed answer
correctness. Historical all-corpus self-retrieval was 3,353/3,353 and historically
2,538 returned references passed independent tests. The `run_contract.json`
150-problem solving sample is a comparison journey, not corpus coverage.

The preserved v2 catalog has **2,456 source-bound approvals / 3,288 eligible
entries (74.70%)**. Every approved entry still matches its recorded source hash.
The other eligible entries are:

| Exclusion | Entries |
| --- | ---: |
| Missing independent tests | 685 |
| Exact answer path not qualified | 100 |
| Failed stored solution | 26 |
| Unusable imported evidence | 19 |
| Unusable independent tests | 2 |

Five serving runtime files differ from historical approval bindings, listed in
[coverage.json](coverage.json). Consequently, this work does not relabel that old
catalog as a current-runtime release. No approval manifest was modified.

The authoritative [release contract](../../contracts/known_lookup_release_v2.json)
still requires at least 18/20 correct known paraphrase/sibling queries, zero wrong
or unqualified acceptances, and 4/4 absent rejections. Its earlier 13/20 failed
result remains unchanged; a new independent set is required for a changed
candidate. Exact self-identity cannot substitute for this recognition gate.

## Implementation and frozen comparison

The old parser captured one output line, rejecting valid multiline lists and
matrices. The new scanner follows quote/bracket boundaries, preserves all quoted
whitespace and escapes, and converts non-breaking layout spaces only outside
strings. The restricted AST data parser remains responsible for validity; it
never executes expressions. Input text is retained in full, so an extra input
line cannot disappear. Partial/unsafe examples still fail closed.

Before scoring, the comparison selected all 19 eligible catalog entries whose
exclusion was `exact_answer_path_not_qualified` and whose recorded public-example
count was zero. Both arms use the same stored reference, exact statement and
interface, index, thresholds, real sandbox, 120-second route allowance and
30-second public judge allowance. Exact identity requires no embeddings or
model initialization. The run was capped at 300 seconds, two CPU threads,
6 GiB memory and 1 GiB disk; it completed in 0.853 seconds of runner wall time.
All timings are from a contended shared host and provide no latency promotion.

All 38 public decisions were sealed before independent tests were loaded.
Independent tests score the original problem only after answer return. Raw
answers and decisions remain ignored under `runs/known-problem-1a-128-v2`.
Source/asset hashes and the decision seal are in [corrected-v2](corrected-v2/).

| Corrected comparison, 19 selected cases | Control | Candidate |
| --- | ---: | ---: |
| Accepted and independently correct | 0 | 3 |
| Wrong accepted answers | 0 | 0 |
| Abstentions | 19 | 16 |

| Recovered exact answer | Public checks | Independent checks |
| --- | ---: | ---: |
| Combination Sum II | 2/2 | 102/102 |
| Print Binary Tree | 2/2 | 63/63 |
| Rotating the Box | 3/3 | 114/114 |

The 3,288-entry public-parser census changes only five previously empty example
sets and changes **zero previously nonempty example sets**. The other two
recovered sets, Find Valid Matrix Given Row and Column Sums and Text Justification,
fail the unchanged public comparison and still abstain. The former permits
multiple valid outputs; the latter contains non-breaking spaces inside quoted
expected data. Neither was silently normalized or given a weaker checker.
This census does not execute the other 3,269 entries.

## Preserved rejected attempt

The first implementation inadvertently truncated multiline input after a complete
first-line expression. The full eligible static census caught one existing
parse loss and newly parsed design-operation examples whose input was incomplete.
That candidate is rejected despite its same three accepted outputs. Its code is
preserved at `runs/known-problem-1a-128-v1/candidate-importers.py`; its parser census,
contract, sealed decisions and summary remain in this report's top level.

The first runner also failed during reporting on `source: null`, after sealing
all decisions. [score_sealed.py](score_sealed.py) recovered scoring without any
route replay, retuning or changed decision bytes. The corrected comparison is a
separately named v2 run with the whole-input bug fixed and a null-safe scorer.
Use only **corrected-v2** for the final implementation's measurements.

Software checks passed separately: **46 tests and 10 subtests** across public
example parsing, the existing judge and lane suites; changed Python files
compile. Regressions cover multiline/nested data, quoted whitespace and labels,
escaped quotes, incomplete/executable outputs, and undiscarded input lines.

## Completion checklist and next executable work

- [x] Recover and distinguish full index, historical sample and qualified coverage.
- [x] Exclude protected aliases before example recovery or execution.
- [x] Reproduce and fix an exact-answer abstention defect.
- [x] Execute returned solutions in the real sandbox and independently score them.
- [x] Preserve rejected implementation and scoring failure; retain original gates.
- [ ] Qualify current serving runtime and the three new source-bound answer paths
  in a separately frozen approval refresh; do not rewrite the old manifest.
- [ ] Close remaining 97 exact-path gaps with public-contract checker work,
  public input binding, and imported-example repairs. Next bounded development
  action: implement an explicit nonnegative-matrix/row-column-sums property
  contract, rather than equating one displayed matrix with every valid answer.
  It must be selected from the query's explicit semantics and tested against
  adversarial invalid matrices before fresh independent scoring.
- [ ] Supply independently authored tests for 685 missing-test entries, repair
  21 unusable-evidence entries without manufacturing correctness, and diagnose
  26 stored-reference failures. These cannot be closed by similarity tuning.
- [ ] Qualify paraphrase and sibling matching on a new sealed independent set
  after development; existing opened release cases are no longer fresh evidence.

The dominant near-100% gap is independent evidence coverage and public-contract
execution, not exact indexed-statement identity. No training, downloads, new
dependencies, service interruption, protected scoring, or public push occurred.

The consumed release route constructs requests with explicit public examples;
`recover()` returns such requests unchanged, so the changed importer is not on
that path. This is code inspection, not a new 24-case execution or performance
claim. The historical query path recorded in the v2 contract is currently absent
on 128, so a direct input-file parity check was not performed. No alternative
query corpus was substituted. The original 13/20 result remains unchanged.
