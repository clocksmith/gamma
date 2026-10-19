# Corpus macro representation analysis

Two parameterized fragment entries reconstruct shared pieces across five problems
in both languages: one breadth-first level collector and adjacent-duplicate pointer
skipping. The complete streams save327 bytes across the94-problem paired corpus
relative to a syntax-only lexical profile, but the dictionaries cost2,943 extra
bytes. **The two-fragment profile loses2,616 bytes on one complete corpus pass.**
That is a measured representation tradeoff, not autonomous-solving improvement.

## Exact admission accounting

The first wave contains100 unique problems. The five foundation problems are252,
1046,1464,1512 and1748; none overlaps the wave. Therefore the union is105, with94
admitted and11 unadmitted. Do not subtract the foundation five from the wave count.
The table lists retained valid-domain/quarantined existing cases; those domain
regressions do not retroactively pass the frozen full-set gate.

| ID | Problem | Why full-set admission remains withheld | Valid/quarantined |
|---|---|---|---:|
| 1 | two-sum | Frozen tests include absent or multiple index-pair answers; statement guarantees exactly one. | 32/48 |
| 17 | letter-combinations-of-a-phone-number | Frozen tests include digit1 and strings beyond the four-digit bound; reference negative indexing is not phone semantics. | 76/3 |
| 33 | search-in-rotated-sorted-array | Frozen tests include arrays that are not rotations of an ascending distinct array. | 122/9 |
| 39 | combination-sum | Frozen tests violate distinct positive2..40 candidate/size/target bounds; duplicate-input reference output repeats combinations. Chunked output also hit the cap. | 30/63 |
| 45 | jump-game-ii | Frozen tests include unreachable last indices, contrary to the stated guarantee. | 36/8 |
| 50 | powx-n | Frozen tests include out-of-range bases, exponents or mathematical results; nonfinite output remains rejected. | 63/20 |
| 60 | permutation-sequence | Frozen tests include k outside1..n!; candidate and reference differ outside that domain. | 56/2 |
| 65 | valid-number | Frozen tests include nonstring input and strings longer than20. | 239/67 |
| 74 | search-a-2d-matrix | Frozen tests violate sorted-row, strictly ordered row-boundary or integer-range constraints. | 131/12 |
| 81 | search-in-rotated-sorted-array-ii | Frozen tests include arrays that are not rotations of a nondecreasing sequence. | 74/3 |
| 87 | scramble-string | All12 quarantined Scramble String cases have unequal input-string lengths. | 97/12 |

No excluded source was mined. Their originals, test expectations, failed receipts
and separately scoped domain evidence remain unchanged.

## Bounded analysis and candidate ranking

The [source manifest](source-manifest.json) freezes188 admitted implementations.
Existing Babel parses JavaScript; Python uses its standard AST. Matching statement
shapes parameterizes identifiers, preserving properties, operators and literals.
The bounded search accepts20..700-character statements with at least five AST
nodes and occurrences in at least two problems. It found57 recurring JavaScript
groups and25 Python groups. This is structural evidence, not a semantic proof:
wrappers such as forwarding to an implementation are not promoted as algorithmic
reuse, and overlapping parent/child candidates are not counted independently.

[Ranked candidates](ranked-candidates.json) and [actual binding/instruction examples](binding-examples.json):

1. **Collect one BFS level:**102 ordinary level order,103 zigzag level order,
   107 bottom-up level order. The same fragment is instantiated three times in
   each language. JavaScript reads a frontier array and appends values and children
   to separate arrays; Python consumes exactly the initial deque length and
   appends children on that deque. The language-specific effects are explicit.
   Actual complete streams for these three programs fall from883 to725 bytes in
   JavaScript and898 to757 in Python, including bindings and remaining source.
2. **Skip adjacent duplicate values:**15 Three Sum and18 Four Sum. Both leftward
   and rightward variants share one entry, with a paid direction byte and explicit
   array/pointer bindings. Four uses per language. Complete streams fall from1258
   to1186 bytes in JavaScript and795 to707 in Python. This preserves existing
   sorted-input and in-range-pointer preconditions; it does not sort or mutate
   the input array itself.
3. **Whole BFS level loop:** structural reuse in102/107, but overlaps candidate1.
   Not promoted; its coverage and raw sizes must not be added to candidate1.
4. **Bounded integer-list guard:** structural reuse in1512/1748 in both languages.
   Domain bounds and language-specific exceptions need an explicit contract.
5. **Advance linked-node cursor:**11 JavaScript occurrences across seven problems.
   Small and common, but nullability and reference effects are context-dependent;
   no generic or Python-equivalent fragment is claimed.

Only the first two are included in the measured semantic profile. Each has a
closed language-specific template: no arbitrary source-body operand. Identifier
operands and direction select names and a fixed expansion variant. Original
bindings and algorithms are retained. Candidate ranking is a bounded engineering
choice informed by recurrence and measured reuse, not global vocabulary optimality.

