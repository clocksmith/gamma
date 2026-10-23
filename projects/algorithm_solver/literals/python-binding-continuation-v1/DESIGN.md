# Python continuation: scope-local naming with matched dictionary fitting

Status: design and implementation rationale, 2026-10-23. [FREEZE.md](FREEZE.md)
is the prospective execution contract. No
corpus source, test payload, search proposal or cost was opened/measured for
this preparation. Existing baseline dictionaries were read only as opaque bytes
for hashing during contract preparation. Read-only review used public contracts/code/results. Root must review
the runner/contract and adapter, freeze exact identities and obtain team
cross-review before launch. No training or protected access is involved.

This is owner track T4. Transfer the best selected JS mechanism, item 13
scope_joint256, to Python under independently measured semantics and costs. JS
item 15's stacked dictionary improvement failed its median/breadth successor
gate; its dictionary is not a Python seed. Python and JS remain separate evidence.

## Exact existing population and starting artifacts

Reuse [python-name-v1/contract.json](../python-name-v1/contract.json) without
expanding its source list: 36 previously exposed qualified Python problems,
27 fit and 9 validation. Fit IDs: 6, 10, 11, 15, 18, 22, 28, 29, 34, 35, 40,
42, 51, 52, 54, 55, 58, 59, 62, 64, 66, 67, 69, 71, 78, 79, 84.
Validation IDs: 7, 8, 14, 20, 41, 44, 57, 63, 76. The other 14 historical
stage50 problems, final held-out 100 and protected 66 stay closed. Never call a
stage50 loader and filter after reading; load exact permitted file paths only.

Original source choice remains item 6's 34 canonical-compact and two inline-row-dp
sources, preserving its source, case, qualification and observation hashes.
Use item 6's separately fit Python baseline dictionaries at 128 and 256 entries,
private `python-name/run-v1/w7/baseline-dictionary.json` and
`python-name/run-v1/w8/baseline-dictionary.json`. Verify and pin their exact bytes
against the prior receipts before any source search; do not import JS or historical
50-problem dictionaries. Candidate reuse is disclosed adaptive development.

Historical [item 6](../python-name-v1/README.md) is unselected: 256 rename gave
937 versus 949 validation actions, joint 934 but a worse median and character
fraction. New arm rankings must not retrospectively promote it. Retain original,
rename and joint historical costs as references, separately from matched controls.

## Concrete reusable implementation

`graph.py` builds the record consumed by the existing pure Python
[binding-descent optimizer](../binding-descent-v1/rewrite.py): `variables` with
stable IDs, original spellings, exact source spans, eligibility, forbidden targets
and neighbor IDs, plus `unsafe/reason`. Reuse that module's `legal`, `render` and
`optimize`; never invoke its Node/JavaScript `records()` loader. The canonical
codec, exact source-cost DP and coordinate search are language-independent.

The draft adapter uses CPython `ast` and `symtable` for ASCII source. It changes
only function-local Name spans whose binding is neither captured nor externally
named. Parameters stay fixed, including the public Solution-method keyword
interface; module/class/import/namespace bindings stay fixed. Any spelling free,
nonlocal, global, imported or reserved anywhere stays unavailable globally. This
is conservative: it intentionally does not claim full Python closure allocation.
All eligible bindings in the same function scope conflict; distinct function
scopes may reuse a name. Capture is excluded by the global reservation of every
free/nonlocal spelling. Defaults are traversed in the defining scope. All annotation identifiers are
reserved and remain unchanged, preserving CPython 3.14 deferred annotation scopes;
function bodies use their matching symtable. Ambiguous AST/table matching
retains the entire source as unsupported.

