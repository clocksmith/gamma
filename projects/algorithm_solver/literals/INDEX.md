# Composition experiment index

Start here for source versions, experiments and the working literal languages.
This is a navigation index over existing manifests and reports, not a second
results ledger. Completed runs below retain their source, dictionary and execution identities.

## Exact character-fraction certificate — 2026-10-23

[Fixed-source/codebook ratio optima](fraction-certificate-v1/README.md): all six
certificates and3,600packet decodes pass. Validation minima are77.75% R128,
48.63% R256 and43.91% naming256;10% is unreachable for these fixed pairs even
without an action budget. The256witnesses add12.94%/14.12% actions. This bounds
no changed dictionary or source, and promotes no encoder.
[Freeze](fraction-certificate-v1/FREEZE.md), [review](fraction-certificate-v1/REVIEW.md),
[evidence](fraction-certificate-v1/evidence/results.json).

## Mined identifier templates — 2026-10-23

[Identifier-parameterized AST templates](identifier-templates-v1/README.md): all
1,600 packets decode with unchanged-source qualification. R saves 33 validation
actions (0.36%); naming adds 11. Both have 95 eligible programs, but use templates
in 20 and 1 respectively. Neither candidate is ready; conditional benefits and
complete metadata/decoder costs are reported. Separate structured goal2c.
[Freeze](identifier-templates-v1/FREEZE.md), [review](identifier-templates-v1/REVIEW.md),
[evidence](identifier-templates-v1/evidence/results.json).

## Prefix expression constructors — 2026-10-23

[Matched prefix-arity experiment](expression-prefix-v1/README.md): all 1,600
packets decode; validation actions improve 1.28% at 128 entries and 0.46% at
256 versus searched literal controls. Storage increases, neither arm is ready.
Eligibility and actual use are reported separately; no constructor-impossibility
or M1 claim. [Freeze](expression-prefix-v1/FREEZE.md),
[review](expression-prefix-v1/REVIEW.md), [evidence](expression-prefix-v1/evidence/results.json).

## Compiler alternatives — 2026-10-23

[Compiler choice and joint fitting](compiler-choice-v1/README.md): all 3,200
choices qualify; 589 distinct changes pass 57,280 checks. At 128 entries joint
saves 5.28% validation actions (81 better/11 worse) but raises single-character
fraction; at 256 it saves 0.15%. No ready arm. Byte-minimum source can worsen
literal input cost. [Freeze](compiler-choice-v1/FREEZE.md),
[review](compiler-choice-v1/REVIEW.md), [evidence](compiler-choice-v1/evidence/results.json).

## Scope-local naming family — 2026-10-23

[Fixed naming alternatives](scope-choice-v1/README.md): all 3,200 choices qualify;
163 distinct changed programs pass 15,632 checks. Joint naming saves 21/28 validation
actions at 128/256 over matched printer controls; only three validation programs
choose a mangled profile in either joint arm. No ready arm. This is a finite
alphabet-family result, not a bound on per-binding search.
[Freeze](scope-choice-v1/FREEZE.md), [review](scope-choice-v1/REVIEW.md),
[evidence](scope-choice-v1/evidence/results.json).

## Per-binding naming descent — 2026-10-23

[Capture-conflict naming search](binding-descent-v1/README.md) passes the frozen
development criteria at256: scope_joint saves6.01% validation actions
(75better/21same/4worse), lowers character fraction55.14%→49.89% and package
bytes15,255→14,724. Fixed-dictionary scope also passes (5.22%,73/27/0).
All4,000choices qualify;649distinct changes pass62,521checks. Confirmation is
owner-gated; M1 remains unmet. [Freeze](binding-descent-v1/FREEZE.md),
[review](binding-descent-v1/REVIEW.md), [evidence](binding-descent-v1/evidence/results.json).

## Coupled naming continuation — 2026-10-23

