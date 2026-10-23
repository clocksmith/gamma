# Python scope naming continuation v1

Prospective run freeze for owner track T4. It takes effect only with the reviewed
code/contract commit pushed before launch. No corpus search or cost probe preceded
this document. [DESIGN.md](DESIGN.md) explains the implementation and proof limits;
this file fixes the execution protocol. No original frozen experiment is edited.

## Population and isolation

Exactly python-name-v1's 36 allowed Python problems: 27 fit, nine consumed
validation, same selected original sources, cases, observation and qualification
hashes. Load explicit contract paths only. Other14 stage50 problems and final100/
protected66 remain closed. Keep Python independent of JS and the500-problem M1.
Use item6's fit-only baseline dictionaries at128/256, hashed before launch. All
private payload stays private; report hashes/counts only. Original qualification
reuse is bound to source hash and item6's passing receipt.

## Arms, source policy and fitting

At each width run control, global, global_joint, scope, scope_joint. All start
from the same original sources and baseline dictionary. Control has fixed source
and two dictionary continuation rounds. Global/scope have two naming calls with
fixed dictionary; joint arms alternate naming and dictionary fitting twice.

Use graph.py's conservative CPython AST/symtable adapter and the pinned pure
binding-descent-v1 optimize/legal/render backend. Only eligible function-local
Name spans change. Parameters, module/class/import/namespace bindings and all
captured/global/nonlocal spellings stay fixed; those names and attributes,
keyword arguments, pattern targets, annotations, comprehension/lambda and
JoinedStr/TemplateStr names and Python keywords are globally unavailable as new targets. Each function's
eligible locals form a conflict clique. Separate functions may reuse colors.
Global groups all bindings with the same original spelling and retains an
injective mapping; scope edits individual bindings. Both use identical eligibility.

Any ast.Try or ast.TryStar retains the entire source as unsupported: caught
UnboundLocalError/NameError text can expose renamed binding spellings. Formatted
and template strings reserve all contained names before optimization, including
debug-fstring labels and template interpolation expression text. Normal fstrings
use the same conservative rule. These unsupported choices remain in all
denominators; no fallback repair or corpus-based exception is introduced.
Non-ASCII, reflection, decorators, type parameters, keyword expansion and ambiguous
AST/symtable mapping also retain original source with a reason. Source/stack
reflection helpers (including inspect.getsource/getsourcelines/findsource, frame
and traceback extraction, linecache reads and __file__) are guarded as names,
attributes and direct imported names even when locally aliased. This conservative
list is not a proof against arbitrarily concealed reflection. No complete closure or
comprehension renaming claim. Every call has two sweeps/6000 exact evaluations,
a-z proposals and eligible-pair swaps, strict whole-source selection improvement,
source bytes/text ties. graph.validate_rewrite checks exact structural AST except
owned Name spans, consistent colors, all graph constraints and compilation after
every call. It does not establish universal semantic equivalence.

Retain original and all prior fit variants. Ordinary dictionary search uses
30000 exact trials/600 seconds each round, 24-refill shortlist,96addition/500swap/
150pair limits with16pair-addition/eight-removal shortlist and designed_fraction
0.25 with no supplied designed entries. Require two selected fit owners. All96
fallback characters remain. A cap skips final pruning, preserving the evaluated
incumbent without exceeding the trial limit. Python original source, complete
Solution entry-method and body strings from every retained fit variant are banned
from proposals. Audit the final dictionary against all fit/validation variants;
any illegal entry blocks readiness without repair.

All ten dictionaries and chosen fit sources seal before ANY validation source
loads. Validation does two same-policy naming calls under each sealed dictionary,
no dictionary fitting. Source costs strictly improve per call, so original and
prior validation variants remain represented by the incumbent. All choices seal
before loading independent cases. The baseline is independently reconstructed
from pinned original source and dictionary after choices seal. This is adaptive
development source-plus-encoder optimization, not fresh confirmation.

