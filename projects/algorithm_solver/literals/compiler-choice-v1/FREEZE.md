# Compiler alternatives under literal selection costs

Board item 10, goal 2b. The minify-control stage disabled compression and
mangling; name-search changed bound identifiers. This stage tests a fixed small
family of ordinary compiler simplifications, followed by exact-string vocabulary
selection. It is offline source optimization supplied with known programs.
It does not measure autonomous assembly, unseen solving or a learned scorer.

## Population and compiler family

Use only cost-decomposition-v1's hash-bound qualified R dev-fit 300/dev-val 100
and L-R 128/256 dictionaries. The final held-out 100 and protected 66 stay closed.
Validation is consumed development. No corpus compiler run preceded this freeze.

The installed, hash-pinned Terser package generates three alternatives alongside
the original. The same frozen generator is applied to validation only after each
arm's dictionary seals. No per-problem options or result-driven rewrite repairs.

- `original`: unchanged R.
- `layout`: Terser printer, compression and mangling off.
- `syntax`: defaults off; booleans, conditionals, if-return simplification,
  declaration joining and sequences enabled, one pass.
- `standard`: default compression, two passes, with the conservative overrides
  below. This can remove dead code, simplify expressions, inline local functions
  and combine statements; it is not a layout-only transformation.

All profiles disable mangling. Compression profiles disable every `unsafe*`
option, pure-getter assumptions, pure-function lists, pure-new assumptions,
console/debugger dropping, top-level removal and module mode. They retain function
and class names, argument lists and Infinity spelling. Output is ECMAScript 2022,
ASCII escaped, semicolon-delimited, without comments. Code and options are pinned.

Any program with `with`, an `eval` or `Function` identifier, or a literal `.name`
or `.toString` property access retains only the original under a conservative
reflection guard. This also skips ordinary numeric/string toString calls; skips
stay in the denominator. Compiler/parse failure or output over twice the input
bytes removes only that generated candidate and records the failure. It never
removes the original. No exception or test result triggers a repair.

These options are a candidate-generation policy, not a proof of equivalence.
All final changed choices must independently pass every original frozen case
and strict observation parity, including the existing value/type and mutation
checks. Complete source and solve definitions/bodies are excluded from dictionaries.
No helper code, runtime table or source payload is external to the encoded source.

## Eight arms

At 128/seven bits and 256/eight bits:

- `control`: original R only; continue the exact local dictionary search from L-R.
- `bytes`: choose the candidate with minimum UTF-8 bytes (then profile name);
  keep the initial L-R dictionary fixed.
- `select`: choose minimum literal selections under the initial fixed L-R
  dictionary, then source bytes and profile name.
- `joint`: same candidate family, choose the exact lowest-cost source after
  every dictionary trial and continue dictionary search from L-R.

`select` versus `bytes` isolates source choice objective with a fixed dictionary.
`joint` versus `select` adds dictionary adaptation. `joint` versus searched
`control` is the full source-plus-dictionary comparison. Report pinned R baseline
separately, so control drift is visible. Bytes and selections can disagree.

Use the existing matched80-v3 exact-cost evaluator and refill/swap/pair search,
style150-v2's chosen-source span proposer, the pinned minify-control neighborhood
and refill shortlist 24. Proposals require two selected source owners and exclude
all complete sources and solve bodies in the candidate family. Mandatory 96
fallback characters remain. Width, framing and canonical decoder are unchanged.

Per searched arm: 60,000 trials or 900 seconds. Four search workers, then four
sandbox workers, address-space ceiling 4 GiB per process, global cap 5,400 seconds,
PYTHONHASHSEED=0. Retain stop reasons and bounded-search limitations. No learned
ranking or new model/provider dependency.

Seal private fit variants, selected fit sources and dictionaries before reading
validation. Generate validation candidates once under the fixed policy and choose
under the sealed dictionary; no refitting. Persist all candidates and failures
privately. Independently decode every final packet to its selected source hash.
After all choices are sealed, qualify distinct final changed source/ID pairs in
four sandbox workers. Failures remain failed choices and invalidate readiness;
there is no fallback selection after seeing tests. Unchanged sources reuse their
hash-bound qualification. Record candidate generation skips separately from
qualification failures. All 400 source choices remain in each arm's denominator.

## Costs and predictions

Report both splits: source bytes; selections/actions with median, p90, p95,
worst and <=32/96 counts; coverage and qualification; single-character fraction;
chosen profiles, skips/errors, paired better/same/worse; dictionary, packets,
41-byte headers, padding, raw packages and canonical decoder dependency bytes.
One Finish per program is included. Compiler and source-generator package bytes
are reported separately as offline encoder tooling, not charged to decoder input.
Complete installed Node/CPython/stdlib footprints remain unmeasured.

- C1: searched controls reproduce pinned fit and validation selection totals.
- C2: byte-minimizing choice reduces validation source bytes by at least 5% but
  saves fewer than 5% validation actions at both widths versus pinned R.
- C3: `select` never costs more actions than `bytes` on any validation program,
  and strictly improves at least 20 at each width.
- C4: `joint` saves at least 5% validation actions versus searched `control` at
  256 entries, with at least 60 better and at most 25 worse programs.
- C5: all 3,200 final choices independently decode and qualify; whole-solution
  audits are clean. Compilation failures/skips are retained separately.
- C6: no arm meets all M1 cost indicators on consumed validation.

An arm other than control is an input candidate only if all 100 validation
choices decode and qualify; audits are clean; total actions fall at least 5%
versus searched control; median and p90 actions are lower; at least 60 improve
and at most 25 worsen; single-character fraction does not increase; and raw
package bytes are within 105% of control. Rank by actions, full package bytes,
width and arm name. Report every predicate. This is readiness for a separately
proposed confirmation, not M1 qualification or storage/solving superiority.

Seven synthetic compiler checks and three source-choice checks pass before the
freeze; they cover getter side effects, short circuiting, negative zero/NaN,
arguments, closure/alias mutation, reflection retention and disagreement between
byte and input objectives. Python compilation/import passes. The unchanged
judge/lane infrastructure retains A's 37 checks. Cross-review precedes launch
under PLAN's review/timeout rule; all run code is committed and pushed first.

No training, source publication, protected opening, BITS deployment, human study,
ledger/catalog/claim write or threshold change. Component: algorithm_solver
literal research; intent preserved. Compiler alternatives stay private; production
interfaces and the canonical literal decoder are unchanged.