[Dictionary-guided coupled changes](coupled-names-v1/README.md): all2,400choices qualify;
324distinct changes pass32,466checks. Coupled proposals save7validation actions
over the ready item13 seed (5better/95same/0worse), but character fraction rises
slightly despite two fewer character codes. No incremental successor selected.
[Freeze](coupled-names-v1/FREEZE.md), [review](coupled-names-v1/REVIEW.md),
[evidence](coupled-names-v1/evidence/results.json).

## Exact segmentation audit — 2026-10-23

[Fixed-source tie and character objectives](segmentation-audit-v1/README.md): all6,400
packets decode. Among shortest encodings, control256 validation character codes
fall4,934→4,855 (1.60%) at unchanged9,048actions; scope_joint256 falls4,193→4,129.
Control128 has no character-count tie headroom. No encoder change or promotion.
[Freeze](segmentation-audit-v1/FREEZE.md), [review](segmentation-audit-v1/REVIEW.md),
[evidence](segmentation-audit-v1/evidence/results.json).

## Character-aware dictionary objectives — 2026-10-23

[Fixed-source weighted search](character-objective-v1/README.md): all6,000packets
decode. Strongest penalty reduces validation character codes6.13% but increases
actions5.17%; it misses the frozen10%within5%tradeoff. The original ready seed
remains selected. Canonical/common-encoder and weighted views are separate.
[Freeze](character-objective-v1/FREEZE.md), [amendment](character-objective-v1/AMENDMENT-1.md),
[review](character-objective-v1/REVIEW.md), [evidence](character-objective-v1/evidence/results.json).

## Pinned FSST comparison — 2026-10-23

[Native FSST and Gamma adapters](fsst-compare-v1/README.md): all4,000packets decode.
Optimal native parsing saves2.07%/2.31%validation actions over the author encoder
on R/naming, but both native and adapted tables remain larger than Gamma’s seeds.
No ready adapter; the native eight-byte symbol limit and format stay explicit.
[Freeze](fsst-compare-v1/FREEZE.md), [review](fsst-compare-v1/REVIEW.md),
[evidence](fsst-compare-v1/evidence/results.json).

## Current goal navigation

