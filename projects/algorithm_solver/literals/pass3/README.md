# Functional rewrites and AST-informed literal dictionaries

The bounded comparison covers all **20 known development problems**. Its new
61-string candidate uses **78 selections at six bits**; the matched fixed-source
AST control uses 63 strings and 81 selections. The gain comes from two checked
functional rewrites, not a general synthesis engine. The smallest package found
here uses **114 strings and 1,107 selections at seven bits: 2,726 bytes**. That
storage winner keeps the original normalized sources. There is no single winner
on storage and input length.

The live shared7 dictionary remains unchanged. No 1a/1b corpus admission or
protected/3b data was used. All findings describe offline encoding of supplied
correct source alternatives, not autonomous assembly from a problem description.

## Measured comparison

Every row reconstructs 20/20 complete sources. Dictionary bytes include the LTD1
header and every string length and UTF-8 byte. Total bytes also include all LTV1
packets: 41 framing bytes per program (820 total), selections and byte padding.
Whole-program entries remain a charged diagnostic, not the shared result.

| Candidate | Strings | Bits/selection | Selections | Dictionary bytes | Selection bits | Padding bits | Total package bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
| [fixed-AST-and-three-line-spans](search-v2/encodings/88f44886736869fff1ea.json) | 63 | 6 | 81 | 3941 | 486 | 66 | 4830 |
| [joint-AST-and-three-line-spans](search-v2/encodings/236bf9fe4d999fd0d3f3.json) | 61 | 6 | 78 | 3932 | 468 | 68 | 4819 |
| [fixed-lexical-merges-32](search-v2/encodings/590d21bed4973485c93e.json) | 114 | 7 | 1107 | 929 | 7749 | 67 | 2726 |
| [joint-lexical-merges-64](search-v2/encodings/cac9e07c20f72f7c5b21.json) | 126 | 7 | 1004 | 1152 | 7028 | 60 | 2858 |
| [fixed-lexical-merges-64](search-v2/encodings/88fc9836908e938fc740.json) | 140 | 8 | 843 | 1258 | 6744 | 0 | 2921 |
| [joint-whole-program-diagnostic](search-v2/encodings/ccbcb429577d3521d941.json) | 20 | 5 | 20 | 4200 | 100 | 60 | 5040 |

The [machine comparison](comparison.json) reports each candidate at **all matched
budgets 16, 32, 64, 128 and 256**, including infeasible points. No complete shared
candidate was found at 16 or 32 in this search; this is not an impossibility result.
The 20-entry whole-program diagnostic fits at 32 with no cross-problem reuse.

