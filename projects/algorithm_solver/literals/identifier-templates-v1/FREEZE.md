# Mined identifier-parameterized AST templates

Board20, goal2c, separate structured representation. Earlier structural-v1 used
31handwritten components; expression-prefix-v1 used32short expression patterns
with each child/repeated identifier separately charged. Test automatically mined
AST-span templates whose repeated identifier arguments are explicit parameters.
No source/algorithm rewrite, model training or hidden identifier table.

## Fixed sources and matched arms

Two fixed-source cohorts: item13 control256 R and selected scope_joint256 naming,
each qualified fit300/consumed-validation100. The naming seed was selected using
validation outcomes; this is adaptive development. Final held-out100/protected66
stay closed. Four256-entry/eight-bit arms: literal and typed for each cohort,
starting from the same cohort dictionary and exact source bytes. No corpus
extraction, eligibility or cost search preceded this freeze. Twelve synthetic
tests cover repeated/distinct arguments, shared alpha patterns, fixed properties,
whole-body/free-byte checks, unavailable long identifiers, literal-span boundaries,
malformed arguments, independent ASTIdentifier span checks, escaped identifiers
and exact-cache parity. Compile/import/help checks pass.

## Mining and parameter semantics

Acorn identifies candidate spans of2–160bytes. Node kinds: for/for-of/for-in,
while/do-while,if,return,variable declarations and expression statements;
assignment,call,binary,logical,conditional,new,member,array,object,unary/update
expressions. Identifier nodes also supply whole-identifier literal proposals.
Standalone parsing (expressions, or one statement in a function wrapper) must
recover the same root kind; unsupported contextual syntax remains literal.

Within a candidate, parameterize exact-spelled Identifier spans, grouped by the
same identifier text in first-occurrence order. These are text parameters, not
new semantic bindings or claims about variable resolution. Leave fixed:
noncomputed member/property/method keys, labels, escaped identifier spellings,
and solve/undefined/Infinity/NaN/Math/Number/Array/Object/JSON/Map/Set/String/
Boolean/BigInt/Date/RegExp/console. Require1–4distinct parameters, at most16
occurrences and2–96fixed bytes. Store root kind, all fixed parts, occurrence-to-
parameter indices and arity in the charged dictionary entry.

One constructor selection is followed by one literal selection per distinct
parameter. That literal must be the complete actual identifier, not a character
fragment. If it is absent, the constructor match is unavailable. No default
name, external lookup, free raw spelling, END or recursive argument exists.
The decoder repeats the charged argument bytes only where stored occurrence
indices specify. Sharing a name across distinct lexical bindings inside a
match is a text equality, not a semantic rewrite; the full decoded source must
still equal the qualified source exactly.

## Whole-solution and decoder checks

Reject a match equal to a complete source, solve definition, solve body or its
trimmed block contents. For each use, fixed bytes plus repeated copies of argument
bytes must be strictly less than half the complete program bytes. This preserves
structural-v1's per-match rule. Report summed free bytes and the maximum per-program
share; no new aggregate half-program limit is imposed, because combining reusable
small templates is the representation being tested. All fixed text/repetition
metadata is stored and charged, and each distinct argument is selected explicitly.

The independent Node decoder validates dictionary shapes,1–4arity/16occurrence/
96fixed-byte bounds, identifier arguments, and each expanded root kind. It
reparses every expansion and requires each inserted span to be exactly one
Identifier with the same name, rejecting token-pasting and contextual changes.
After reconstructing the full solve program, it independently enforces the same
per-use free-byte and whole-source/body exclusion. Malformed/truncated packets,
wrong hashes/widths, unknown IDs, nonliteral/nonidentifier arguments and invalid
AST shapes fail closed. Expansion output is bounded at4MiB. No source execution
inside either encoder/decoder; unchanged-source qualification is reused by hash.

