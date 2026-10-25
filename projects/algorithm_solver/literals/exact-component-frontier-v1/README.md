# Exact component frontier: bounded finite-U/V control

Component intent is preserved. This is offline representation evidence, not source
qualification, recognition, autonomous solving, a full-corpus result or M1.
Original M1 remains **UNMET**. Foundation 1a/1b/1c is not blocked on this experiment.
No existing runs, admission authorities, thresholds or protected populations change.

## Implemented control

`frontier.py` exhaustively enumerates all nonempty subsets of a supplied legal
literal universe (at most18 entries) and every reachable source-variant choice
(at most12 problems and8 variants each). There is no mandatory singleton alphabet.
Every segmentation minimizes selections N, then absolute singleton selections C,
then literal IDs, using the existing explicit-basis-v2 code-point DP checked
against its independent forward UTF8-byte DP. Singleton means `len(string)==1`,
not byte length or historical ID. Unreachable means `None`, never a finite sentinel.
The default feasible population is every supplied problem; partial-coverage runs
retain the complete denominator and explicit unreachable IDs.

Co-selection first maximizes feasible coverage, then minimizes N and absolute C.
Dictionary bytes are only a deterministic subsequent tie-break. Every reachable
source choice is enumerated, not greedily discarded before aggregate gates.
Median is a rational arithmetic mean of the middle two counts for even populations;
p95 uses nearest rank. Optional median/p95/character-fraction gates never replace
historical thresholds. Minimum paths prevent padding to dilute character fractions.
A dual-feasible all-zero potential vector is not accepted as a shortest-path proof.

All original strings remain immutable. Whole-source entries of **any** supplied
variant are excluded even if that variant is not selected. Real sources additionally
require an existing qualification/access authority and a stronger explicit legality
predicate; the generic synthetic API does not purport to recognize arbitrary
whole-solution bodies. It is not a second qualification registry.

`expansion_levels` systematically introduces all witnessed adjacent-character
merges in increasing maximum length. No top-K or random sweep. The persisted
nondominated ledger compares identical covered populations on N, absolute C,
median, p95, entry count and complete package bytes. It is report-only: **no**
intermediate dictionary is pruned from exhaustive enumeration because it looks
locally dominated. Thus retirement, source-choice crossovers and later merge
synergies are not lost to heuristic frontier pruning. The exactness claim is always
finite-U/V; a resource cutoff says `incomplete_budget`, never infeasible/optimal.

LTD1 dictionary serialization and LTV1 fixed-width packets reuse the existing
literal codec, including dictionary hash, 41-byte packet framing, bit padding,
strict reconstruction and the charged decoder source bytes. The five profiles
are16/32/64/128/256 (4/5/6/7/8 bits). Tiny U below16 does **not** test a binding
capacity frontier, even though every profile is exercised.

## Evidence

-15 focused tests cover the mandated `D={a,b,ab}`, source `ab`, alleged path
 cost8/budget3 counterexample; exhaustive independent all-path segmentation;
 independent dictionary/source enumeration; source crossovers; aggregate-gated
 source choice; Unicode singleton charging; character retirement; exact even-median
 gate; unreachable states; whole-source exclusions; full packet costs and cutoffs.
-`SYNTHETIC-RESULT-v1.json`: two public inert synthetic problems, incremental
 universes of2/6/10 entries. All subsets (3/63/1023) exhausted at all five widths.
 Best total N falls10 ->6 ->4; absolute C falls10 ->0 ->0. These strings are not
 candidate algorithms. The receipt pins implementation/helper hashes at run time;
 its test-file pin describes the then-current14-test suite, before the additional
 end-to-end median test. Later focused tests are recorded below, not rewritten into
 that historical receipt.
-`QUALIFIED-PAIR-RESULT-v1.json`: exactly Python `leetcode:1160` and `leetcode:916`,
 canonical `normative-typed-effects` metadata verified through immutable v9b config
 SHA`c805894d69b36fefbc4cb0af6204872dfe9b655e719679019a088513db2bcea2`.
 Source bytes were opened only through `KnownSpecService.request` after both
 metadata selections passed, with the existing per-open boundary gate.
 Family: character-frequency constraints. Full-catalogue denominator remains4081;
 this diagnostic has denominator2. No cases or other source payloads were read.