Comprehensions, generator expressions and lambdas stay textually unchanged, with
all their identifier spellings reserved globally, including walrus targets. This
allows independent safe surrounding locals to change without pretending the
implicit scopes were modeled. JoinedStr/TemplateStr identifiers are also reserved
globally before optimization: debug labels and template interpolation expressions
make their original spellings observable. Normal fstrings use the same rule.
Any ast.Try/ast.TryStar makes the entire source unsupported, since caught
UnboundLocalError/NameError messages can expose local binding names. Unsupported
sources stay unchanged in every denominator; there is no test-driven retry.
Pattern captures, attribute and keyword-argument spellings remain reserved. Non-ASCII, reflection, decorators,
type parameters and keyword expansion retain original source. Reflection guards
extend the old explicit list to frame attributes and `__getattribute__`; they are
still not a proof against all observable Python introspection. Explicit source/stack
helpers, linecache reads and __file__ are guarded, including directly imported
helper aliases; inspect.getsource is exercised through real temporary module files.

Both new global and scope policies use **this same conservative eligibility**.
Do not compare unrestricted item 6 parameter edits with restricted scope edits
and label the result scope attribution. Full Python closures, comprehension
bindings and public parameter renaming require their own correctness argument;
unsupported portions remain visible in eligibility counts and denominators.

Render against original character offsets (ASCII gives byte equality), apply all
edits simultaneously, then reparse and rebuild the graph after each completed
optimization call. `validate_rewrite` requires unchanged structural AST after normalizing only the
recorded eligible identifiers by binding identity and verifies final consistent
spelling against the graph. Wire this check into every optimizer call before
launch. Parameter, attribute, literal, control-flow, function/class definition and
signature tokens must remain unchanged. Every changed selected program still
undergoes independent sandbox qualification; a syntax/graph audit cannot replace it.

## Matched arms and fixed budgets

At both 128/seven-bit and 256/eight-bit widths start every arm from the corresponding
item 6 baseline dictionary and original selected sources:

| Arm | Name search | Dictionary |
| --- | --- | --- |
| control | None | Two matched continuation rounds |
| global | Injective groups sharing original spelling | Fixed baseline |
| global_joint | Same global policy | Two alternating search rounds |
| scope | Individual eligible lexical bindings | Fixed baseline |
| scope_joint | Same scope policy | Two alternating search rounds |

All naming calls use two sweeps and at most 6,000 exact whole-source evaluations,
a-z substitutions and eligible-pair swaps, strict selection-count improvement,
then source-byte length and lexical text as ties. The original and every prior
variant remain selectable. No equal-cost exploration, multi-character palette,
compiler transformation, source padding or character-weighted objective.

Reuse `python-name-v1/run.py:polish` and its Python `bindings.forbidden(text,entry)`
body extraction, not the JS `solve` detector. Adopt matched item 13 dictionary
budgets: 30,000 exact trials or 600 seconds per round, shortlist 24 and the item 6
neighborhood (96 additions, 500 swaps, 16 pair-addition/eight removal shortlist,
150 paired moves). Pool spans come only from chosen fit source variants; require
two distinct owners. Retain all 96 fallback characters. Include current complete
source, Solution entry-method and body strings across **all retained variants**
in the exclusion set before every proposal and the final audit. Preserve the
incumbent if the budget expires; reuse the prune-at-cap fix rather than invoking
an additional evaluation after budget exhaustion.

Seal **all ten** dictionaries and fit source choices before loading any of the
nine validation source files. Validation gets two calls of the same naming policy
under the sealed dictionary, original and prior variants retained, no refit.
Finish every choice at both widths before reading cases for fresh qualification.
The comparison is source-plus-encoder optimization, not untouched-source compression.

## Qualification and exact costs

Reuse the original item 6 Python harness and qualification behavior, with a
strict loader that verifies each explicit case file and original-observation hash
at use. Expected values never enter the sandbox. Require the unchanged return/
mutation oracle **and exact serialized observation parity**, including result type,
argument mutation and alias edges. Deduplicate changed sources by ID/hash only
after all choices seal. Reuse qualification only for exact previously passed
source hashes with an identified receipt. Retain historical failures separately;
no retry, repair, source substitution or test-feedback selection is allowed.

At most four sandbox workers; 32-case batches, 3 CPU seconds, 8 wall seconds,
512 MiB and 4 MiB output per batch, unchanged from item 6. All selected packets
must independently decode to their sealed source hash. Every failure remains in
the 36-program denominator and blocks readiness. Finite cases remain evidence,
not arbitrary-input equivalence or a complexity proof.

