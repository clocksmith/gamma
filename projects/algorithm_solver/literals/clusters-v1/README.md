# Larger clusters: fixed literal composition and dictionary merging

The experiment expands the original 20-problem development family to **40**,
and adds a separate **20-problem array/matrix cluster**. It freezes 48 fit and
12 development-heldback problems before inspecting new source bodies or tuning.
All 60 have independently checked source variants. A frozen 256-entry language
represents **48/48 fit and 11/12 heldback programs**: **59/60 overall**.

The best measured rewritten global dictionary needs **5,345 eight-bit selections**
on the 48 fit programs, versus 11,936 for the best fixed-source control and
10,070 for a naive deduplicated union of the rewritten cluster dictionaries.
Its full fit package is **9,413 bytes**, including a 2,100-byte dictionary and
all program framing. This is compression/representation of supplied code, not
autonomous synthesis from descriptions. The live demo and prior baselines are
unchanged.

## Frozen selection and exposure

[Contract and split](contract.json) · [source/dictionary freeze](vocabulary-freeze.json)
· [qualification chronology](verification.json) · [attribution](ATTRIBUTION.json).

Only the pre-existing eligible, previously qualified JavaScript development
export was used. Selected source hashes are pinned; no protected problem text,
solutions, independent tests, or 3b reservation material was opened. The human
owner's 1a/1b ledger was not modified. A historical eligibility snapshot supplied
family/status metadata only; no corpus runs or claims were resumed.

The original 20 remain in fit because they were extensively exposed in prior
literal experiments. New IDs were selected by category using export metadata;
all source material had already been authored/qualified in earlier corpus work.
The new heldback split therefore means **held back from this vocabulary fitting**,
not truly unseen tasks or a claim of semantic-family-disjoint generalization.
SHA256 of `gamma-literal-clusters-devheld-v1:ID` orders added IDs, taking eight
legacy additions and four array/matrix problems for heldback. All selected
metadata families are distinct, but semantic techniques overlap.

| Cluster | Total | Fit | Heldback | Rationale |
|---|---:|---:|---:|---|
| Legacy-expanded | 40 | 32 | 8 | Preserve the mixed original 20, adding string/counting/membership scans. Not a pure semantic cluster. |
| Array-matrix | 20 | 16 | 4 | Array/matrix transforms and numeric aggregation; disjoint problem IDs. |

**legacy-expanded fit IDs:** 121, 136, 169, 242, 387, 541, 551, 575, 594, 599, 605, 643, 657, 674, 682, 697, 704, 709, 724, 734, 748, 771, 806, 821, 824, 914, 917, 925, 961, 1051, 1108, 1119.

**legacy-expanded heldback IDs:** 645, 696, 796, 830, 844, 859, 893, 929.

**array-matrix fit IDs:** 566, 661, 832, 892, 908, 922, 942, 944, 976, 977, 1005, 1013, 1018, 1085, 1086, 1122.

**array-matrix heldback IDs:** 766, 867, 883, 896.

## Matched fit comparison

Every row below covers the same 48 fit problems with at most 256 stored entries
in aggregate. Separate mode stores two 128-entry dictionaries; its IDs take
seven bits and it pays one additional cluster-selector bit per program. Union
and global modes use eight-bit IDs and no selector. All entries are charged,
including unused fallback strings. Costs are from actual serialized packets.

| Method | Stored entries | Selections | Dictionary bytes | Selection bits | Cluster bits | Total package bytes |
|---|---:|---:|---:|---:|---:|---:|
| Best fixed-source global control | 256 | 11936 | 2504 | 95488 | 0 | 16408 |
| Rewritten separate dictionaries | 256 | 10673 | 2088 | 74711 | 48 | 13432 |
| Naive rewritten union/deduplication | 159 | 10070 | 1370 | 80560 | 0 | 13408 |
| Relearned global rewritten dictionary | 256 | 5345 | 2100 | 42760 | 0 | 9413 |
| Mixed source-choice AST/swap search | 254 | 8936 | 3137 | 71488 | 0 | 14041 |

[Full comparison](comparison.json) and [all 84 trials/frontier](search-v1/summary.json)
retain weaker candidates and all feasible 64/128/256-entry costs. The best fixed
control uses 32 lexical pair merges; the best rewritten candidate uses 64. With
**64 merges matched on both sides**, the fixed control needs 12,184 selections
and 16,558 bytes versus 5,345 and 9,413 after rewriting. This isolates the pipeline
comparison more closely; it still does not prove a globally optimal rewrite.
No shared candidate fit the 64-entry budget in this bounded proposal family.

The 48-entry whole-program diagnostic uses 48 selections but **24,338 dictionary
bytes** on canonical sources (26,354 total at eight bits). It is explicitly
memorization with no cross-program literal reuse, not the shared result.

The strongest shared dictionary has 161 entries used across multiple problems;
5,258/5,345 fit selections use shared entries. It stores 52 unused entries, all
charged. These were frozen as part of the finite candidate; the report does not
silently prune them after evaluation or claim optimality. Its fit median is 95
selections and worst case 344.