## Complete input and codebook cost

All values below are actual serialized bytes. Each byte corresponds to eight
ideal binary presses; [metrics](metrics.json) also report bits. The lexical profile
has128 ASCII entries,126 fitted shortcuts, END and literal-run controls. The hybrid
replaces two shortcuts with two parameterized fragments. The whole-solution
baseline has94 exact solution bodies plus two controls, occupying96 slots. It is
legitimate bounded stored representation, but is not evidence of generalization.

| Language | Profile | Slots | Complete stream bytes | Codebook bytes | One pass, including codebook |
|---|---|---:|---:|---:|---:|
| javascript | lexical | 256 | 35,426 | 10,769 | 46,195 |
| javascript | semantic | 256 | 35,292 | 12,220 | 47,512 |
| javascript | whole | 96 | 3,854 | 65,282 | 69,136 |
| python | lexical | 256 | 24,223 | 10,507 | 34,730 |
| python | semantic | 256 | 24,030 | 11,999 | 36,029 |
| python | whole | 96 | 3,854 | 52,808 | 56,662 |

Each stream includes38 bytes of magic/version, language/profile and codebook hash;
a binding count; every UTF8 binding name and length; all macro IDs, variant,
indentation and slot-reference operands; all lexical/raw remainder; and END.
Signatures and constants are not supplied through a free side channel. Fixed
step/offset1, tree-field names and control operators are part of the paid codebook.
The two semantic profiles use14 fragment calls total, plus14 variant bytes,
14 indentation operands and54 binding-reference bytes. Identifier table lengths
and bytes are charged too. ASCII identifiers and literals outside fragments remain
in the measured lexical remainder. Python's non-ASCII comments use explicit raw
UTF8 controls and length/payload bytes. A byte-by-byte audit reconciles every total.

Dictionary cost is the exact canonical UTF8 JSON serialization, including bodies,
schemas and semantic contracts. It is not a minimal compressed-description bound.
The shared codec implementation is6,830 bytes, reported separately. The new fitted
profiles are experiment artifacts; no deployed byte256 alphabet was changed.

At the observed mix, paying the dictionary once, the hybrid first strictly beats
lexical after11 complete JavaScript corpus repetitions or8 Python repetitions.
Whole-solution dictionaries first beat lexical after2 JavaScript repetitions or3
Python repetitions. These are repeat-use amortization figures for the same known
corpus, not claims about new problems. Source-aware encoding picks short streams
offline; there is no model choosing the correct solution or fragment sequence.

## Reconstruction and execution evidence

All564 profile/source combinations reconstruct the exact original UTF8 bytes and
re-encode to the identical stream. Exact identity preserves algorithms, public
interfaces, mutation, reference aliases and exceptions; it is stronger than merely
matching a formatted source appearance. The two fragments account for seven
calls per language across five problems. All94 programs still require lexical/raw
remainder in that profile: **zero full programs are represented solely by those
two semantic entries**. Whole-solution one-entry coverage is94 per language and
stores every body in its explicitly charged dictionary.

The five reconstructed program pairs pass409 unchanged independent cases and11
public examples per language in the existing isolated Linux judge. Expected
outputs stay outside candidate sandboxes.24 malformed-stream/operand controls
reject missing/trailing data, profile mismatch, invalid variants, unknown slots,
noncanonical lengths and duplicate fragment handles. These are reconstruction
and software checks on consumed development evidence, not new autonomous solves.
The generic decoder is not a new type/scope verifier: valid tree/list types, fresh
local names and semantic preconditions come from the reviewed occurrences. No
claim of arbitrary safe fragment composition is made.

## Reproduction and preservation

Exact executed scripts are retained here and in the ignored run's `executed-tooling`.
The run contract binds source/catalog/wave hashes; the metrics bind all scripts,
analysis, validation and byte-accounting artifacts. Existing Node/Babel and the
Gamma Python environment were used without downloads. The serial scope was limited
to one CPU and1,536MiB; unrelated model-serving workloads were left running.

Execution order: `macro_freeze.py`, `macro_mine.py`, `macro_analyze.py`,
`macro_validate.py`, `macro_accounting.py`, then `macro_package.py`. Scripts pin the
128 workspace and immutable run name. For a replay, copy the retained tooling to
a new named run, update only its declared output path, and retain the original
script hashes as parents; never overwrite this run or its receipts. Source and
codebook bodies, binary streams, AST examples and complete verdicts remain private
under `runs/corpus-macro-analysis-128-v1`; public Git push is not part of this work.

Production recognition, the original model experiment, protected reservations,
training and the deployed256.one app remain unchanged. This completes the bounded
analysis task; it does not complete autonomous goals2a/2b or select a final256-entry
semantic language. The next useful test is a separately sealed corpus split and
fragment selector after a bounded vocabulary has been specified and frozen.