The qualified pair proposed78 line/adjacent-two-line fragments; exact cross-problem
reuse plus full-source/complete-body containment exclusions left9 legal entries.
All511 nonempty dictionaries were exhausted for each width. Even unlimited use of
those9 entries reaches **0/2** sources. This proves only restricted finite-U/V
infeasibility, **not** capacity infeasibility or global impossibility. There is no
feasible selection median or package result to promote. The diagnostic took0.77s
and40.5MiB peak RSS. Only aggregate metrics, identities and hashes are persisted;
no source fragments, sources, private dictionary or sequence payloads are published.

## Reproduce

From repository root, with no external dependencies or candidate execution:

```sh
(ulimit -v 524288; ulimit -t 60; timeout 60s python3 -B -m unittest discover -s projects/algorithm_solver/literals/exact-component-frontier-v1 -v)
(ulimit -v 524288; ulimit -t 60; timeout 60s python3 -B projects/algorithm_solver/literals/exact-component-frontier-v1/run_synthetic.py > /tmp/exact-frontier-synthetic-new.json)
```

`run_qualified_pair.py` is intentionally hard-bound to the approved two IDs/config;
its execution requires that same source-access authority. It accepts no corpus path
or candidate-execution option. Preserve historical outputs when rerunning.

## Next legal pool step

The line-only universe lacks byte coverage, rather than running out of dictionary
slots. Propose a frozen deterministic cross-problem repeated-substring trie universe
plus **explicitly charged** singleton entries on these same two authorized sources.
Record every whole-source/body rejection and complete repeated-fragment inventory.
If U exceeds18, do not silently truncate it or claim exhaustive global search:
coordinate a bounded exact residual neighborhood with a declared fixed charged
basis, then systematically expand/merge that neighborhood and retain every frontier
state. Additional source variants need exact qualification/access bindings; larger
compute needs coordination. No additional real-source reads or compute are implied
by this proposal. Protected final100/protected66/combined482 and unknown727 remain
closed. No models, downloads, training, GPUs, paid services or remote execution.

Sparse-workspace note: the linked original literal-goal JSON and incremental-v5
implementation were absent. The preserved literal clauses in
`HISTORY-CATSCAN-v1.md`, original `MILESTONES.md`, current goal/CATSCAN hierarchy
and `catalogue/ROADMAP-v1.md` were read; available incremental-v7,
explicit-basis-v2 and relaxed-capacity helper code was inspected. Only present,
self-contained exact DPs/codec were imported; no broad pool loaders were imported.

## Authorized repeated-substring continuation

The lead subsequently approved a same-two-source continuation (no new payload IDs).
`repeated.py` uses suffix automata and prefix-doubling suffix-array/LCP indexing;
it counts all distinct shared substrings without retaining a quadratic string
table. Every multi-character entry has two distinct problem witnesses; singleton
entries are explicit and charged. Whole-source and complete solve-body containment
remain excluded. Exact all-U segmentation is a capacity-relaxed diagnostic only.

The complete inventory is **6,031** entries:5,981 shared multi-character literals
and50 source characters. Its relaxed exact shortest paths total **N=200,C=77**.
Before residual search, all89 distinct non-character path witnesses were frozen
in declared ID order1160 then916, left-to-right, partitioned into15 groups of at
most6. Each group exhaustively explores every subset against each prior accepted
basis. Unused entries retire after exact reconstruction; retained definitions are
always stored in full. This is exact **within each frozen residual neighborhood**,
not global optimization over6,031 entries or complete pricing. The matched sources
and their qualified identities are unchanged.

| Capacity | Reached / diagnostic denominator | Entries | N | C | Median | p95 | Full package bytes |
|---|---:|---:|---:|---:|---:|---:|---:|
|16|0/2|—|—|—|—|—|—|
|32|0/2|—|—|—|—|—|—|
|64|2/2|64|745|656|372.5|488|9,481|
|128|2/2|110|201|79|100.5|121|9,987|
|256|2/2|110|201|79|100.5|121|10,012|