## Implemented rewrites and search

[Generator](generate.cjs), [fit lineage](fit-generated-v1/manifest.json), and
[heldback lineage](heldback-generated/manifest.json) preserve exact originals.
The fixed control converts a single Solution method to a fully counted solve
function while preserving helper bodies and names. The canonical arm inlines a
single-use tail delegate only when arguments are identical positional parameters,
and performs scope-resolved alpha renaming with capture avoidance. It preserves
property names/shorthand keys, function recursion and all concrete constants.
Reflective eval/Function/with contexts are unsupported. It does not invent new
algorithms or perform a general Object-to-Map conversion. Existing collection
construction and its semantics remain in the emitted, charged source.

These changes remove redundant wrappers and make local names/control structures
more consistent. They preserve algorithmic loops/allocations apart from one
constant-cost delegate call. Equivalence is supported by domain tests and exact
original result/input-effect parity, not proved for arbitrary JS contexts,
function identity inspection or reflective code.

AST/subtree signatures erase identifier/literal values **only for offline
similarity proposals**. Emitted entries are always complete concrete strings.
Single-link Jaccard clustering of fit signatures produced groups of sizes
**45,1,1,1** ([trace](search-v1/structural-clusters.json)); that chaining result is
not evidence of four useful semantic families. Nodes, up-to-three-line spans,
lexical tokens and repeated lexical pairs propose fragments. Heuristics rank
storage savings or selection savings, with a cross-structural-group bonus.
Unique long fragments and complete programs are excluded from shared proposal
arms; whole-program entries have a separate charged diagnostic.

The search learns each semantic cluster independently, measures their exact
union/deduplication, then relearns global dictionaries and tries bounded
add/remove/swap moves with full exact shortest-path resegmentation. The mixed
source-choice AST heuristic was weaker than the fixed-canonical lexical merge
candidate. More flexible search did not automatically produce a better dictionary.
All reported best rows are chosen from fit metrics only; no hidden weighted score
replaces the cardinality/storage/selection frontier.

The [search](search.py) completed its enumerated schedule in **84 trials / 2.60
seconds**, below 160 trials / 300 seconds, on one CPU thread with an 8 GiB address
space cap. No GPU, model, download or framework install was used. The planned
active source pool has 180 qualified variants. **One budget deviation is retained:**
the first invalid preflight generation adds 16 distinct superseded canonical
sources, making 196 distinct historical problem/source versions rather than the
planned 180 total. Those 16 were never executed or mined. Disk/memory/time limits
were preserved; historical failures were not deleted to conceal the deviation.

## Heldback expressibility without tuning

[Heldback report](heldback-expression/report.json) applies the hash-frozen rewrite
procedure and dictionaries to all twelve heldback programs. All **36 heldback
source variants pass 2,631 check executions** on 877 reference cases. The best
canonical dictionary represents eleven in **1,361 eight-bit selections**.
The unrepresentable program is **#929, Unique Email Addresses**: its source needs
`@`, absent from every relevant fit-learned alphabet. No escape, new literal,
source replacement or renaming rule was added after seeing that result.

This is an explicit finite-string expressibility failure despite correct supplied
source. The other successes partly rely on fully charged character fallback
entries; they do not show semantic discovery. Original/normalized and frozen
canonical expressibility are both recorded for each candidate. All broader
baseline source exposure is disclosed above. No autonomous or truly unseen 3b
claim is supported.

## Execution and artifact verification

[Checks](checks.py) independently specify the new forty development problems;
the existing original 20 oracle is reused. There are **6,759 distinct reference
cases**, 180 active source variants and **20,277 passing check executions** under
the final input-effect policy. Native runs actually executed 20,937 checks,
including a targeted 660-check recheck; 183 initial input-policy failures remain
in history. Expected values stayed outside the bounded Linux sandbox. Every
executed source was first reconstructed through the literal packet codec.

Two pre-search corrections are preserved in [preflight-failure](preflight-failure/receipt.json).
A synthetic recursion test caught unresolved global helper references during
renaming; scope resolution was repaired before execution/mining. The initial
oracle policy incorrectly demanded nonmutation from #976's retained in-place
sort. The corrected check requires its exact sorted input effect, and #832/#922
require input/result agreement. Every transformed variant must exactly match
its original's output and input effects. No candidate was fixed using heldback
feedback. The invalid first generated pool is retained as unqualified evidence.

[Audit](audit.json): 4,384 fit packets, 344 heldback packets and six selector files
verify exact bytes, source identities and costs. An additional 219 saved #942
observations pass strict integer checks for the nonunique permutation output.
Required judge/lane acceptance passed **37 tests** before experiments; ten guarded
rewrite checks and 378 exact segmentation parity cases plus two targeted search
checks passed. Tests cover recorded ASCII/integer/matrix domains and edge cases,
not formal equivalence, official judge acceptance, or all worst-case lengths.
Numeric cases include large bounded integers, long binary prefixes and floor
averages; no unsafe-integer or arbitrary-Unicode claims are made.