[Goals v2](../contracts/algorithm_solver_goals_v2.json) organizes recognition
(1a–c), exact-string languages/joint optimization (2a/2b), structured languages
(2c), human studies (3a–c), autonomous assembly/generalization (4a–c), and
publication-quality research (5a/5b). The [current scorecard](../STATUS.md#current-v2-scorecard)
holds measurements and ownership. This index remains navigation, not another ledger.

Historical 2a/2b macro and 3a/3b literal IDs in dated experiment records retain
v1 meanings. The [alias map](../contracts/algorithm_solver_goals_v2.json) maps
representation to 2a/2b/2c and autonomous evidence to 4a/4b without promoting it.
[Behavior-preserving joint composition](RESEARCH.md#behavior-preserving-joint-composition)
permits qualified alternative algorithms while preserving exact successor decoding.
The [readable family](readable-v1/README.md) is one human-readable policy under
2a; arbitrary-fragment compression remains a separate policy. Both can use 2b.

## Current local implementation checkpoints

These reviewed commits are local research evidence, not new BITS profiles or
public releases. Their runtime/test receipts retain the historical contracts.

| Goals | Implementation and evidence | Result and limits |
| --- | --- | --- |
| 2a/2b | [Audited incumbent preservation](joint-v1/incumbent-v1/README.md), `af6d804ff84dfebaaeee4aefbc92b54b8f6d9906` | Four 16-problem JS/Python arms retain the best imported feasible costs after 80 proposals; no measured rewrite gain. 21 focused tests, 64 packet roundtrips and 2,164 independent forward-DP checks. |
| 2a/2b | [Integer-count alignment](count-alignment-v1/README.md), `ee687ebc8f3b4dbbe039acaef792673869e1e359` | Full-program evidence covers two development problems in both languages. Joined helpers save ten six-bit selections per language versus their exact-line successor control, but increase dictionary/package storage. Preserve original no-helper alternatives; no human-usability claim. 18 focused mechanism tests. |
| 2a/2b | [Dot source-witness inventory](seed-inventory-v1/README.md), `a67e8dc9e8463236b483fa6660e7890a393df118` | 187 cross-problem physical-line witnesses from 120 hash-verified sources / 60 problems; ten tests. Lines are not automatically complete statements or semantically qualified components. Source admission is unchanged. |
| 2b/4c | [Candidate energy harness](energy-search-v1/README.md), `94ea02c9c619a2c3bb8c8cf7bd1152cafb952dcc` | Contract-gated exact costs, source/dictionary neighborhoods and a scorer interface; 30 tests, 18 synthetic arms and a 32-state restricted reference. No model trained, candidate programs executed or independent solving established. |

The [energy protocol](energy-search-v1/PROTOCOL.md) separates development library
optimization from frozen unseen composition. Candidate provenance, qualification,
full input/storage costs and protected boundaries remain gates before promotion.
The existing Python statement miner is
[`macro_mine.py`](../findings/corpus-macro-analysis-128-v1/macro_mine.py): it uses
`ast.stmt` and source segments, but its top-level I/O makes it unsuitable for direct
import. Exact byte-span provenance is a proposed integration refinement, not an
implemented new extractor or semantic-equivalence check.

## 2026-10-23 Python naming transfer

[Python naming transfer](python-name-v1/README.md) uses 27 fit and nine validation
problems with independent Python qualification. All 11 distinct changed sources
pass 1,373 checks. At 256, rename saves 12/949 validation actions; joint saves 15
but worsens median and single-character share. No readiness, no M1 qualification.
The 128-entry arms do not improve; all coverage and failures remain visible.

## 2026-10-23 vocabulary-aware naming

[Binding-aware name search](name-search-v1/README.md) qualifies all 377 distinct
changed programs (37,402 checks). Joint256 reduces validation actions from 9,048
to 8,684 (4.02%), improving 73 and worsening 1; single-character share falls from
55.14% to 51.23%. It fails only the frozen 5% readiness threshold. All six arms
retain full coverage; no promotion. This measures offline source-plus-encoder
optimization, not autonomous solving. Python transfer is the next board item.

## 2026-10-23 tail-search ablations

[Eight-arm tail search](tail-search-v1/README.md) compares alphabet reclamation
and all-position syntax proposals at 128/256 entries. No arm passes readiness.
Reclaiming seven fit-unused character slots loses three validation programs;
positions preserves coverage but adds 16 validation actions at 128 and saves
only five at 256. All searches terminate locally, with no optimum claim.
The next step is vocabulary-aware rewriting under a new qualification contract.

## 2026-10-23 fixed-source feasibility diagnostic

[Cost decomposition and optimistic bounds](cost-decomposition-v1/README.md) uses only
R dev-fit 300 / dev-val 100. L-R-256 dev-val reproduces 8,948 selections (median
63.5, p95 211; 9,048 actions including Finish). Syntax accounts for 50.2% of
byte-fraction selection attribution; identifiers account for 48.2% of the
single-character tail. The fit-only unlimited-substring oracle has median 21
and p95 75, but relaxes shared capacity. The capacity-aware necessary bound is
also too weak to decide M1 feasibility. Neither local search stopping nor
compressor rates prove impossibility. All 800 baseline packets decode exactly;
no held-out/protected sources were opened and no vocabulary was promoted.

## Preserved experiment checkpoints

[Milestones M1–M6](MILESTONES.md) record the agreed compact-library gate and proposed
automation, generalization, scale and literature-comparison targets. Targets are
separate from the measured results below.

**Latest matching refinement:** [Exact token-boundary proposals](scale150-refine-v1/README.md)
on the same 150 programs reduce eight-bit selections from 12,790 to 12,337,
median 77 to 74, p95 205 to 198, and package bytes from 22,773 to 22,296.
A matched deeper AST/span control reaches 12,738 selections. Both arms pass
1,800 independent packet/source-choice checks in total; native source hashes
are unchanged. Original 100 regress by 14 selections; shared 125 improve by 205.
M1 remains unmet; no live dictionary changed.

**Latest staged expansion:** [125 to 150 development problems](scale150-v1/README.md)
represents all 150 with 256 entries: 12,790 selections, median 77, p95 205,
60.43% character bits and a 22,773-byte complete package. The initial three
missing-constructor failures are preserved; the successor explicitly encodes
that support source. All 162 new variants pass 11,878 checks; 1,200 packets and
source choices pass independent audit. Shared 125 regress by four selections;
new 25 improve by 408. M1 remains unmet. Corpus admission and a concrete frozen
500-problem manifest remain qualification dependencies.

**Previous staged expansion:** [100 to 125 development problems](scale125-v1/README.md)
represents 125/125 with the frozen 256-entry dictionary and qualified source
normalization: 9,836 selections, median 67, p95 185, 57.84% character bits and
18,253 package bytes. Shared 100 stay at 6,613 selections; added 25 cost 3,223.
164 source versions pass 15,272 checks; 1,000 packets and source choices pass an
independent audit. Bounded relearning found no input improvement. M1 remains unmet;
no frozen 500-problem qualification population has been established here.

**Previous coordinated source/dictionary result:** [matrix traversal](matrix-kernels-v1/README.md)
uses 6,613 eight-bit selections on the same 100 exposed problems, median 57,
p95 148 and 53.20% character bits. Its 14,005-byte package is 25 bytes larger than
the [window baseline](window-count-v1/README.md). Four rewrites pass 4,584 checks;
2,800 packets independently decode. Seven-bit storage/tail regressions and the
smaller storage alternatives remain explicit. M1 and autonomous solving are not qualified.

**Latest selection-search result:** [exact marginal ranking](rank-v1/README.md)
beats matched estimated ranking on the same 674 source choices / 100 problems.
The 256-entry result uses **6,963 selections**, median **58.5**, p95 **153** and
**53.37%** character bits. Its 14,005-byte package and worst-case 234 selections
are worse than the row control. The 128-entry result improves both selections
(11,558) and storage (15,750 B). All 400 packets independently decode and five
accepted moves replay; unchanged source receipts supply execution evidence.
No compact-library or autonomous-solving qualification.

**Latest joint-refactor result:** [shared DP rows](row-v1/README.md) pass
2,132 checks on 533 cases. One counted helper serves four selected eight-bit
solutions; the same 100-problem pool uses 7,016 selections, median 60, p95 152.
The package increases to 13,948 bytes and character fraction to 53.38%, so retain
the heap package as the smaller-storage control. Source-only and dictionary-only
ablations establish that the selection gain needs both changes. All 800 packets
independently decode. M1 and autonomous solving remain unqualified.

**Latest semantic-refactor result:** [shared heap code](heap-v1/README.md)
cuts #1046 from 494 to 205 selections with the dictionary unchanged. The same 100
problems now use 7,085 eight-bit selections and 13,797 complete package bytes;
worst program 230, median 62 and p95 152. All 332 checks pass and 206 packets are
independently decoded. The helper now serves 976, 1051 and 1046. Character fallback
remains 52.59%; this improves the expensive tail, not Milestone 1 qualification.
[Complete source](heap-v1/generated/sources/1046-heap-role.js) ·
[Sequence](heap-v1/encodings/heap-role-8/manifest.json) · [Comparison](heap-v1/summary.json).

**Latest broader-set checkpoint:** [100-problem expansion](scale100-v1/README.md)
adds 20 already-qualified development problems. All 136 new source versions pass
13,495 checks; 1,000 packets pass independent decoding and receipt joins.
The frozen 256-entry dictionary covers 100/100 in 7,374 selections, median 62,
p95 152 and 52.22% character bits. Relearning does not improve total selections;
a 39-byte package saving costs 14 extra selections. Private sources/tests and
their packets remain on 128; public evidence records identities and costs.
Milestone 1 remains unmet; no autonomous or protected result.

**Latest measured improvement:** [capture-checked source rewrites and joint learning](rewrite-v1/README.md)
reduce the same 80 problems from 6,413 to 5,461 eight-bit selections (14.84%), with
an 11,353-byte complete package (3.63% smaller). Median 57, p95 148 and 51.05%
character bits remain above Milestone 1 targets. All 460 new/control source versions
pass 56,623 checks; 800 packets pass independent decoding and receipt joins.
The matched ablation distinguishes source-only, dictionary-only and joint effects.
No autonomous/protected result or deployment claim.
[Exact dictionary](rewrite-v1/search-v1/joint-256-start0/dictionary.json) ·
[Sequences](rewrite-v1/search-v1/joint-256-start0/manifest.json) · [Audit](rewrite-v1/audit.json).

**Previous joint-search result:** [multi-seed source/dictionary comparison on 128](joint-v1/README.md)
checks 3,299 exact-cost moves over the same 80 problems. The best input count stays
6,413 selections; unused-entry removal saves eight bytes. The storage arm saves
68 bytes (0.58%) but adds 50 selections. All winners still select compact source;
no accepted move switches variants. Eight behavioral checks and 640 independently
decoded packets pass by joining unchanged-source execution receipts. No new
execution, autonomous-solving, protected-result or deployment claim.

**Previous broader-set result:** [measured-gain literal selection on 80 problems](scale-v2/README.md)
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

The [legacy literal contract](../contracts/literal_composition_goals_v1.json) and
[ownership handoff](OWNERSHIP.md) retain their frozen meanings;
[current aliases](../contracts/algorithm_solver_goals_v2.json) reorganize them. The human user owns 1a/1b;
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
| 2c macro representation; 4a/4b macro assembly | Planned broader vocabulary; existing precursors retained | [Macro contract](../contracts/semantic_macro_goals_v1.json). Separate from flat literals; this index does not requalify precursor results. |
| 2a/2b flat literals | Passed offline representation and development execution | [Budget comparison](budgets/README.md) and [preserved working guide](pass2/working/README.md); no hidden slots, renaming, dispatch or injected helpers. |
| 2a readable literals | Small exact-text pilot; qualified source parity | [Readable family](readable-v1/README.md): complete formatted lines and small statements/blocks, three Medium development problems in both languages. Full costs and weak cross-problem reuse disclosed; no typed holes or autonomous claim. |
| Bounded AST preprocessing for literals | Passed for six concrete rewrites | [Rules](pass2/rewrite.cjs), [lineage](pass2/transformations.json), [execution](pass2/execution/report.json). AST parsing selects source rewrites; emitted vocabulary remains flat strings. |
| 2c structured composition languages | Local balanced-statement pilot qualified; broader language unestablished | [Current scorecard](../STATUS.md#current-v2-scorecard) distinguishes that three-problem local pilot from existing AST preprocessing and macro evidence. No autonomous claim. |
| Functional source alternatives for flat literals | Bounded offline experiment passed | [Pass 3](pass3/README.md): guarded functional folds/filter/map and arrow rewrites; no new functional composition language or autonomous claim. |
| 4a literal known-description assembly / 4b frozen unseen evaluation | Unmeasured for these literal packages | Representation success does not establish either goal. Protected holdouts remain outside this index. |
| 3a–c human learning and independent solving | Unmeasured | Guided replay and UI checks are mechanism evidence, not participant outcomes. |
| 4c neural primitives; 5a/5b research quality | Stretch / unmet | [Research protocol](RESEARCH.md) and unchanged [M5/M6 gates](MILESTONES.md) require separate measured evidence. |

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


## Research feedback loop and matched baselines — 2026-10-21

- [Continuous research loop and M6 discovery gate](RESEARCH_LOOP.md), with M1–M5 unchanged.
- [Matched source/dictionary baseline protocol](BASELINE_PROTOCOL.md) and [central literature mapping](RESEARCH.md).
- [Completed JS150/Python25 and restricted flow diagnostic](research-loop-v1/RESULTS.md): methods, aggregates and hash commitments only. This is offline representation evidence; private programs/cases are not redistributed and public corpus reproduction remains incomplete.