Ten arms times 36 programs produce **360 final choices**. Report fit/validation
coverage and qualification, total/median/p90/p95/worst selections and actions,
<=32/96 counts, absolute single-character selections and fraction, source bytes,
paired better/same/worse, dictionary/payload/header/padding/package bytes, decoder
and offline-tool source inventories, search trials/moves/caps and elapsed time.
One Finish per program remains an action. Preserve all imports, helpers, class and
method interface in emitted bytes. Decoder-inclusive aggregate and per-program standalone packages include the full
13010bytes of literals.py plus pass2/working/bitpack.py, both required and hash-bound.
Installed CPython/stdlib footprint remains
unmeasured and is explicitly excluded rather than charged as zero.

## Predictions and development readiness to freeze

- P1: replayed original/baseline costs reproduce item 6's 1,420/949 validation
  actions at 128/256, before continuation; all source/artifact hashes agree.
- P2: scope beats global on fit selections in at least one width under the fixed
  shared dictionary; a negative result does not exclude excluded Python scopes.
- P3: scope_joint256 improves validation actions over global_joint256.
- P4: all 360 final choices decode and qualify with no body/whole-source entry.
- P5: no arm meets every unchanged M1 cost indicator on the nine validation IDs.

Use item 6's readiness gates independently at each width: all 36 qualify, all nine
validation programs decode, clean whole-source/body audits, at least 5% fewer
validation actions than the same-width original-source baseline, strictly lower
median/p90 actions, at least six improved and at most two worsened, nonincreasing
single-character fraction and package at most 105% of baseline. Also report every
predicate against matched searched `control`; a new scope candidate must pass both
baseline and searched-control readiness. To attribute a scope successor require
strictly fewer actions than its matched global arm, nonhigher median/p90/fraction,
at most two worsened, package at most 105%, complete qualification and clean audits.
Rank eligible scope candidates by validation actions, package, width, arm name.

The nine-program panel cannot qualify M1: 400/500 frozen problems, at most 256
entries, median at most 32/p95 at most 96 selections, at most 10% single-character
selection bits, zero whole-solution entries remain unchanged. No source population
expansion, confirmation, Python/JS pooling, publication, deployment or M2 claim.

## Runtime, proof gaps and next concrete integration

Two width-search workers on cores2/3, then four sandbox workers on cores2-5, with no overlap. Use the
existing pinned `/usr/bin/python3` runtime for AST/symtable and judge; verify the
recorded binary hash and version before launch. Python graph search needs no
SciPy, model, GPU, install or download. Bound each search process to one assigned
CPU within team cores 0-15, PYTHONHASHSEED=0, 4 GiB address space and 7,200-second
overall cap. The executable freeze assigns cores2/3 and2-5; root coordinates them with other
running jobs. Do not use old cores16-31.

The implementation now includes explicit-name backend imports, the Python body
ban, cap-preserving dictionary search, two-phase fit/validation runner, copied
strict observation qualification with case hashes, metadata-only contract writer,
outer process-group supervisor and independently decoding/reaggregating report.
There are28 focused synthetic checks, including a durable preflight-failure receipt, actual optimization/execution of
debug and normal fstrings, template-string expression metadata and caught binding
errors under Try/TryStar.
Root must still review, push the freeze/code/contract, obtain Claude review, then
launch. No corpus execution occurred during preparation.

Further item 14/15/16/24 transfers must be separately named, not implicit factors:
item 14 coupled substitutions need this Python graph first; item 15 LNS can reuse
language-neutral fixed-source `repair`, but needs Python body exclusions and a
recorded Python seed; item 16 minN/minC can audit these sealed dictionaries without
new source search, using matched policy on both controls; item 24 optional-character
search requires a Python-specific fit character set and full validation coverage,
with no free escape. These pure backends are reusable. JS-specific source loaders,
body detectors and dictionary/codebooks are not. Their effects must be measured
against the exact same Python seed, not inferred from JS results.
