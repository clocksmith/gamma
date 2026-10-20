# Joint source and literal recomposition

The follow-up [working language and full assembly examples](working/README.md)
cover20/20 problems using79 literal strings at7 bits per selection, verified
directly from packed files. This report retains the source-search comparisons.

This second pass removes the historical four-bit vocabulary cap. It compares
20 distinct known JavaScript problems with three source arms: the frozen
standalone baseline, eight manually authored shared-counting rewrites, and six
mechanically selected rewrites. Original accepted sources remain preserved in
`../sources/original`. The human user owns 1a/1b; this experiment changes no
recognition, corpus claims or protected evaluation data.

## Actual rewrite mechanism

`rewrite.cjs` uses the already installed Acorn parser and four deliberately
bounded AST patterns. It replaces an inline Map frequency loop with
`countValues`, Set cardinality with frequency-map cardinality, Set membership
with frequency-map membership, or a signed-32-bit XOR fold with count parity.
The guard requires canonical names and a standalone `solve` interface, rejects
helper collisions, and restricts Set uses to membership/size queries. This is
an offline, manually designed rewrite pass, not an inferred semantic optimizer.

The generic Map rule matches 242, 594 and 657. Other rules match 136, 575 and 771.
The remaining fourteen programs are returned byte-for-byte unchanged. Every
changed program contains the complete 167-byte helper. Input prefix/tail spans
and hashes are recorded by the reproduction command. The XOR rewrite increases
auxiliary memory from constant space to one Map entry per distinct value. The
rules assume ordinary inputs, unmodified built-ins, no source/stack reflection,
and no externally supplied callbacks whose behavior depends on the call stack;
their specific domains
are returned in the transformation metadata. They are not a hostile-code sandbox.

The separate authored arm rewrites 136, 169, 242, 387, 575, 594, 771 and 961.
Its majority and repeated-element transformations rely on the original problem
promises. It must not be confused with mechanically generated alternatives.

## Dictionary search

Uniform source arms compare characters, lexical pieces, lines, whole programs,
and 16/32/64/128/256/512 adjacent-pair merges, with and without the complete
helper as a candidate literal. All literals are flat UTF-8 strings; a helper
entry stores its entire text. Exact dynamic-programming segmentation minimizes
selections for each fixed source/dictionary pair.

After deduplicating identical sources, the experiment exhausts 3,888 source
combinations under each of two fixed strategies: 64 or 128 lexical pair merges,
plus an explicit helper candidate and exact segmentation. This exhausts the
finite declared source-choice pool for those two heuristics. It does not find
a global optimum over JavaScript rewrites or all possible dictionaries.

The retained Pareto frontier uses vocabulary cardinality, dictionary storage
bytes and total selections. Whole programs remain a valid costed baseline.
Results also retain median/worst selections, framing and program bytes, source
choices and search cost. No arbitrary weighted score selects a universal winner.

## Reproduce

From this directory, with existing Python, Node, Acorn and the repository judge:

```bash
node test_rewrite.cjs
node generate.cjs /tmp/literal-rewrite-reproduction
python3 -B experiment.py --output /tmp/literal-joint-reproduction
python3 -B verify.py --output /tmp/literal-rewrite-execution
python3 -B controls.py --output /tmp/literal-dense-controls
python3 -B summarize.py
```

Output directories must be new. `generate.cjs` verifies baseline and output
hashes and emits complete files plus transformation provenance. `verify.py`
checks the committed experiment packets in `results/encodings`, reconstructs
all source variants, and executes only new source bytes against the unchanged
independent development checks. Identical prior sources reuse hash-bound passing
evidence. Expected values stay outside the sandbox. All changed programs are
checked for outputs and input preservation. These are development checks, not
protected evaluation or proof for every possible input.

Exact dictionaries and sequences are in `results/encodings`; all trial metrics
are in `results/results.json`. Unretained trial encodings are reproducible from
their source choices and dictionary construction parameters. Autonomous assembly
from a problem description and 3b unseen evaluation remain untested.

## Measured outcome

The main search completed **7,825 trials** in 245.76 seconds on one CPU, including
two strategies for every one of the 3,888 distinct source combinations. A further
32 unchanged-source controls (lexical merge steps 8 through 256, step 8) took
1.69 seconds. The combined three-objective frontier retains 63 trial points,
including duplicate metric vectors. All 2,540 retained packet/program
reconstructions match their source hashes.

**14 new complete sources passed all 2,488 independent output and input-preservation
checks.** The other 26 shared/recomposed entries reuse identical previously tested
source bytes. The prior 20 baseline sources remain hash-bound to their original
passing evidence. These solving checks are separate from 25 rewrite matcher tests,
independent source review, and synthetic codec/verifier tests.

The denser baseline matters: an apparent win at a 2,048-byte dictionary budget
under the sparse sweep disappears when the unchanged-source control is sampled
more finely. Do not promote the shared-source arm as a general improvement.

| Measured encoding | Literals | Dictionary bytes | Total selections | Median | Worst |
|---|---:|---:|---:|---:|---:|
| Baseline, 64 lexical merges | 140 | 1,258 | 843 | 40 | 87 |
| Mechanical shared helper in 242/594/657 | 140 | 1,419 | 813 | 37 | 87 |
| Baseline, 88 lexical merges | 149 | 1,484 | 720 | 34 | 75 |
| Baseline, 120 lexical merges | 163 | 1,877 | 602 | 27.5 | 62 |
| Baseline, whole programs | 20 | 4,302 | 20 | 1 | 1 |

The 140-literal rewritten point saves 30 selections (3.56%) but adds 161 dictionary
bytes (12.80%). With the current explicit 32-bit-ID packet format, total package
size increases from 5,430 to 5,471 bytes. Thus it is a Pareto tradeoff, not an overall
compression win. Dictionary bytes include an 8-byte header and four bytes per
literal length plus every UTF-8 byte. Each program packet adds a 40-byte header
and four bytes per selection. No hypothetical bit-packing savings are credited.

At dictionary budgets 512/768/1024/1280/1536/2048/3072/4096/8192 bytes, none of the
rewritten candidates beats the best measured unchanged-source control in total
selections. All alternatives and tradeoffs are retained; no global optimum or
impossibility claim follows from this finite search.

## Concrete before/after and sharing

For anagram equality (#242), the frozen baseline begins with an inline frequency
loop, then decrements counts for the other string:

```js
const counts = new Map();
for (const value of values) {
  counts.set(value, (counts.get(value) || 0) + 1);
}
```

The mechanical version replaces that exact AST pattern with:

```js
const counts = countValues(values);
```

The complete 167-byte `countValues` definition is prepended to every rewritten
source; it is never injected for free. In encoding
[`fdd94e86cfb2e1ed4f07`](results/encodings/fdd94e86cfb2e1ed4f07.json), literal 93
stores that entire definition and is selected by 242, 594 and 657. Their complete
program sequences fall from 54/55/54 selections to 43/45/40. Other programs incur
some dictionary retokenization costs, leaving a net saving of 30 selections.
Compare the full [before](../sources/normalized/0242.js) and
[after](sources/recomposed/0242.js), not just these explanatory fragments.

The reusable mechanism is now working and tested, but this particular
counting-family recomposition is not a universal improvement. A further search
would need additional correctness-checked source families or better dictionary
construction, with the same dense controls and full-source accounting. Nothing
here establishes autonomous selection from natural-language problem statements.