## Qualification and artifacts

Decode every final packet independently and persist packets privately. Deduplicate
new selected sources by ID/hash after choice sealing; run every original case
with item6's preserved Python harness, same return/mutation oracle and exact JSON
observation parity including type/mutation/alias edges. Tests and original stdout
hashes are reverified at use; expected outputs remain outside the sandbox. Original
source reuses its exact-hash passing receipt. Failed assertions, killed processes,
timeouts, missing evidence and mismatches remain failures. No retry, repair,
test-driven fallback or dropping IDs. Strict finite development qualification
is not a proof for all inputs or arbitrary introspection.

Four sandbox workers,32-case batches,3 CPU seconds/8 wall seconds/512MiB/4MiBoutput
per batch. Ten arms produce360 final choices. Preserve full private fit/validation
traces, choices, packets, qualification stdout/stderr and all immutable seals.
Report coverage and qualification separately from potentially invalid costs.

Costs include complete emitted Python source (imports/helpers/interface), literal
dictionary,7/8-bit selections,41-byte headers,padding and one Finish per program.
Report selection/action total,median,p90,p95,worst,<=32/96, absolute character
codes/fraction, paired changes, source bytes, raw/decoder-inclusive package,
source-tool inventory, trial/move/cap counts and measured elapsed time. Decoder
source inventory is exactly literals.py plus pass2/working/bitpack.py (13010bytes),
with required existence and hashes. Aggregate packages charge both files once;
per-program standalone packages charge the entire dictionary, packet and both
decoder files. No missing dependency silently contributes zero. Installed
CPython/stdlib footprint is unmeasured, never silently zero. Reporting is separately
rerunnable and does not invoke fitting or qualification.

## Predictions and pass rules

P1: exact baseline replay yields item6 validation actions1420/949 at128/256.
P2: scope beats global fit selections in at least one fixed-dictionary width.
P3: scope_joint256 beats global_joint256 validation actions.
P4: all360 choices decode/qualify with clean whole-source/body audit.
P5: no arm meets every M1 cost indicator even on the nine validation IDs.

Readiness requires all36 qualified and all9 validation decoded, clean audits,
>=5% fewer validation actions, strictly lower median and p90 actions,>=6 better,
<=2 worse, nonincreasing single-character fraction and raw package<=105%.
Evaluate against both same-width pinned baseline and searched control. To select
a scope candidate additionally require strictly fewer actions than its matched
global arm, nonhigher median/p90/character fraction,<=2 worse and package<=105%,
with all qualification/coverage/audits passing. Rank by actions,package,width,arm.
Report every failed predicate; no post-result threshold choice.

M1 remains400/500,<=256entries,median<=32,p95<=96selections,<=10%single-character
selection bits,zero whole-solution entries. This panel cannot qualify M1 or confer
confirmation, autonomous assembly, human fluency or deployment authority.

## Runtime and review

Two search workers pinned to cores2 and3, sequential five-arm fitting within each
width; the same two workers then perform encoding. Qualification follows with
four workers within cores2-5, no phase overlap. Root coordinates these exact cores
with other runs before launch. Pinned/usr/bin/python3, PYTHONHASHSEED=0,4GiBaddress
space perworker,7200-second global deadline; parent terminates children on timeout and writes durable phase/failure metadata.
The launch.py supervisor starts a separate process group under taskset2-5, covers
preflight/setup with a7230-second outer cap, and kills the whole group after
failure/timeout before writing its receipt. Partial artifacts stay preserved;
any failure blocks reporting/promotion.
No model/GPU/SciPy requirement, install, training or download.

Synthetic graph/structural/codec/search/qualification tests, syntax/import/help
and hash-only verify precede launch. Freeze,code,contract pushed; Claude review
or documented PLAN30-minute timeout before launch. Source publication, protected
opening, training, human studies and production remain owner-gated. Intent and
component boundaries preserved; no ledger/catalog/claim writes.