Historical comparisons are preserved: [shared7](../pass2/working/packages/shared7/manifest.json)
has 79 strings, 154 selections, 3,507 dictionary bytes and 4,468 total bytes;
[baseline8](../pass2/working/packages/baseline8/manifest.json) has 140 strings,
843 selections and 2,921 total bytes. The new 114-string option saves 195 bytes
but requires 264 more selections. The previously published
[59-string span candidate](https://github.com/clocksmith/gamma/blob/743ec6870e9960f390aad9edb54d1097d9dcb9d7/projects/algorithm_solver/literals/budgets/compact-v1/budget-64/manifest.json)
uses 74 selections and 5,009 total bytes: it still takes four fewer selections
than the new 61-string candidate, which saves 190 package bytes.

## What actually ran

[generate.cjs](generate.cjs) uses installed Acorn to recognize bounded AST patterns
in the hash-pinned normalized/shared sources. It generates frequency-loop folds,
Set membership folds, ASCII case conversion/map and vowel-filter alternatives,
and guarded block/expression arrow entrypoints. Unsupported contexts remain
explicit in the [97-attempt lineage](generated/manifest.json). There are 84 unique
(problem, source hash) variants; originals and all alternatives are retained.
These are specific rewrites, not a general equivalence prover.

AST nodes and one-to-three-line spans propose **flat exact strings**. There are
no holes, parameter substitutions, helper injections, graph expansions or free
renamings. Characters, lexical pair merges, line/AST fragments and charged whole
programs are comparison arms. Exact shortest-path segmentation selects the
fewest dictionary entries for each complete source alternative, breaking ties
by source bytes then variant name. The search evaluates fixed and joint pools,
then bounded deletion trials with full resegmentation. It retains non-dominated
cardinality/storage/selection tradeoffs rather than one hidden weighted score.

[search-v1](search-v1/summary.json) retains 46 preliminary trials. Its fragment
admission missed a unique anonymous-arrow entrypoint case; it is superseded for
shared-fragment conclusions. [search-v2](search-v2/summary.json) tightens that
check, adds the matched fixed-source AST control, saves candidate pools, and
retains unused pool entries during deletion. It evaluates 55 trials. **101 total
trials** stay below the 120 ceiling; both stop at the end of the enumerated
schedule (1.26 and 2.71 seconds), not at an optimum. Each sweep had a 180-second
limit, one CPU thread, 8 GiB address-space cap and a 512 MiB artifact budget.

Non-diagnostic entries exclude whole programs. Unique fragments have at most
two nonempty lines and 160 UTF-8 bytes, with entrypoint-body guards; larger
fragments need at least two problem owners. These admission rules are disclosed
heuristics, not proof of strong compositionality. The 61-string candidate has
only four cross-problem entries, accounting for 21/78 selections. The storage
candidate has 82 shared entries and 1,065/1,107 shared selections.

## Correctness, costs and limits

[Qualification](qualification-v1/report.json): **84/84 source variants,
16,258/16,258 check executions**, with zero observed input mutations. These repeat
the same existing 3,834 reference cases across source variants; they are not
16,258 distinct new cases. Expected answers remain outside the Linux sandbox.
Each source is reconstructed through the existing packet codec before isolated
Node execution, with strict output framing, bounded CPU/time/memory/output, and
input-preservation checks. Tests support these input domains, not formal
semantic equivalence over all JavaScript values.

Functional folds use ordinary dense arrays or strings and unmodified built-ins;
counts must remain within safe integer bounds. Array.from can add O(n) temporary
memory. Case conversion is ASCII-specific. Arrow rewrites change declaration,
hoisting and function identity semantics; the declared harness invokes solve
after definition and does not construct it or inspect identity. The generator
rejects sensitive this/arguments/recursive entrypoint uses.

[Packet audit](audit.json) checks all 5,548 saved packets across 283 dictionary/
budget sets, exact source identities, dictionary bytes, widths, padding, and
package totals. It reuses native execution evidence only after byte equality;
it does not claim a second execution run. Seven rewrite assertions and five
fragment-admission assertions passed. Required judge/lane acceptance passed
37 tests before the experiments (8.86 seconds).

Package costs exclude human-readable duplicate JSON, raw observations, this
report and the common decoder implementation; they do not exclude emitted
program helpers or wrappers. The [artifact inventory](artifact-inventory.json)
separately charges retained research files and records common codec source sizes.
The dictionary is separately versioned; nothing here promotes or replaces the
live language.

## Reproduce

Use an existing compatible Python environment and installed Node/Acorn. On 128,
the system Python changed to 3.14 while the existing venv packages are 3.13;
the run used the already cached Python 3.13.15 interpreter with those packages.
No installation or environment repair was performed. From the Gamma checkout:

```bash
P=/home/x/.local/share/uv/python/cpython-3.13.15-linux-x86_64-gnu/bin/python3.13
L=projects/algorithm_solver/literals
RUN=/tmp/gamma-pass3-reproduction
mkdir "$RUN"
node "$L/pass3/test-rewrites.cjs"
PYTHONDONTWRITEBYTECODE=1 "$P" "$L/pass3/test-search.py"
node "$L/pass3/generate.cjs" "$L" "$RUN/generated"
PYTHONDONTWRITEBYTECODE=1 taskset -c 14 "$P" "$L/pass3/verify.py" --pilot "$L" --generated "$RUN/generated" --output "$RUN/qualification-v1"
PYTHONDONTWRITEBYTECODE=1 timeout 210s taskset -c 14 prlimit --as=8589934592 --cpu=200 "$P" "$L/pass3/search.py" --pilot "$L" --generated "$RUN/generated" --qualification "$RUN/qualification-v1/report.json" --output "$RUN/search-v2" --max-trials 74 --max-seconds 180
PYTHONDONTWRITEBYTECODE=1 "$P" "$L/pass3/audit.py" --pilot "$L" --output "$RUN/stored-audit.json"
```

The final command audits the committed packets; the fresh v2 output has the same
finite schedule but different elapsed times. Generate v1 separately with
search-initial.py if reproducing historical preliminary results. Source hashes,
pool hashes and packets are the reproducibility identities, not wall-clock times.

## Complete before/after examples

The two functional sources selected by the 61-string candidate follow. Every
shown character, including indentation and wrappers, is in the dictionary;
sequences are zero-based IDs. No editor finish/undo controls are included in this
offline packet benchmark. LTV1 framing is separate from a future UI protocol.

### 0242: Valid Anagram

Before:

```javascript
function solve(values, other) {
    const counts = new Map();
    for (const value of values) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
    for (const value of other) {
      counts.set(value, (counts.get(value) || 0) - 1);
    }
    return [...counts.values()].every(value => value === 0);
  }

```

After (264/264 checks, zero input mutations):

```javascript
function solve(values, other) {
    const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
    for (const value of other) {
      counts.set(value, (counts.get(value) || 0) - 1);
    }
    return [...counts.values()].every(value => value === 0);
  }

```

IDs `[59, 15, 6, 42]`: 4 selections / 24 bits, plus 328 framing bits and 0 padding bits. Exact pieces in order:

- `59` = `"function solve(values, other) {\n"`
- `15` = `"    const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());\n    for (const value of other) {\n"`
- `6` = `"      counts.set(value, (counts.get(value) || 0) - 1);\n    }\n"`
- `42` = `"    return [...counts.values()].every(value => value === 0);\n  }\n"`

### 0771: Jewels and Stones

Before:

```javascript
function solve(values, other) {
    const counts = new Set(values);
    let result = 0;
    for (const value of other) {
      if (counts.has(value)) result++;
    }
    return result;
  }

```

After (190/190 checks, zero input mutations):

```javascript
function solve(values, other) {
    const counts = new Set(values);
    return Array.from(other).reduce((result, value) => result + counts.has(value), 0);
  }

```

IDs `[59, 17, 40]`: 3 selections / 18 bits, plus 328 framing bits and 6 padding bits. Exact pieces in order:

- `59` = `"function solve(values, other) {\n"`
- `17` = `"    const counts = new Set(values);\n"`
- `40` = `"    return Array.from(other).reduce((result, value) => result + counts.has(value), 0);\n  }\n"`

The publication commit containing this directory is its immutable version.
Use `git log -1 --format=%H -- projects/algorithm_solver/literals/pass3` to resolve it.
