# Literal composition pilot: joint source and vocabulary optimization

[Experiment index: versions, lineage, languages, evidence and proposals](INDEX.md).

The current goal is to recompose correct solutions into consistent, reusable
literal pieces and measure the vocabulary/storage/program-length tradeoff.
The owner removed the four-bit restriction on2026-10-20 at16:50UTC. Vocabulary
size is now an experimental variable. The earlier sixteen-entry experiment is
preserved below as a historical baseline, not the active acceptance constraint.
This first checkpoint provides tested source alternatives and reproducible
encoding/search tools; it is not an autonomous solver.

The [goal contract](../contracts/literal_composition_goals_v1.json) keeps goals
1a/1b (identification and selection), 2a/2b (parameterized macros), and 3a/3b
(literal composition) separate. A literal is an actual string containing actual
names and syntax. Concatenation adds nothing. There are no NAME/VALUE/EXPRESSION
slots, free renaming, injected helpers, raw-source escapes, interpreter tricks,
or problem-dependent dispatch inside the emitted program.

## Measured checkpoint

All 80 complete source versions passed **15,336 development cases** in
100 isolated sandbox calls. The independently authored inventory contains
3,834 cases across twenty problems; each was run against four source versions.
Input preservation was checked. These are development tests, not fresh held-out
evaluation, mathematical equivalence proofs, or official judge acceptance.

The general comparison measured 144 configurations in 4.18 seconds; the
four-bit search evaluated 4,490 states in 2.25 seconds on host128's CPU.
Execution took 6.34 seconds. Timing is one observed run, not a latency guarantee.
No models, downloads, training, protected fixtures, or 3b holdouts were used.

The original-class-interface tradeoffs below reconstruct all twenty programs.
All rows are allowed comparisons under the updated variable-size objective.
The historical sixteen-entry search could not represent all twenty programs.

| Method, idiomatic source | Entries | Literal UTF-8 bytes | Stored dictionary bytes | Total selections | Median | Worst |
|---|---:|---:|---:|---:|---:|---:|
| Characters | 74 | 74 | 378 | 4,598 | 234.5 | 362 |
| Character pair merges, 64 steps | 112 | 247 | 703 | 1,880 | 101.5 | 163 |
| Lexical pair merges, 64 steps | 157 | 884 | 1,520 | 899 | 42 | 89 |
| Exact lines | 94 | 3,555 | 3,939 | 181 | 10.5 | 14 |
| Whole programs | 20 | 4,598 | 4,686 | 20 | 1 | 1 |

Within these measured choices, a 1,600-byte dictionary ceiling favors the
64-step lexical merge point for selection count. A 4,000-byte ceiling permits
the line dictionary with 181 selections. Neither met the historical
sixteen-entry restriction. There is no universal best row; the complete
[Pareto frontiers](summary.json) retain storage/cardinality/selection tradeoffs.

Changing the call interface to standalone `solve(...)` reduces source bytes
from 4,598 to 4,214. Its lexical-64 point uses 140 entries, 1,258 dictionary
bytes and 843 selections; whole-program storage still requires twenty entries.
This separate profile includes the entire `function solve` declaration and
all body bytes. It is not directly LeetCode's `class Solution` interface and
does not receive a free adapter. Its frontier is reported separately.

The bounded joint search re-mined dictionaries after changing one program to
another tested source version. It evaluated 60 distinct neighbors under explicit
dictionary-byte ceilings and found no improving move from its selected seeds.
Fixed-source line additions/deletions also failed to improve the retained
frontiers. This does not establish local or global optimality outside the
declared candidate pool and move schedule.

## Exact format and cost

- `LTD1`: four-byte magic, uint32 dictionary count, then a uint32 UTF-8 byte
  length and the complete bytes of each literal. Cost: `8 + 4K + literal_bytes`.
- `LT41`: four-byte magic, 32-byte dictionary SHA256, uint32 selection count,
  then packed four-bit IDs. Cost: `40 + ceil(N/2)` bytes. Selections cost
  exactly `4N` bits; an odd selection count adds four zero padding bits.
  IDs outside the dictionary, nonzero padding, trailing bytes and K>16 fail.
- General over-cap diagnostics use `LTP1`, with the same forty-byte framing
  and uint32 IDs. Their `program_bytes`/`package_bytes` fields are **not**
  four-bit costs. Infeasible four-bit metrics are null.

Names, constants, punctuation, whitespace and wrappers are in the dictionary
and sequences. Literal entries are flat strings even when pair merging proposed
them. The decoder requires no grammar expansion or source file. Source manifests,
problem labels and research reports are provenance, not inputs to the decoder;
their storage is not presented as part of the compact wire format. Human problem
selection, navigation and correction costs were not measured.

