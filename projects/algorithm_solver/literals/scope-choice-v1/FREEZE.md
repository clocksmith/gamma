# Scope-local naming alternatives with matched printer controls

Board item 12 (codex), goal 2b. Item4's global injective spelling map cannot
reuse names across disjoint lexical bindings. This experiment uses the installed
compiler's scope resolver to expose that possibility, with a fixed small name
family and exact literal costs. It does not introduce a learned scorer or train
a model. Offline source transformation is supplied with a known program.

## Population and candidate family

Only cost-decomposition-v1's hash-bound R dev-fit 300/dev-val 100, preserving
its split and initial L-R 128/256 dictionaries. Final held-out 100 and protected
66 remain closed. Validation is consumed development. No corpus scope-mangling
or dictionary measurement preceded this freeze.

Each source gets up to twelve candidates:

1. Unchanged `original`.
2. `layout`: the Terser printer, compression and mangling disabled.
3. `default`: Terser's normal scope-aware local mangling, compression disabled.
4. Nine fixed-order scope manglers: lowercase alphabet rotations starting at
   offsets 0, 4, 8, 13, 17, 18, 19 and 23, plus reverse alphabetical order.
   Enumerate each alphabet bijectively as single letters, then two letters, etc.
   The compiler skips reserved/capturing names. No frequency adaptation or
   dictionary-dependent generator parameters in these nine profiles.

Every generated profile uses the same printer (ECMAScript 2022, ASCII escaping,
semicolons, comments removed). Mangling keeps top-level names, function/class
names and `solve`, leaves property mangling off, module mode off and eval mangling
off. Compression is entirely off: no arithmetic/branch/dead-code transformations.
The installed compiler guards enclosing referenced bindings when choosing a name;
sibling scopes may reuse it. Global variables and public property spellings stay
under the compiler's normal local-mangling semantics.

The conservative reflection guard from compiler-choice remains: `with`, an eval
or Function identifier, or literal name/toString property access keeps only the
original. If original-source scope analysis fails, retain original only, record
the failure and mark reuse diagnostics unavailable. Skips stay in every denominator. Parse/compiler failures or output more
than twice the original bytes drop only that generated candidate and are recorded;
original is always retained. No per-problem manual intervention or test-driven
repair. Measure binding counts and distinct binding spellings per candidate via
the independently installed ESLint scope analyzer; these are reuse diagnostics,
not semantic proof. Parser/compiler/scope packages and generator code are pinned.

## Eight arms and attribution

At 128/seven bits and 256/eight bits:

- `control`: original and layout compete under a continued dictionary search.
  This is a matched printer control, not strictly original source only.
- `default`: original, layout and default mangler compete under fixed initial L-R.
- `select`: all twelve candidates compete under fixed initial L-R.
- `joint`: all twelve compete after each dictionary trial, starting from L-R.

Source choice minimizes exact selections, then source bytes, then profile name.
`select` versus `default` isolates availability of the fixed alphabet family under
one dictionary. Its non-worsening is by construction, not an empirical discovery.
`joint` versus `select` adds dictionary fitting. `joint` versus `control` compares
the whole naming-plus-dictionary method against a searched printer-only control.
Also report pinned R costs and prior name-search joint results as historical
comparisons, explicitly identifying their different source policies/searches.

Use existing matched80-v3 exact evaluation/refill/swaps/pairs and style150-v2's
chosen-source span proposals, the pinned minify-control neighborhood and refill
shortlist 24. Proposals require two selected owners; exclude all complete sources
and solve definitions/bodies in the candidate family. All 96 fallback characters
remain mandatory. Exact canonical decoder, fixed widths and framing are unchanged.

Per searched arm: 60,000 trials or 900 seconds, retain the incumbent and stop
reason. Four search workers, then four sandbox workers; 4 GiB address space per
process, 5,400-second global cap, PYTHONHASHSEED=0. No global-optimality claim.

Seal fit variants, selected fit sources and dictionaries before opening validation
for each arm. Validation applies exactly the frozen twelve-profile generator and
sealed dictionary; no refitting. After all choices seal, independently decode and
qualify distinct final changed source/ID pairs against all original frozen cases
and strict observation parity, including existing value/type and mutation checks.
No retry or fallback after seeing a qualification failure; failures remain in the
denominator and invalidate readiness. Unchanged R reuses hash-bound qualification.
Finite parity checks are evidence, not universal equivalence or unseen solving.

## Costs and predictions

Report fit/validation source bytes, source choices and binding-name reuse;
coverage/qualification, selections/actions with median/p90/p95/worst and <=32/96
counts, single-character fraction, paired changes, dictionary and packet bytes,
41-byte headers, payload/padding, raw and decoder-inclusive packages. One Finish
is included per program. Compiler/generator/scope tooling bytes are offline encoder
storage, reported separately; complete installed runtimes remain unmeasured.
All helpers and emitted source text are encoded. No side-channel identifier table.

- S1: searched printer controls stay within 1% of pinned R validation actions at
  both widths.
- S2: `select` never worsens validation actions versus `default` (consistency
  check), and strictly improves at least 20 programs at each width (empirical).
- S3: `joint` saves at least 5% validation actions versus its searched control at
  256 entries, with at least 60 better and at most 25 worse programs.
- S4: all 3,200 final source choices independently decode and qualify, and
  whole-solution audits are clean. Compiler skips/failures remain explicit.
- S5: the chosen joint256 sources use fewer distinct bound-name spellings in
  total than the chosen control256 sources, with equal total binding count.
- S6: no arm meets all M1 cost indicators on consumed validation.

An arm other than control is an input candidate only if all 100 validation choices
decode and qualify, audits are clean, actions are at least 5% lower than searched
control, median and p90 actions are lower, at least 60 improve, at most 25 worsen,
single-character fraction does not increase and raw package bytes are within 105%.
Rank by actions, package bytes, width and arm name. This is readiness for separately
proposed confirmation, not qualification or permission to open a protected set.
No M1 threshold changes.

Nine synthetic mangling/closure/capture/shorthand/arguments/eval/name-enumerator
checks and three source-control/metadata/retention tests pass. Python compilation
and import pass; unchanged judge/lane infrastructure retains A's 37 checks.
Commit/push code/contract/freeze and obtain Claude's cross-review before launch
(or record PLAN's 30-minute timeout without a reply).

No training, private-source publication, held-out opening, BITS deployment,
human study or ledger/catalog/claim writes. Component: algorithm_solver literal
research; intent preserved. Canonical decoder and production boundaries unchanged.