## Format and full costs

Each flat LTD1 dictionary costs `8 + 4K + sum(UTF8 literal bytes)`. Each program
uses existing LTV1: 41 header bytes plus packed IDs and zero padding. Fit framing
is 1,968 bytes. Separate mode additionally writes LTS1: eight header bytes plus
48 selector bits (six bytes). Selector padding, selection padding and both
dictionaries are charged. Joint modes need no cluster selector. Interactive
finish/undo/navigation controls were not exercised: recorded control bits are
zero **for this offline packet experiment**, not a claim of free UI interaction.

No wrappers, helpers, identifiers, constants, whitespace or punctuation are
injected by the decoder. Metadata, readable duplicate source views, raw check
observations and common codec implementation are excluded from compact package
metrics and listed separately in [artifact inventory](artifact-inventory.json).
Every decoder packet is sufficient with its exact dictionary; no problem-specific
source lookup or templated substitution is part of decoding.

## Exact working artifacts and examples

[256 literal strings and all fit sequences](search-v1/encodings/bc5239eeff4a513d94ab.json) · [binary dictionary](search-v1/packets/bc5239eeff4a513d94ab/256/dictionary.ltd) · [heldback sequences/results](heldback-expression/bc5239eeff4a513d94ab/result.json). IDs below are zero-based.

### #908: Smallest Range I

Fixed-source control:

```javascript
function smallestFlexibleRange(values, adjustment) {
  let minimumValue = values[0];
  let maximumValue = values[0];
  for (const value of values) {
    minimumValue = Math.min(minimumValue, value);
    maximumValue = Math.max(maximumValue, value);
  }
  return Math.max(0, maximumValue - minimumValue - adjustment * 2);
}
function solve(nums, k) {
  return smallestFlexibleRange(nums, k);
}
```

Canonical source, with all original behavior checks passing:

```javascript
function solve(values, other) {
  let minimum = values[0];
  let maximum = values[0];
  for (const value of values) {
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }
  return Math.max(0, maximum - minimum - other * 2);
}
```

Exact IDs: `[157, 45, 202, 36, 189, 195, 20, 240, 118, 52, 123, 70, 189, 193, 20, 240, 118, 52, 123, 77, 235, 25, 240, 37, 195, 20, 104, 47, 194, 31, 195, 45, 235, 33, 71, 193, 20, 104, 47, 192, 31, 193, 45, 235, 41, 255, 104, 47, 192, 31, 52, 45, 193, 15, 8, 195, 15, 8, 202, 8, 42, 8, 57, 33, 79]`. 65 selections / 520 selection bits, plus 328 framing bits and zero padding.

### #1018: Binary Prefix Divisible By 5

Fixed-source control:

```javascript
function prefixDivisibilityByFive(values) {
  const resultValues = [];
  let remainderValue = 0;
  for (const value of values) {
    remainderValue = ((remainderValue * 2 | value) % 5 + 5) % 5;
    resultValues.push(remainderValue === 0);
  }
  return resultValues;
}
function solve(nums) {
  return prefixDivisibilityByFive(nums);
}
```

Canonical source, with all original behavior checks passing:

```javascript
function solve(values) {
  const result = [];
  let value = 0;
  for (const value2 of values) {
    value = ((value * 2 | value2) % 5 + 5) % 5;
    result.push(value === 0);
  }
  return result;
}
```

Exact IDs: `[157, 40, 211, 20, 118, 123, 70, 189, 235, 21, 77, 236, 25, 240, 37, 235, 19, 11, 31, 235, 8, 42, 8, 57, 8, 250, 8, 236, 34, 28, 8, 62, 13, 62, 34, 28, 8, 62, 71, 211, 50, 235, 22, 52, 41, 255, 211, 79]`. 48 selections / 384 selection bits, plus 328 framing bits and zero padding.

Shared concrete strings between these examples include:

- ID 157: `"function solve(values"`
- ID 77: `";\n  for (const "`
- ID 255: `"}\n  return "`
- ID 37: `") {\n    "`
- ID 71: `";\n    "`
- ID 240: `"values"`
- ID 41: `");\n  "`
- ID 235: `"value"`

## Reproduction and next decision

[Reproduction instructions](REPRODUCE.md) use retained originals, the frozen split,
existing Node/Acorn/eslint-scope/escodegen and compatible Python. No corpus access,
new training or download is required to reproduce the published source experiments.
The installed system Python/old venv mismatch on 128 is avoided with the existing
cached 3.13.15 interpreter, as in pass3.

The next useful comparison would improve the fit-only candidate pruning/proposals
(the current winner still stores unused entries), and test a newly frozen
heldback development split. If #929 or `@` is added to fitting, it becomes exposed
training material; its current heldback result must remain unchanged. This report
does not perform that next experiment or deploy a new live dictionary.

The introducing publication commit pins this directory. Resolve it with
`git log -1 --format=%H -- projects/algorithm_solver/literals/clusters-v1`.
