# Per-binding exact-cost naming under lexical conflicts

Board item 13, goal2b. Name-search used a globally injective spelling map;
scope-choice used twelve whole-program alphabet/printing alternatives. This
stage optimizes individual lexical bindings against complete-source literal
selection costs, retaining a matched global-map comparator. It tests a specific
search weakness, not a new decoder or a learned naming model.

## Inputs and pre-freeze audit

Use cost-decomposition-v1's qualified R dev-fit 300/dev-val 100 allowlist and pinned
L-R 128/256 dictionaries. Validation is consumed development. Final held-out 100
and protected 66 stay closed. No corpus naming-cost search preceded this freeze.

Fit-only scope audit: 300 programs, 2,648 eligible bindings in 295 programs;
maximum 43 eligible bindings in one program; 9,671 conflict edges. Five programs
retain original under the reflection guard. No original-graph conflict occurred.
The audit measured eligibility/structure, not source-rewrite or dictionary gains.
Twelve synthetic checks pass, including 100 independently executed legal colorings.

## Capture constraints and exact source spans

The pinned ESLint scope analyzer resolves declarations and references; Acorn
provides exact identifier spans. Each binding is a vertex, including fixed
bindings. A name assignment is allowed only if:

- bindings of the same lexical scope have different names;
- for every resolved reference to binding u, u differs from all other bindings
  along the path from the reference's scope through u's defining scope;
- an eligible binding cannot take the spelling of an unresolved reference from
  its scope or a descendant scope;
- fixed bindings retain their original spelling.

These constraints prevent changing reference resolution when names change.
Bindings that do not conflict may reuse a name. Graph topology stays fixed under
identifier-only substitution. Fixed alias vertices (such as class inner/outer
names) may already share a name and are never edited; a conflict involving an
eligible original binding instead retains the entire source as unsupported.

Eligible bindings are local parameters, variable declarations and catch bindings
with complete exact Identifier spans. Global/module/class-scope bindings are fixed.
Function/class declaration names, variables initialized or assigned function/
arrow/class expressions (including default/destructuring assignments), shorthand
property bindings and shared/overlapping declaration spans stay fixed. Every
span must equal its binding's original spelling. No shorthand key expansion,
property renaming, layout printing, arithmetic or control-flow rewrite occurs.

The whole source retains original if it contains with, an eval/Function identifier,
or literal name/toString property access. Non-ASCII source is retained because
Acorn positions use UTF-16. This conservative policy does not claim universal
reflection equivalence; final qualification remains mandatory.

## Matched descent policies

Both policies use the same scope records and guards, full-source canonical
selection cost, original source, two coordinate sweeps and at most 6,000 exact
candidate evaluations per call. Order units by decreasing total span count,
then smallest vertex ID. For each unit, consider a–z substitutions and swaps
with each other eligible unit. Swaps may reuse an existing multicharacter name;
new substitutions are lowercase single letters. Every proposal must satisfy
all constraints. Select the strict selection-count improvement with minimum
source bytes, then lexical source text. Equal-cost changes are not accepted.
Retain the best complete incumbent on the trial cap. Report calls, trials,
accepted moves, stop reasons, eligibility and binding-spelling counts.

- `global`: a unit contains all bindings originally sharing a spelling. A group
  is editable only if all its members are eligible. Distinct groups remain
  injective, and targets exclude fixed or unresolved spellings globally. This
  is deliberately more restrictive than lexical conflicts, matching the global
  spelling-map mechanism; it is not claimed identical to name-search's old policy.
- `scope`: each eligible binding is its own unit, and only the lexical graph
  restricts sharing. No globally reserved letter set beyond graph constraints.

Unchanged source is always available. Pair swaps are checked against every
incident graph edge and unresolved-name restriction before scoring. No arbitrary
source edits, compiler compression or model calls occur in the search.

## Ten arms and dictionary protocol

At 128/seven bits and 256/eight bits: `control`, fixed-dictionary `global` and
`scope`, and dictionary-fitting `global_joint` and `scope_joint`.

All start from R and the same L-R dictionary. Two fit rounds: non-control arms
run their bounded naming policy on the currently selected source, retain the
original and previous alternatives, then choose minimum-cost sources. Joint arms
and control continue matched80-v3 exact refill/swap/pair dictionary search using
the style150-v2 chosen-source span proposer. Fixed arms keep L-R unchanged.

The dictionary search has 30,000 trials or 600 seconds per round, the pinned
minify-control neighborhood and refill shortlist 24. Proposals require two selected
owners and exclude complete sources/solve definitions/bodies in all fit variants.
All 96 fallback characters remain; canonical widths, dictionary format and decoder
are unchanged. Four search workers, then four sandbox workers, 4 GiB address-space
ceiling per process, 7,200-second global cap, PYTHONHASHSEED=0. Report every cap.
Local termination is not global optimality.

Seal private fit alternatives, chosen sources and dictionaries before opening
validation per arm. Validation performs two calls of the same bounded naming
policy under its sealed dictionary, never refits. Audit all fit and validation
alternatives for whole-source/body entries. Independently decode all final
packets. After every choice seals, qualify distinct changed source/ID pairs on
all original frozen cases and strict observation parity. Failures remain failed
choices, with no retry, repair or test-driven fallback. Unchanged source reuses
hash-bound qualification. Finite cases do not prove universal equivalence.

The global/scope contrast uses matched fixed dictionaries. The global_joint/
scope_joint contrast compares two complete source-plus-dictionary searches;
their proposal trajectories may diverge. Report each against searched control
and pinned R, and show the historical name-search result separately.

## Costs, predictions and readiness

Report both splits: source bytes, coverage/qualification, selections and actions
(total, median, p90, p95, worst, <=32/96), single-character fraction and absolute
character codes, paired changes, dictionary/packet/framing/padding, raw and
canonical-decoder-inclusive packages. One Finish per program. Scope/parser and
rewrite tooling bytes are offline encoder storage; complete installed runtime
footprints remain unmeasured. No hidden identifier declaration or lookup channel.

- D1: controls reproduce pinned fit and validation selections.
- D2: scope saves validation actions versus global at both widths and improves
  at least 20 validation programs at each width. Different coordinate paths mean
  non-worsening is not guaranteed by the larger feasible set.
- D3: scope_joint256 saves at least 5% validation actions versus control256, with
  at least 60 better and at most 25 worse programs.
- D4: scope_joint beats global_joint on validation actions at both widths.
- D5: all 4,000 final source choices independently decode and qualify, and
  whole-solution audits are clean. Unsupported policies remain in the denominator.
- D6: no arm meets every M1 cost indicator on consumed validation.

Non-control readiness is unchanged: 100/100 validation choices decode/qualify;
audits clean; at least 5% fewer total actions versus searched control; lower
median and p90 actions; at least 60 improve and at most 25 worsen; nonincreasing
single-character fraction; raw package bytes within 105%. Rank by total actions,
package bytes, width and arm name. Report every failed predicate. A passing
input candidate can only motivate separately frozen owner-approved confirmation.
No M1 threshold change or current qualification claim.

Twelve synthetic tests and compilation/import/help checks pass before launch.
Cross-review follows commit/push of freeze/code/contract, under PLAN's timeout
rule. No training, private-source publication, protected opening, BITS deployment,
human study or ledger/catalog/claim write. Component intent preserved; production
interfaces and canonical decoder unchanged.
