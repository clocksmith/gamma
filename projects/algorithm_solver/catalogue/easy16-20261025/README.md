# Sixteen Easy problems: Python and JavaScript

New paired implementations for sixteen unresolved known-problem paths, authored
for the explicit October 25 request. This is development material, not a new
benchmark population or a promotion of historical receipts.

## Selection and provenance

All sixteen keys occur as `missing_independent_tests` in the retained
[`remaining-causes.json`](../../findings/known-public-order-1a-128-v1/corrected-v2/remaining-causes.json)
at Gamma `7290ac480db36698b4c69e677f4f51172dd738bd` (blob
`e3c5ff32425622b8fb2d24af888625d04f0b8d27`). “Unsolved” here means no newly
successful qualified path in that report, not that nobody has published a
reference solution. These are new implementations, not imported reference code.

Difficulty and problem definitions follow the same Doocs revision used by Gamma's
4,081-ID inventory: `88c8c2c29f19c186d7cc05c9db17245d9ae3df43`.
`assignment.public-safe.json` supplies concise paraphrased contracts and exact
upstream file identities; upstream statements/solution bodies are not copied.
Descriptions/examples were consulted; this is not a blind or unseen-solving claim.

No private corpus cases or reserved payloads were opened. The frozen 500-problem
experiment, protected exclusions, qualification ledger, and original full-universe
status are unchanged. The broader private reservation/claim metadata is unavailable
here; these sources must not be automatically admitted to a research population.
The new development tests are public, authored by the same contributor, and do
not replace independent judge review or establish LeetCode submission acceptance.

## Consistent interface

Each numeric `.py` / `.js` file defines `solve` with ordered positional arguments.
Both languages use the same algorithm and preserve inputs. Mutable results are
fresh; order, ties, booleans and integer values agree. Every solution includes all
helpers it requires. JavaScript files are standalone source functions, not package
modules; the existing source-loader style can evaluate their `solve` declaration.
Python uses standard language features only. JavaScript needs no packages.
Inputs outside each stated domain have no additional promised behavior.

| ID | Problem | Arguments | Time |
|---|---|---|---|
| 3894 | Traffic Signal Color | `timer: integer` | O(1) |
| 3898 | Find the Degree of Each Vertex | `matrix: integer[][]` | O(n^2) |
| 3903 | Smallest Stable Index I | `nums: integer[], k: integer` | O(n) |
| 3908 | Valid Digit Number | `n: integer, x: integer` | O(d) |
| 3912 | Valid Elements in an Array | `nums: integer[]` | O(n) |
| 3917 | Count Indices With Opposite Parity | `nums: integer[]` | O(n) |
| 3921 | Score Validator | `events: string[]` | O(n) |
| 3925 | Concatenate Array With Reverse | `nums: integer[]` | O(n) |
| 3931 | Check Adjacent Digit Differences | `s: string` | O(n) |
| 3936 | Minimum Swaps to Move Zeros to End | `nums: integer[]` | O(n) |
| 4000 | Largest Integer With Given Digit Sum | `n: integer, s: integer` | O(n) |
| 4006 | Count Valid Prefixes | `s: string` | O(n) |
| 4010 | Maximize Pair Strength Using GCD | `nums: integer[]` | O(n^2 log M) |
| 4020 | Elevator Requests I | `n: integer, requests: integer[]` | O(m) |
| 4024 | Nearest Available Drone | `drones: integer[][3], target: integer[2]` | O(n) |
| 4030 | Check ASCII Palindromic | `s: string` | O(n) |

## Run the focused checks

From the Gamma root, with Python 3.10+ and Node available:

```sh
python3 projects/algorithm_solver/catalogue/easy16-20261025/test_solutions.py
```

`NODE_BIN` may select the Node executable. A missing runtime fails rather than
silently skipping a language. The parent builds deterministic public/development
cases and reference answers. Each language subprocess receives inputs only and
returns results, mutation observations and alias observations; expected answers
stay in the parent. These runners execute this batch's reviewed source, not
arbitrary untrusted code, and are not a security sandbox. A process deadline
bounds a hung run. Repeated calls also exercise reuse of the loaded functions.

Checks cover full small domains, deterministic randomized cases, boundaries,
strict comparisons, ties, duplicate values, stop-after-ten semantics, leading
zero bits, input preservation, output ownership and cross-language parity.
Problem 4000's complete stated n/s domain is checked by enumerating integers;
4010 includes a result above 2^32 and its maximum input length.
Finite tests do not establish universal correctness or complexity bounds.

The manifest uses the existing authoring artifact interface. From
`projects/algorithm_solver/`:

```sh
python3 -m algsolve.authoring_variants catalogue/easy16-20261025/manifest.json --output /tmp/easy16-variants.json
```

This creates authoring variants with unknown qualification, not admission.
`manifest.json` pins the sources, per-problem semantics and public assignment.
`development-results.json` records the executed development check separately.
Historical counts and claims remain untouched.

Component: `gamma.projects.algorithm_solver.catalogue`. Intent preserved.
Boundary effects: adds explicit authored examples and tests; no runtime, model,
protected-data, qualification-policy or serving-authority changes.