## Before and after

For #575, the original accepted source explicitly counts object keys, then
compares the count to half the input length. The preserved [original](sources/original/0575.js)
is 592 bytes; the alternative is a complete program:

```javascript
class Solution {
  distributeCandies(values) {
    return Math.min(new Set(values).size, Math.floor(values.length / 2));
  }
}
```

This is an offline authored rewrite, tested independently. It does not prove an
optimizer discovered `Set`. Both versions preserve the input. See
[all rewrite rationales](source_reasoning.json) and the
[source manifest](source_manifest.json). Cost changes include #643's extra O(k)
temporary storage and #1051's use of engine-provided sorting; no speed or memory
improvement is claimed.

## Reproduce and inspect

Run from this directory with Python3 and the repository's existing Linux
Node/bubblewrap/prlimit judge dependencies. No package installation is needed.

```bash
python3 -B -m unittest -v test_literals test_checks
python3 -B experiment.py --output /tmp/literal-baseline-reproduction
python3 -B search16.py --output /tmp/literal-cap-reproduction
python3 -B reconstruct.py results/encodings/c8207770976a7b2c392e.json 0575 --output /tmp/candies.js
python3 -B verify_execution.py --output /tmp/literal-execution-reproduction
python3 -B summarize.py
```

Output directories must not already exist. The baseline and capped-search
outputs contain exact dictionaries and program sequences, complete configuration
choices, hashes, costs and search traces. `verify_execution.py` decodes every
saved baseline packet and executes each distinct reconstructed source version
against the independent checks. Expected values remain on the host; only source,
invocation inputs and the evaluation harness enter the sandbox. A normalized
program is called through `solve`, not an injected official-method wrapper.

Shortest segmentation uses dynamic programming over source offsets. It is exact
for a fixed source and dictionary; greedy longest-match can be wrong. Mining
compares characters, lossless lexical pieces, lines, whole programs, adjacent
pair merging, shared-only merging, fixed-source dictionary moves and a bounded
source-choice search. The capped search keeps at most eight dictionary states
per depth, proposes prefixes up to96 characters plus complete suffixes and lines,
and stops at sixteen literals. This narrow heuristic can miss feasible languages.

All sources and tests concern these distinct known tasks:

| ID | Task | ID | Task |
|---:|---|---:|---|
| 121 | Best stock profit | 136 | Single unpaired number |
| 169 | Strict majority | 242 | Anagram equality |
| 387 | First unique-character index | 551 | Attendance eligibility |
| 575 | Candy-type allocation | 594 | Harmonious subsequence length |
| 605 | Flower placement feasibility | 643 | Maximum fixed-window average |
| 657 | Robot returns to origin | 674 | Increasing contiguous run |
| 704 | Binary search | 709 | ASCII lowercase |
| 724 | Pivot index | 771 | Jewel/stone membership count |
| 961 | N-times repeated value | 1051 | Height-order mismatches |
| 1108 | Defang IPv4 text | 1119 | Remove vowels |

Selection was deliberate, not random. Domains and input hashes are in
[the independent checks](checks.py); original provenance and notices are in
[ATTRIBUTION.json](ATTRIBUTION.json) and [notices](notices/NOTICE.txt).
The original source corpus is unchanged. No corpus acceptance was added.

## Working 4–8-bit language

The [concrete shared language](pass2/working/README.md) now reconstructs all twenty
problems with79 literals and7 bits per selection. The154 selections include real
JavaScript statements and a helper reused across eight programs; no entry is a
whole solution. Programs decoded from the packed files passed3,834/3,834 checks.
The guide shows two complete before/after examples, dictionary IDs and full byte
accounting. An alternative140-literal language fits8 bits per selection.

## Remaining work and ownership

The human user owns 1a/1b and the corpus continuation. This task owns only
`literals/`, its new literal goal contract, and scoped goal/status documentation.
[Ownership and handoff](OWNERSHIP.md) records the boundary and corpus snapshot.
Existing macro work and the 256one application are unchanged by this pilot.

The completed [joint recomposition experiment](pass2/README.md) adds a guarded
AST rewrite pass, 3,888 source combinations and 7,857 dictionary trials including
dense baseline controls. Fourteen new source versions passed all 2,488 output and
input-preservation checks. Shared rewrites offer some vocabulary/selection
tradeoffs, but do not beat the denser unchanged-source control at the declared
dictionary-byte budgets. See the exact dictionaries, source sequences and
[measured summary](pass2/summary.json). Autonomous problem-description-to-sequence
assembly and unseen evaluation remain untested.
