# Composition experiment index

Start here for source versions, experiments and the working literal languages.
This is a navigation index over existing manifests and reports, not a second
results ledger. Completed runs below retain their source, dictionary and execution identities.

[Milestones 1–5](MILESTONES.md) record the agreed compact-library gate and proposed
automation, generalization, scale and literature-comparison targets. Targets are
separate from the measured results below.

**Latest broader-set result:** [measured-gain literal selection on 80 problems](scale-v2/README.md)
replaces frequency-only admission with exact counterfactual resegmentation,
reclaims redundant entries, and measures bounded swaps. Scope-safe compact source
plus 256 strings represents 80/80 exposed development programs in 6,413 eight-bit
selections (median63), versus9,218 for matched frequency ranking and7,933 for the
lexical control. The128-string arm covers80/80 in10,155 seven-bit selections.
All240 source versions pass25,236 checks on8,412 distinct cases;960 selected/control
packets independently decode to qualified source hashes. Single-character fallback
still accounts for53.2% of eight-bit selections. No autonomous/unseen-result claim.
[Dictionaries and sequences](scale-v2/search-v2/) · [audit](scale-v2/audit.json).

**Latest input-cost result:** [complete line-span search](budgets/SPANS.md),
59 exact strings at six bits after equal-length compaction, 20/20 programs in
74 selections / 444 selection bits, with 3,834/3,834 development checks.
The complete package is 5,009 bytes, down from the first span result's 5,405 bytes.
This is the selection minimum for its frozen 341-string pool, not a global
optimum or autonomous solving.
[Current dictionary](budgets/compact-v1/budget-64/dictionary.json) ·
[All assemblies](budgets/compact-v1/budget-64/manifest.json) ·
[Live set explorer](https://256.one/labs/two-button/compositions/)

**Previous input/storage tradeoff:** [literal-only budget comparison](budgets/README.md),
58 exact strings at six bits, 20/20 programs in 77 selections / 462 selection bits,
with 3,834/3,834 development checks. Its complete package is larger (4,972 bytes)
than shared7 (4,468 bytes); this is an input-cost/storage tradeoff.
[Exact strings](budgets/selected-v1/budget-64/dictionary.json),
[sequences](budgets/selected-v1/budget-64/manifest.json), and
[execution receipt](budgets/execution-v1/report.json) are preserved.

**Preserved working baseline:** [shared7 guide and two complete examples](pass2/working/README.md),
79 literals, seven bits per selection, 20/20 programs and 3,834/3,834 development
checks. [Exact strings](pass2/working/packages/shared7/dictionary.json) and
[all sequences](pass2/working/packages/shared7/manifest.json) reconstruct complete
JavaScript by concatenation. Offline encoding is verified; autonomous selection
from a description and 3b generalization are untested.

The [six-goal contract](../contracts/literal_composition_goals_v1.json) and
[ownership handoff](OWNERSHIP.md) remain authoritative. The human user owns 1a/1b;
this index does not import their corpus ledger or modify its admission status.

## Bounded functional and AST-informed literal comparison

[Pass 3 report and complete examples](pass3/README.md) records 84 qualified source
variants, 16,258 check executions on the same 20 development problems, and 101
bounded dictionary trials. The new 61-string candidate uses 78 six-bit selections;
the matched fixed-source control takes 81. A 114-string candidate uses 1,107
seven-bit selections and a 2,726-byte package. These are separate storage/input
tradeoffs; the prior 59-string/74-selection result remains the lower-input result.
[Lineage](pass3/generated/manifest.json), [all costs](pass3/comparison.json),
[execution](pass3/qualification-v1/report.json), and [packet audit](pass3/audit.json)
are retained. Functional rewrites and AST-informed fixed-string proposals are
implemented here; autonomous synthesis and AST/functional composition languages
remain unimplemented. Shared7 live dictionary IDs/bytes remain unchanged.

## Larger development clusters and dictionary merging

[Sixty-problem cluster experiment](clusters-v1/README.md) expands the legacy family
to 40 and adds 20 array/matrix problems. The frozen split is 48 fit / 12
previously exposed development-heldback problems. All 180 active source variants
pass 20,277 checks on 6,759 distinct reference cases under the final input-effect
policy. The 84-trial fit sweep finds a 256-string rewritten global dictionary
with 5,345 selections and a 9,413-byte fit package, versus 10,070 selections /
13,408 bytes for naive union and 11,936 / 16,408 for the best fixed-source control.

Frozen expressibility is 48/48 fit plus 11/12 heldback, **59/60 overall**; #929
needs an absent `@` literal. No heldback tuning or autonomous-synthesis claim.
[Split](clusters-v1/contract.json), [comparison](clusters-v1/comparison.json),
[freeze](clusters-v1/vocabulary-freeze.json), [heldback report](clusters-v1/heldback-expression/report.json),
[audit](clusters-v1/audit.json) and [reproduction](clusters-v1/REPRODUCE.md) retain
exact sources, sequences, costs, failures and limitations. Sixteen additional
unqualified preflight source versions exceeded the planned historical source cap;
that deviation is recorded, while the executed pool stayed at 180. Live shared7
and all prior baselines remain unchanged.

## Tracks and status

| Track | Status | Evidence boundary / entry point |
|---|---|---|
| 2a/2b parameterized macros | Planned broader vocabulary; existing precursors retained | [Macro contract](../contracts/semantic_macro_goals_v1.json). Separate from flat literals; this index does not requalify precursor results. |
| 3a flat literals | Passed offline representation and development execution | [Budget comparison](budgets/README.md) and [preserved working guide](pass2/working/README.md); no hidden slots, renaming, dispatch or injected helpers. |
| Bounded AST preprocessing for literals | Passed for six concrete rewrites | [Rules](pass2/rewrite.cjs), [lineage](pass2/transformations.json), [execution](pass2/execution/report.json). AST parsing selects source rewrites; emitted vocabulary remains flat strings. |
| AST-backed composition language | Planned proposal only | No implemented language, vocabulary, sequences, execution result or committed experiment claimed. Existing AST preprocessing is not this proposal. Await research/design. |
| Functional source alternatives for flat literals | Bounded offline experiment passed | [Pass 3](pass3/README.md): guarded functional folds/filter/map and arrow rewrites; no new functional composition language or autonomous claim. |
| Autonomous known-description assembly / 3b frozen unseen evaluation | Planned; untested | Representation success does not establish either goal. Protected holdouts remain outside this index. |

Status vocabulary: **planned** has no measured result; **running** requires live
run evidence; **passed/failed** applies only to the named criterion;
**superseded** preserves the old artifact while replacing its active constraint
or recommendation. A completed negative experiment can pass execution checks
while failing its optimization target. Do not infer overall goal completion.

## Binary demo integration

[Literal demo protocol, tools and evidence](demo/README.md): implemented binary
input using the unchanged shared7 dictionary, separately counted controls, exact
replay and isolated Gamma validation. [Qualification](demo/evidence/qualification.json)
passed 3,834/3,834 checks; [desktop/mobile smoke](demo/evidence/browser-receipt.json)
passed. Human assembly and offline reconstruction only; no autonomous or 3b
claim. This integration has its own introducing Git commit; source and dictionary
hashes remain pinned in the linked records. Live deployment is verified separately.

## Source versions and lineage

The original/pass2 source inventory below contains **20 problems × 6 named source versions = 120 source files**, representing
**94 distinct (problem, source SHA256) pairs**. Package `assembled/` files are
verified decoded views, not additional solution versions. Hash manifests and the
introduction commits below pin immutable versions; later changes should add a
new version rather than overwrite these sources.

| Version | Parent and method | Exact identity / correctness | Introduced |
|---|---|---|---|
| original | Preserved accepted-source export, class interface | [80-source hash manifest](source_manifest.json), [attribution](ATTRIBUTION.json), [execution](execution/report.json) | [2f33bb37](https://github.com/clocksmith/gamma/commit/2f33bb37b88a33d3039b4c662d53c5ca64195676) |
| canonical | Offline authored conservative rewrite from original | [Reasoning](source_reasoning.json), same hash manifest and execution report | [2f33bb37](https://github.com/clocksmith/gamma/commit/2f33bb37b88a33d3039b4c662d53c5ca64195676) |
| idiomatic | Offline authored idiomatic alternative to original | Same reasoning/manifest; full class wrapper included | [2f33bb37](https://github.com/clocksmith/gamma/commit/2f33bb37b88a33d3039b4c662d53c5ca64195676) |
| normalized | Deterministic standalone `solve` extraction from idiomatic | [API lineage/body hashes](normalized_api.json), same execution report; no free official adapter | [2f33bb37](https://github.com/clocksmith/gamma/commit/2f33bb37b88a33d3039b4c662d53c5ca64195676) |
| shared | Normalized → 8 authored counting-family rewrites; 12 byte-identical | [Hash manifest](pass2/source_manifest.json), [design](pass2/source-design.md), [execution/reuse](pass2/execution/report.json) | [a1730d36](https://github.com/clocksmith/gamma/commit/a1730d363a2f3d5ce879879bb84ac0f375bfc788) |
| recomposed | Normalized → 6 guarded AST pattern rewrites; 14 byte-identical | [Rule, replaced spans and parent/output hashes](pass2/transformations.json), [generator](pass2/generate.cjs), same execution/reuse report | [a1730d36](https://github.com/clocksmith/gamma/commit/a1730d363a2f3d5ce879879bb84ac0f375bfc788) |

Older manifests retain paths relative to their original staging layouts. Resolve
source identities using the source table below and recorded SHA256, not a guessed
path: `normalized_api.json`'s `idiomatic/` and `normalized/` refer to `sources/`;
`pass2/transformations.json`'s `recomposed/` refers to `pass2/sources/recomposed/`.
Historical “execution pending” prose in source-only reasoning is superseded by
the linked execution reports, not silently rewritten.

| Problem | Original | Canonical | Idiomatic | Normalized | Shared | Recomposed |
|---:|---|---|---|---|---|---|
| 121 | [source](sources/original/0121.js) | [source](sources/canonical/0121.js) | [source](sources/idiomatic/0121.js) | [source](sources/normalized/0121.js) | [source](pass2/sources/shared/0121.js) | [source](pass2/sources/recomposed/0121.js) |
| 136 | [source](sources/original/0136.js) | [source](sources/canonical/0136.js) | [source](sources/idiomatic/0136.js) | [source](sources/normalized/0136.js) | [source](pass2/sources/shared/0136.js) | [source](pass2/sources/recomposed/0136.js) |
| 169 | [source](sources/original/0169.js) | [source](sources/canonical/0169.js) | [source](sources/idiomatic/0169.js) | [source](sources/normalized/0169.js) | [source](pass2/sources/shared/0169.js) | [source](pass2/sources/recomposed/0169.js) |
| 242 | [source](sources/original/0242.js) | [source](sources/canonical/0242.js) | [source](sources/idiomatic/0242.js) | [source](sources/normalized/0242.js) | [source](pass2/sources/shared/0242.js) | [source](pass2/sources/recomposed/0242.js) |
| 387 | [source](sources/original/0387.js) | [source](sources/canonical/0387.js) | [source](sources/idiomatic/0387.js) | [source](sources/normalized/0387.js) | [source](pass2/sources/shared/0387.js) | [source](pass2/sources/recomposed/0387.js) |
| 551 | [source](sources/original/0551.js) | [source](sources/canonical/0551.js) | [source](sources/idiomatic/0551.js) | [source](sources/normalized/0551.js) | [source](pass2/sources/shared/0551.js) | [source](pass2/sources/recomposed/0551.js) |
| 575 | [source](sources/original/0575.js) | [source](sources/canonical/0575.js) | [source](sources/idiomatic/0575.js) | [source](sources/normalized/0575.js) | [source](pass2/sources/shared/0575.js) | [source](pass2/sources/recomposed/0575.js) |
| 594 | [source](sources/original/0594.js) | [source](sources/canonical/0594.js) | [source](sources/idiomatic/0594.js) | [source](sources/normalized/0594.js) | [source](pass2/sources/shared/0594.js) | [source](pass2/sources/recomposed/0594.js) |
| 605 | [source](sources/original/0605.js) | [source](sources/canonical/0605.js) | [source](sources/idiomatic/0605.js) | [source](sources/normalized/0605.js) | [source](pass2/sources/shared/0605.js) | [source](pass2/sources/recomposed/0605.js) |
| 643 | [source](sources/original/0643.js) | [source](sources/canonical/0643.js) | [source](sources/idiomatic/0643.js) | [source](sources/normalized/0643.js) | [source](pass2/sources/shared/0643.js) | [source](pass2/sources/recomposed/0643.js) |
| 657 | [source](sources/original/0657.js) | [source](sources/canonical/0657.js) | [source](sources/idiomatic/0657.js) | [source](sources/normalized/0657.js) | [source](pass2/sources/shared/0657.js) | [source](pass2/sources/recomposed/0657.js) |
| 674 | [source](sources/original/0674.js) | [source](sources/canonical/0674.js) | [source](sources/idiomatic/0674.js) | [source](sources/normalized/0674.js) | [source](pass2/sources/shared/0674.js) | [source](pass2/sources/recomposed/0674.js) |
| 704 | [source](sources/original/0704.js) | [source](sources/canonical/0704.js) | [source](sources/idiomatic/0704.js) | [source](sources/normalized/0704.js) | [source](pass2/sources/shared/0704.js) | [source](pass2/sources/recomposed/0704.js) |
| 709 | [source](sources/original/0709.js) | [source](sources/canonical/0709.js) | [source](sources/idiomatic/0709.js) | [source](sources/normalized/0709.js) | [source](pass2/sources/shared/0709.js) | [source](pass2/sources/recomposed/0709.js) |
| 724 | [source](sources/original/0724.js) | [source](sources/canonical/0724.js) | [source](sources/idiomatic/0724.js) | [source](sources/normalized/0724.js) | [source](pass2/sources/shared/0724.js) | [source](pass2/sources/recomposed/0724.js) |
| 771 | [source](sources/original/0771.js) | [source](sources/canonical/0771.js) | [source](sources/idiomatic/0771.js) | [source](sources/normalized/0771.js) | [source](pass2/sources/shared/0771.js) | [source](pass2/sources/recomposed/0771.js) |
| 961 | [source](sources/original/0961.js) | [source](sources/canonical/0961.js) | [source](sources/idiomatic/0961.js) | [source](sources/normalized/0961.js) | [source](pass2/sources/shared/0961.js) | [source](pass2/sources/recomposed/0961.js) |
| 1051 | [source](sources/original/1051.js) | [source](sources/canonical/1051.js) | [source](sources/idiomatic/1051.js) | [source](sources/normalized/1051.js) | [source](pass2/sources/shared/1051.js) | [source](pass2/sources/recomposed/1051.js) |
| 1108 | [source](sources/original/1108.js) | [source](sources/canonical/1108.js) | [source](sources/idiomatic/1108.js) | [source](sources/normalized/1108.js) | [source](pass2/sources/shared/1108.js) | [source](pass2/sources/recomposed/1108.js) |
| 1119 | [source](sources/original/1119.js) | [source](sources/canonical/1119.js) | [source](sources/idiomatic/1119.js) | [source](sources/normalized/1119.js) | [source](pass2/sources/shared/1119.js) | [source](pass2/sources/recomposed/1119.js) |

## Experiment chronology

| Experiment / method | Status and measured criterion | Vocabulary, sequences, evidence and limitations | Commit |
|---|---|---|---|
| First source/encoding comparison | Passed: 80 versions,15,336/15,336 checks;144 encoding trials | [Results and trial IDs](results/results.json), [exact dictionaries/sequences](results/encodings), [metrics by API](summary.json), [execution + mutation checks](execution/report.json). Mixed class/standalone interfaces remain separate. | [2f33bb37](https://github.com/clocksmith/gamma/commit/2f33bb37b88a33d3039b4c662d53c5ca64195676) |
| Historical four-bit bounded search | Failed 20/20 target: best 16/20; fixed cap superseded for current pilot | [Search trace and witness](search16-results/results.json). Retained negative baseline, not an impossibility claim or a failed execution result. | [2f33bb37](https://github.com/clocksmith/gamma/commit/2f33bb37b88a33d3039b4c662d53c5ca64195676) |
| Joint source/dictionary recomposition | Passed execution:14 new sources,2,488/2,488 checks;3,888 source combinations and7,825 trials | [Trials/frontier](pass2/results/results.json), [exact encodings](pass2/results/encodings), [execution/reuse](pass2/execution/report.json), [review receipts](pass2/review-evidence.json). Finite-pool enumeration under two heuristic dictionary strategies, not global optimization. | [a1730d36](https://github.com/clocksmith/gamma/commit/a1730d363a2f3d5ce879879bb84ac0f375bfc788) |
| Dense unchanged-source controls | Passed comparison; general improvement claim rejected | [32 control trials](pass2/controls/results.json), [control encodings](pass2/controls/encodings), [combined summary](pass2/summary.json). Rewrites did not beat unchanged-source controls at declared dictionary-byte checkpoints; retain Pareto tradeoffs. | [a1730d36](https://github.com/clocksmith/gamma/commit/a1730d363a2f3d5ce879879bb84ac0f375bfc788) |
| Working 4–8-bit packets | Passed:shared7 decoded 20/20 and3,834/3,834 checks | [Package summary](pass2/working/packages/summary.json), [packet execution](pass2/working/execution/report.json), [codec review](pass2/working/review-evidence.json). Fixed-width IDs and all framing counted; primary shared language has zero whole-program entries. | [0951af88](https://github.com/clocksmith/gamma/commit/0951af88c332818133f132cce9d6cf8e277b90cb) |
| Literal-only 16/32/64/128/256 budget comparison | Passed execution; lower input cost with larger dictionary. Small-cap coverage incomplete. | [Frozen contract](budgets/results-v1/contract.json), [accepted merge traces](budgets/results-v1/trials.json), [pooled winners](budgets/selected-v1/summary.json), [execution](budgets/execution-v1/report.json). 16/32 entries covered9/14 tasks;58 entries cover20 with77 selections. 22 distinct decoded task/source pairs passed4,107 checks; identical programs across widths share execution evidence. No new source rewrite or autonomous solve. | [b4bf675c](https://github.com/clocksmith/gamma/commit/b4bf675c633edbfeefffc691436085634a88297f) |
| Complete admitted line-span pool | Passed: 20 programs, 74 selections, 3,834 checks | [Frozen pool and implementation identity](budgets/spans-v1/contract.json), [minimum counts](budgets/spans-v1/summary.json), [packets](budgets/spans-v1/budget-64/manifest.json), [execution](budgets/spans-execution-v1/report.json). 62 strings; 444 input bits; larger 5,405-byte package. No new source semantics. | Immutable artifact hashes in the linked contract |
| Equally short assemblies, smaller dictionary | Passed: 20 programs, 74 selections, 3,834 checks | [Result and deletions](budgets/compact-v1/summary.json), [execution](budgets/compact-execution-v1/report.json). 59 strings, 444 bits, 5,009 package bytes. Follow-on [75/77/80-selection searches](budgets/frontier-v1/summary.json) found no additional improvement; identical packets reuse execution via [explicit receipt](budgets/frontier-v1/verification.json). | Immutable artifact hashes in the linked contracts |

All trial IDs map to their retained encoding JSON or reproducible method/source
choices. Existing tools and reports remain in place; no rejected trace, source
baseline or raw archive was duplicated to construct this index. Development
checks test outputs and input preservation, not official judge acceptance,
formal equivalence, independent generalization, or query-time synthesis.

## Working package lookup

Every package below was introduced at [0951af88](https://github.com/clocksmith/gamma/commit/0951af88c332818133f132cce9d6cf8e277b90cb). Its manifest binds the
source-encoding ID/hash, dictionary hash, per-program packet/source hashes,
source variant, exact ID sequence, selections/bits/padding and storage costs.
The dictionary JSON is a readable view; `dictionary.ltd` is the counted binary
vocabulary. `programs/` holds the packed sequences and `assembled/` their decoded
source views. The same problem ID joins these records to the source table.

| Package / vocabulary identity | Status | Entries / bits | Selections / selection bits | Dictionary / total package bytes | Sequences | Decoded sources |
|---|---|---|---|---|---|---|
| [whole5 strings](pass2/working/packages/whole5/dictionary.json) | Passed reconstruction; diagnostic whole programs | 20 / 5 | 20 / 100 | 4302 / 5142 | [manifest](pass2/working/packages/whole5/manifest.json) | [JavaScript](pass2/working/packages/whole5/assembled) |
| [characters6 strings](pass2/working/packages/characters6/dictionary.json) | Passed reconstruction; source execution reused by exact hash | 61 / 6 | 4214 / 25284 | 313 / 4300 | [manifest](pass2/working/packages/characters6/manifest.json) | [JavaScript](pass2/working/packages/characters6/assembled) |
| [baseline7 strings](pass2/working/packages/baseline7/dictionary.json) | Passed reconstruction; source execution reused by exact hash | 77 / 7 | 141 / 987 | 3466 / 4415 | [manifest](pass2/working/packages/baseline7/manifest.json) | [JavaScript](pass2/working/packages/baseline7/assembled) |
| [shared7 strings](pass2/working/packages/shared7/dictionary.json) | Passed reconstruction and direct packet execution | 79 / 7 | 154 / 1078 | 3507 / 4468 | [manifest](pass2/working/packages/shared7/manifest.json) | [JavaScript](pass2/working/packages/shared7/assembled) |
| [baseline8 strings](pass2/working/packages/baseline8/dictionary.json) | Passed reconstruction; source execution reused by exact hash | 140 / 8 | 843 / 6744 | 1258 / 2921 | [manifest](pass2/working/packages/baseline8/manifest.json) | [JavaScript](pass2/working/packages/baseline8/assembled) |
| [compact8 strings](pass2/working/packages/compact8/dictionary.json) | Passed reconstruction; source execution reused by exact hash | 140 / 8 | 813 / 6504 | 1419 / 3052 | [manifest](pass2/working/packages/compact8/manifest.json) | [JavaScript](pass2/working/packages/compact8/assembled) |

For non-shared7 packages, exact source hashes join either the baseline
[execution report](execution/report.json) or [rewrite execution report](pass2/execution/report.json).
Do not present reconstructed views as fresh execution runs. At4 bits the measured
bounded witness remains incomplete; at 5 bits the complete whole-program package
is a diagnostic, not the shared-language claim. The 6/7/8-bit languages cover 20/20.

## Research and proposed comparisons

The [budget comparison's package index](budgets/selected-v1/summary.json)
adds five successors at declared widths4–8. Their manifests use the same
dictionary/packet/source hash chain. The 58-entry winner is packed separately at
6/7/8 bits, with dictionaries, sequences and decoded views under
[`budgets/selected-v1`](budgets/selected-v1). These packages were introduced at
[b4bf675c](https://github.com/clocksmith/gamma/commit/b4bf675c633edbfeefffc691436085634a88297f);
the earlier package table remains unchanged.

The [concise literature mapping](RESEARCH.md) separates direct tokenisation,
one-level grammar costs, library learning, fixed-string compression and future
synthesis. An AST-backed composition language remains a proposal. Bounded AST
and functional source preprocessing for flat strings now has the separately
recorded pass3 results above; it is not that proposed language.

## Maintenance rules

Add a short row and links when a scoped experiment closes; update current status
without overwriting frozen sources, reports or failed trials. Record proposals
as planned until they have a committed method and evidence. Pin the source,
vocabulary and encoding identities before comparing results. Keep input API,
case inventory, mutation policy and storage format matched or explicitly distinct.
No running status, success claim or promotion may come solely from a planned
command or generated source. Keep 1a/1b ownership and protected evaluation
boundaries unchanged.
