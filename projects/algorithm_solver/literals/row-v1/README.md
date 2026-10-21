# Shared rolling-row dynamic programming

Five existing development problems now have tested implementations using one
generic rolling-row helper: #62 Unique Paths, #63 Unique Paths II, #64 Minimum
Path Sum, #72 Edit Distance and #97 Interleaving String. The helper supplies the
previous row, current left value and previous diagonal to an explicit transition
callback. Boundary and transition callbacks remain complete counted source.

[Contract](evidence/contract-summary.json) · [Source verdicts](evidence/sources.json) ·
[Independent audit and per-problem costs](evidence/audit.json) ·
[Search contract](evidence/search-contract.json) · [Exact selected helper](helper-scope.js)

## Matched result

The same 100-problem pool includes the previous heap refactor. No new problems,
protected cases, corpus admissions or query-time model work were introduced.

| Metric | Heap baseline, 8-bit | Joint row candidate, 8-bit |
|---|---:|---:|
| Entries | 256 | 256 |
| Selections | 7,085 | **7,016** |
| Payload bits | 56,680 | 56,128 |
| Median / p95 | 62 / 152 | **60 / 152** |
| Worst program | 230 | 230 |
| Character selection bits | 52.59% | **53.38%** |
| Dictionary | 2,612 B | 2,832 B |
| Complete package | **13,797 B** | 13,948 B |

This saves 69 selections (0.97%) but costs 151 additional package bytes (1.09%).
It is an input-cost candidate, **not** a storage improvement or M1 completion.
Absolute character selections also increase, 3,726 → 3,745; the helper alone
does not fix callback/binding fragmentation.

At seven bits, 128 entries improve 11,997 → 11,746 selections, median 113 → 105.5,
and 15,990 → 15,989 package bytes. p95 remains 256; character fraction changes
77.95% → 78.01%. Every header, name, callback and helper remains counted.

| Problem | Baseline 8-bit selections | Joint 8-bit selections |
|---|---:|---:|
| 62, unique paths | 61 | 61 (old source retained) |
| 63, obstacle paths | 65 | 55 |
| 64, minimum path sum | 56 | 54 |
| 72, edit distance | 89 | 55 |
| 97, interleaving | 116 | 93 |

The helper is actually selected by four eight-bit programs and five seven-bit
programs. Source-only changes under the old dictionaries save **nothing**.
Dictionary-only changes without the new sources save no eight-bit selections and
add six seven-bit selections. The gain requires the source and dictionary together.
This ablation is retained alongside both successful and rejected search moves.

## Contract and verification

The helper is an ordinary JavaScript function, not a source-template macro.
It takes dimensions, a boundary callback and a transition callback; returns the
bottom-right scalar; owns fresh row storage; and does not mutate inputs. Runtime
arguments are allowed, but their complete source must be encoded. The decoder
still concatenates exact strings and performs no substitutions.

Its recurrence uses O(rows × columns + rows + columns) work and O(columns + 1)
storage. These are inspected complexity bounds, not new maximum-input timing or
memory measurements. Number/BigInt behavior is preserved for #62; Boolean results
are required for #97. The original short length rejection remains in #97.

- **198/198** helper checks against an independent full-matrix implementation,
  including zero dimensions, Number/BigInt/Boolean values and a wrong-diagonal
  counterexample.
- **6/6** result-transport checks reject object spoofing of BigInt, rounded Number
  results, mutation and Boolean/Number confusion.
- **2,132/2,132** native checks across 20 original/new source versions on **533**
  distinct development cases. Three binomial-oracle cases extend #62's numerical
  checks. Other cases reuse existing tests; these counts are not new problems.
- **800** independently decoded packets, source-receipt joins and independent
  forward shortest-segmentation checks across baseline, source-only,
  dictionary-only and joint arms. Two accepted dictionary moves replay correctly.

Search took 16.44 seconds on 128; native qualification took 5.74 seconds. These
are offline experiment costs, not description-to-solution latency. Source
rewriting was authored offline; no autonomous composition is demonstrated.

## Reproduce and artifacts

Tooling lives here; private source proposals, tests, outputs, failed trials and
encoded packages remain at the hash-bound private path in the audit. Public
evidence contains IDs, hashes, costs and verdicts, with no private solution strings
or answer data. Existing experiments are unchanged.

On the same Linux checkout, use a fresh output path:
1. Run node test-row.cjs and python test-verifier.py with the existing native
   judge environment.
2. Run prepare.py with --prior-run, --proposal and a fresh --output directory;
   then run node generate.cjs with that output path.
3. Run verify.py --run with the fresh path. It executes the frozen sources in the
   existing Linux sandbox, with expected values kept host-side.
4. Run node pool.cjs with the fresh path, then measure.py --run with that path.
5. Run audit.py --run with that path and --publish with a fresh evidence directory.

The private run's sibling literal-heap-v1 directory supplies the frozen baseline
dictionaries. Source code and experiment identities must match the recorded
contracts; a new candidate requires a new run, not overwriting this one.

Next: reduce binding/callback fragmentation and improve candidate ranking using
actual re-encoding gains. Retain this input/storage tradeoff as a measured
baseline. M1 still requires 400/500, median ≤32, p95 ≤96 and ≤10% character bits.