All packages include8,240 decoder-source bytes. The50-entry singleton baseline
requires N=C=1,437 and packages9,658/9,838/10,017 bytes at6/7/8 bits. Thus the
128-entry selection improvement **increases** complete package bytes; storage
tradeoffs are not hidden. Low-width absence means only no feasible explored
state, not an impossibility proof. Character fractions are656/745 and79/201;
absolute character dependence remains material. This does not meet original M1.

`REPEATED-PAIR-RESULT-v1.json` preserves the first23.46s run:2,529 candidate
evaluations and221 nondominated aggregate states, peak40.5MiB. Its ordering label
incorrectly said “numeric ID”; the actual hard-bound order was1160 then916. v2
corrects that label and hardens the singleton-whole-source edge case; it preserves
v1 rather than rewriting it. Both receipts contain aggregate metrics/hashes only.
The final focused suite has20 tests, including exhaustive substring-inventory and
all-U DP parity, residual retirement, explicit-basis capacity, deadline handling
and singleton-whole-source rejection. No native candidate judge was run or needed:
this optimizer treats independently qualified source bytes solely as data.

Next: price systematic alternative repeated fragments against the current accepted
basis, or coordinate a larger exact residual neighborhood that can retire used
characters under replacement. The present finite neighborhood explains neither
the remaining one-selection gap to the relaxed oracle nor low-width infeasibility.
Further compute must retain the same boundary gate, explicit source identity,
complete charges, protected exclusions and measured stopping status.

Final check:21 focused tests pass and all7 Python modules compile
(`FINAL-CHECK-v1.json`). v2 repeated-pair rerun completed in19.24s with the same
2,529 evaluations and identical profile objectives/costs. A final general
single-character whole-source unreachable-propagation fix is covered by focused
controls; these real sources have many characters and that fix does not change
this pair's result. Historical receipt code pins are preserved, while final code
pins are recorded separately. The next same-language19-JavaScript-family proposal
and its missing exact receipt/source-freeze bridge are in
[`NEXT-JS-GLOBAL-IMPACT.md`](NEXT-JS-GLOBAL-IMPACT.md).

## Full300-fit JavaScript impact (completed bounded follow-through)

The approved follow-through resolved the fold receipt bridge and found **all19
fold variants already present by owner/hash** in the875-source pool. Same-vocabulary
addition therefore makes no change. Two bounded slices then priced all460 frozen
reviewed-helper/shared-component bundles against the unchanged full300 population.
No hidden macro definitions: every component is stored/charged flat. All875 source
opens in each slice passed the live gate and pinned source hash; no cases opened.

Final256-capacity candidate uses251 entries: N35,706 -> **35,402**, absolute
C14,932 unchanged, median91 ->90, p95=248 unchanged.168 programs improve, none
worsen; all300 final exact paths/packets independently verify. Complete package
57,986 ->57,693bytes including decoder. The character fraction **worsens** from
41.8193% to42.1784%. No source switches and zero fold variants selected; the
reviewed fold helper retires as unused. The gain is from one ordinary literal,
not a fold-component victory or M1 qualification. All26 nondominated retained
states share the baseline source-choice hash. No global-optimality claim.

See [`NEXT-JS-GLOBAL-IMPACT.md`](NEXT-JS-GLOBAL-IMPACT.md) for precise bindings,
method, preserved failed/partial receipts and completedv3 outcome. v3 finished in
41.56s at60.2MiB peak; CPU is idle after handoff. No live optimizer state was changed.

## New actual joint source/helper gain

The [indexed long-span and complementary repair experiment](LONG-SPAN-RESULTS.md)
now yields a **255-entry** bounded candidate over the same875variants/300fit:
N35,402 ->35,086, absoluteC14,932 ->14,892,median90 ->88.5,p95=248.123 problems
improve,none worsen; **two qualified fold variants switch in and the reviewed
helper remains**. Complete package57,693 ->57,502bytes. The singleton fraction
still worsens42.1784% ->42.4443%; no M1/promotion claim follows.
All300 final paths/packets independently verify. The frozen cross-product remains
partially searched with explicit active-retirement counters; its incumbent is
verified, not globally optimal. Aggregate frontier merge preserves88 distinct
states and34 nondominated states. The next executable resume point and quiet-CPU
coordination requirement are documented; no further heavy task is active.
