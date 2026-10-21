# Literal-only budget comparison

[Experiment index](../INDEX.md) · [Frozen search contract](results-v1/contract.json) ·
[Selected packages](selected-v1/summary.json) · [Execution receipt](execution-v1/report.json)

**58 flat literal strings reconstruct all twenty programs in 77 selections at
six bits per selection: 462 selection bits.** Programs decoded from the actual
selected packets passed all 3,834 existing development checks. No entry contains
a whole program, and no characters, bindings, wrappers or helpers are injected.
This is a lower-input-cost representation with a larger stored dictionary,
not a general compression win, learned solver or new algorithm.

## Matched budgets and complete costs

Coverage is the first selection criterion, then total selections at the declared
width, then stored dictionary bytes. The same frozen twenty tasks and the same
three previously tested source arms participate at every budget. A retained
winner competes at every smaller or larger cap it fits; its IDs are repacked at
that cap's declared width. This matters: the 58-entry candidate discovered in
the 128-entry search also fits the 64-entry cap.

| Cap | Width | Used entries | Complete programs | Selections | Selection bits | Dictionary bytes | Dictionary + packets |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 16 | 4 | 16 | 9/20 | 23 | 92 | 1,300 | 1,682 |
| 32 | 5 | 30 | 14/20 | 44 | 220 | 2,397 | 3,006 |
| 64 | 6 | 58 | 20/20 | 77 | 462 | 4,086 | 4,972 |
| 128 | 7 | 58 | 20/20 | 77 | 539 | 4,086 | 4,983 |
| 256 | 8 | 58 | 20/20 | 77 | 616 | 4,086 | 4,983 |

Incomplete rows encode only their covered programs: do not compare their smaller
totals as if they solved twenty tasks. Missing problem IDs are explicit in each
manifest. Failure at 16/32 entries is a bounded search result under this
experiment's admission rule, not a mathematical lower bound.

The retained [shared79 control](../pass2/working/packages/shared7/manifest.json)
uses 154 selections / 1,078 bits / 4,468 total bytes. The new six-bit point halves
selections and reduces selection bits by 57.1%, while adding 504 package bytes.
The stronger [unchanged-source line control](../pass2/working/packages/baseline7/manifest.json)
uses 141 selections / 987 bits / 4,415 bytes. Relative to that control the new
point saves 64 selections and 525 selection bits, but adds 557 package bytes.
The [compact140 control](../pass2/working/packages/compact8/manifest.json) remains
smaller in storage at 3,052 bytes, with 813 selections / 6,504 selection bits.

LTD1 dictionary framing and every stored UTF-8 byte are charged. Each LTV1 packet
adds 41 framing bytes. The six-bit package has 820 framing bytes, 462 selection
bits and 66 padding bits, giving 886 packet bytes. Explanatory JSON and decoded
source copies are not compact payload. Human navigation, corrections and time
were not measured.

## What changed, and what did not

The search considers exact lines and the explicitly stored counting helper from
the baseline, authored shared and mechanically recomposed source arms. It chooses
the shortest representable source alternative for each problem and proposes
adjacent-string merges. Every trial reruns exact shortest segmentation and prunes
unused entries. The bounded strategy uses four seeds and at most 64 accepted
moves per seed/cap. When a dictionary cannot fit, greedy program admission retains
only complete programs. All resulting strings are stored in full.

Whole sources are forbidden. A one-off chunk is limited to two nonempty lines and
160 UTF-8 bytes; a unique `solve` declaration cannot be merged with its body.
Larger chunks must occur in source alternatives for at least two distinct tasks.
These are explicit experimental constraints, not a theorem about the right
granularity. Old whole-program controls remain preserved elsewhere.

The winning dictionary has **8 entries used across multiple selected programs,
accounting for 27/77 selections**. Shared79 has 14 such entries / 89 of 154
selections. Fewer selections here do not mean more cross-problem reuse.
In particular, the counting helper's text appears inside three larger literal
prefixes. Their repeated stored bytes are a real cost. The largest prefix
supplies 72.1% of the harmonious-subsequence source, but is also used in the
single-number program; the changed algorithmic condition remains another literal.
These are inspectable strings, not necessarily complete AST nodes.

No new JavaScript source was authored or rewritten in this comparison. It
optimizes dictionaries and selection among the already-tested source rewrites.
The 36,183 evaluated merge candidates took 313.18 seconds on one Mac CPU.
[Search traces](results-v1/trials.json) retain accepted merges and evaluation
counts per seed; rejected trials are reproducible under the frozen algorithm,
not individually stored encodings. No global optimum is claimed.

## Exact pieces and complete assemblies

The six-bit package contains [all 58 strings](selected-v1/budget-64/dictionary.json),
[every sequence and hash](selected-v1/budget-64/manifest.json), the
[counted binary dictionary](selected-v1/budget-64/dictionary.ltd), and
[all complete decoded programs](selected-v1/budget-64/assembled).

- Anagram equality: `[52, 37, 38, 17, 47]`, five selections / **30 bits**.
  [Complete assembled program](selected-v1/budget-64/assembled/0242.js).
- Harmonious subsequence: `[51, 16, 49]`, three selections / **18 bits**.
  [Complete assembled program](selected-v1/budget-64/assembled/0594.js).

Literal 51 stores the entire counting helper, a blank line, the `solve(values)`
declaration, count-map initialization, zero accumulator and loop opening.
Literal 16 is exactly:

```javascript
    if (counts.has(value + 1)) result = Math.max(result, count + counts.get(value + 1));
```

Literal 49 closes the loop, returns the accumulator and closes the function.
The JSON dictionary records actual newline characters and exact whitespace.
Nothing is supplied by this explanation or by an external runtime helper.

## Verification and reproducibility

All five selected packages were decoded and checked against the frozen
[source manifest](../pass2/source_manifest.json). Host128's existing Linux judge
executed each distinct `(problem, decoded source hash)` once: **22 source/task
pairs, 4,107/4,107 output and input-preservation checks, 27 sandbox calls**.
Each complete twenty-program package maps to 3,834 passing checks. Identical
sources across widths share that execution evidence; the checks were not
independently repeated five times. Expected results stayed outside the sandbox.
[Raw observations and native receipts](execution-v1/observations) are preserved.

Development controls: 7 budget/selection tests, 18 existing literal/oracle tests,
3 bit-packing tests, and all 37 Linux judge/lane checks passed. The Mac's 27
Linux-only checks were initially skipped and subsequently ran on128; they are
not being counted as Mac passes. An initial wrong unittest invocation and a
repacker syntax error were corrected before the reported runs. No full CI,
protected scoring, corpus admission, GPU work or model training was performed.

From this directory, use fresh output paths:

```bash
python3 -B -m unittest -v test_compare
python3 -B compare.py --output /tmp/literal-budget-search
python3 -B repack.py --search /tmp/literal-budget-search --output /tmp/literal-budget-selected
python3 -B verify.py --packages /tmp/literal-budget-selected --output /tmp/literal-budget-execution
python3 -B ../pass2/working/assemble.py \
  selected-v1/budget-64/dictionary.ltd \
  selected-v1/budget-64/programs/0594.ltv --output /tmp/harmonious.js
```

Only execution requires the existing Linux Node/bubblewrap judge. CPU dictionary
search and decoding run on the Mac. The repacker records its parent manifest and
contract hashes; the selected manifests bind every packet and decoded source.
Preserve `results-v1`, `selected-v1` and `execution-v1` as separate immutable
search, selection and execution evidence.
