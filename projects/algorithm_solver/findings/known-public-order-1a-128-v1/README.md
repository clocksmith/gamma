# Explicit public output order: Goal 1a coverage gain

The opt-in candidate answers **21/100** historical exact-answer-path gaps correctly,
versus **3/100** for the current control: **18 additional correct stored answers,
zero wrong acceptances, zero lost correct answers**. The three control successes
are the previously implemented multiline example repairs. This is exact known
problem development evidence, not informal Goal 1b or new recognition-release
qualification.

## Mechanism and scope

`answer(..., public_output_contracts=True)` binds only a complete explicit
requirement such as “You may return the answer in any order.” before worked
examples. Existing `return:unordered_outer` compares outer lists as multisets,
preserving inner order, multiplicity, values and types. No new judge/comparator,
weaker threshold, changed stored code, expected value or reference selection is
introduced. Explicit caller comparison modes take priority. Direct contradictory
ordered-output instructions disable this binding. Ordinary input-order wording
does not disable an explicit free output order.

The option defaults to **false**. The default route, historical approval manifest,
and protected boundaries are unchanged. The narrow parser intentionally leaves
unsupported paraphrases, arbitrary output properties and free inner order
unhandled. For example, Group Anagrams remains an abstention because its inner
group order also differs; this candidate does not flatten that distinction.

## Coverage classified before execution

The recovered index has 3,353 entries; 65 present entries are protected and 3,288
are eligible. The exclusion closure contains 66 keys, including one absent from
this index. The historical source-bound catalog still has 2,456 approvals and
832 eligible exclusions. These are the concrete causes recorded in
[coverage-causes.json](corrected-v2/coverage-causes.json):

| Cause | Entries |
| --- | ---: |
| Missing independent tests | 685 |
| Other public execution or output-contract gaps | 67 |
| Complete explicit unordered-return clause | 19 |
| No recoverable public examples | 14 |
| Missing SortedList/sortedcontainers dependency | 15 |
| Memory failures under the frozen limits | 10 |
| Missing datetime import | 1 |
| In-place source dataset checks only the None return | 19 |
| Unusable independent tests | 2 |

The runtime cause classification uses existing failure metadata; it does not
claim fresh execution of those 26 excluded references. The 100 exact-path entries
were all freshly executed below, not selected using new scores. The 685 missing
sets cannot be replaced by public examples or old pass flags; the 19 in-place
sets cannot qualify by checking only a None return. No dependencies were installed
and no resource limit was raised.

## Frozen corrected-v2 comparison

Both arms used the same 100 eligible exact inputs, complete 3,288-entry lookup,
selected source bytes, real Linux sandbox, and unchanged 120-second route /
30-second public and independent judge limits. Exact matching required no model.
The experiment cap was 300 seconds, two CPU threads, 6 GiB RAM and 1 GiB disk.
Runtime hashes cover actual recognition dependencies and exclude concurrent
composition files. All **200 public decisions were sealed before loading any
independent tests**. Original independent test contents and comparison rules were
unchanged. Protected examples, references and tests never entered selection or
execution.

| Outcome | Control | Opt-in candidate |
| --- | ---: | ---: |
| Correct accepted answers | 3 | 21 |
| Wrong accepted answers | 0 | 0 |
| Abstentions | 97 | 79 |

The 18 additional answers passed **38 public checks and 1,538 independent checks**.
All 21 answers together passed **45 public checks and 1,817 independent checks**.
Finite checks do not prove correctness. The 19 selected public contracts yielded
18 gains; the remaining selected case, Group Anagrams, continued to abstain.

[The corrected summary](corrected-v2/summary.json) records every case, verdict,
code hash and measured time. Raw source-bearing decisions remain ignored under
`runs/known-public-order-1a-128-v2`. All timings are shared-host, contended
measurements; they do not qualify latency.

## Review correction and retained first candidate

The first candidate missed direct contradictions such as “Return the answer
sorted” and “You must return the answer in ascending order.” Review reproduced
these using synthetic requirements. The first code and receipts remain intact at
`runs/known-public-order-1a-128-v1/public_contracts-frozen-v1.py` and the top-level
report artifacts. That implementation is superseded by separately frozen v2;
no result was overwritten.

V2 adds conservative recognition of those ordered-output instructions. Its
bounded rerun preserves all **200** answer/abstention decisions, source-code hashes,
identity results and contract selections: **19** contracts applied in both versions.
[Parity receipt](corrected-v2/parity.json) records that comparison. Fresh timing
was measured; historical timing was not reused.

Software checks separately passed **48 tests and 16 subtests** across public
contracts, answer routing, judge and lane suites. Tests reject altered inner
order, duplicate/missing rows, bool/float type substitutions, conditional and
quoted clauses, and contradictory order requirements. They also verify the
option is off by default and accepted output still runs through the real sandbox.

## Exact remaining gap and next work

This closes 21 of the historical 832 exclusions in development when combined
with the prior parser fix, leaving **811 entries without a new successful path**:
685 missing-test entries, 79 remaining exact-path gaps, 26 runtime failures and
21 unusable-evidence entries. The source-bound approval catalog remains at 2,456;
**2,477 is not a newly approved total**. A separately frozen current-runtime
qualification must bind these new paths to fresh execution and unchanged source
and test identities before an approval update. The unchanged 18/20 recognition
release gate also remains separate and unpassed.

The next coherent bounded implementation target is the 15 dependency failures:
inspect alternative stored references already present for those same identities
and qualify a source that uses supported dependencies, without substituting a
neighboring problem or generating source at query time. If none exists, keep the
gap explicit. In parallel, independent test authorship for the 685 missing sets
is the dominant coverage requirement. A broader free-output property validator
can address remaining exact-path gaps only with explicit query semantics and
adversarial validation; equality cannot simply be relaxed globally.

No training, model inference, downloads, new dependencies, serving interruption,
protected scoring, approval rebinding or public push occurred.