ITD1 stores canonical JSON for every literal/template and all metadata. ITB1
stores41-byte magic/width/dictionary-hash/count framing and8-bit IDs. Literal
controls retain LTD1/canonical packets. Both have<=256entries and all96fallback
characters. Every constructor, argument literal and ordinary literal is one
selection; Finish adds one. Repeated identifier occurrences cost through the
constructor/argument mechanism, not through invented free declarations.

## Fit-only pools and bounded search

Templates require at least two distinct fit owners. Rank by summed
(fixed bytes + repeated argument-copy bytes -1) across occurrences, then canonical
specification text; keep64. This byte heuristic only proposes candidates;
acceptance uses exact full-program selection counts. Whole-AST/identifier literal
pool: lengths2–160, at least two fit owners, exclude all fit source/body strings;
rank occurrence*(bytes-1),length,text and keep256. Both arms receive that same
literal pool and selected-literal-span proposer (24span merges plus24pool literals).
Merge up to6adjacent selected ordinary literal spans, max160bytes. Constructor
arguments never masquerade as adjacent output spans for proposal merging.
Typed additionally receives the64template candidates; controls cannot emit
constructors. Proposal counts/paths can differ after parsing changes; both share
the same evaluation/time ceilings. This compares complete search procedures,
not equal internal proposal trajectories.

Each source encoder finds a minimum selection-count path over literal edges
and available template calls, tie by complete ID sequence. No recursive template
matching. Each dictionary round measures all nonmandatory deletions, shortlists
12removals by exact loss, considers additions with room and all proposal/removal
swaps; accept a strict total-fit-selection gain, tie by package and dictionary
order. No pair moves, random kicks or learned scorer. Cap12000exact evaluations
or600seconds per arm; retain incumbent and report every stop. Fourworkers on
cores0–7,4GiBperprocess,1800-second overall ceiling,PYTHONHASHSEED0.

Seal fit dictionaries/pools before loading validation values. No validation
refit, source adaptation or test-driven repair. Audit final literal entries against
both splits' source/solve-body strings; preserve any failure. All1600packets decode
independently to original source hashes; no new case execution is claimed.

## Costs, conditional evidence and decisions

Report all programs, eligibility and actual template-use subsets separately:
selection/action totals and median,p90,p95,worst,<=32/96; paired better/same/worse;
absolute literal single-character codes/fraction; constructor entries/codes/
programs, argument codes, fixed bytes and repeated copied bytes, summed/max free
byte share; dictionary/packet/framing/padding and decoder-source-inclusive storage.
Typed decoder.cjs+Acorn source are charged; literal decoder dependencies unchanged.
Offline extraction/search tooling is separately inventoried; full runtime footprint
unmeasured. No human fluency or autonomous-solving claim from offline source encoding.

- I1: initial dictionaries reproduce each cohort's recorded fit/validation counts.
- I2: typed uses at least one template in at least20Rvalidation programs.
- I3: typed saves at least5%validation actions versus matched literal in both cohorts.
- I4: relative typed action gain is greater on R than on naming.
- I5: all1600packets decode/source hashes qualify and whole-solution audits are clean.
- I6: no arm meets every M1 numerical cost indicator; typed remains a separate2c
  representation regardless of those indicators.

Input readiness versus matched literal remains100validation decode/qualify,
clean audits,>=5%fewer actions,strictly lower median/p90,>=60better/<=25worse,
nonincreasing literal-single-character fraction,rawpackage<=105%. Rank any ready
structured arms by actions,package,cohort. This only motivates separately frozen
owner-approved confirmation of that representation; it does not relabel templates
as flat literals or change M1. Report every failed predicate and the conditional
eligible/used contrasts even if no overall candidate is ready.

Freeze/code/contract pushed then Claude review (or PLAN30-minute timeout) before
launch. Component intent preserved; no production/canonical codec or ledger/catalog/
claim change. Training,protected opening,publication,BITS deployment,independent
confirmation and human studies remain owner-gated.
