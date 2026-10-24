# Compact composition milestones

Owner direction, 2026-10-20: Milestone 1 is agreed. Milestones 2–5 below are
proposed numerical targets; Milestone 5 is deliberately a hypothetical
literature-leading target. These are engineering choices, not published
qualification standards or achieved results. The owner subsequently authorized
continued milestone work on x@128. That continuation preserves frozen experiment
gates, protected-data boundaries and separate training/deployment qualification.

The [goals contract](../contracts/literal_composition_goals_v1.json) defines the
literal/macro distinction. [Experiment index](INDEX.md) links measured evidence.
Recognition 1a/1b and parameterized macros 2a/2b remain separate; this roadmap
develops literal representation and autonomous assembly under 3a/3b.

| Milestone | Win condition | Numerical target |
|---|---|---|
| **1. A compact library** — agreed | Correct programs can be assembled economically; offline source rewriting is allowed. | **400/500** frozen problems; **≤256** shared literal entries; **median ≤32**, **p95 ≤96 selections**; **≤10%** of selection bits from single-character entries; **zero whole-solution entries**. Compare 128-entry/seven-bit and 256-entry/eight-bit arms. A 100-problem checkpoint is useful but cannot qualify the 500-problem goal. |
| **2. Automatic familiar assembly** — proposed | One problem description produces its composition without human edits or query-time autoregressive generation. | **400/500 first-attempt correct** on independently written descriptions of familiar problems, retaining M1 compactness; complete warm **p50 ≤250 ms**, **p95 ≤1 s**; **zero observed wrong acceptances**. Complete stored-program/sequence lookup is a separately scored control. |
| **3. Unseen semantic variants** — proposed | A frozen composer connects familiar pieces to satisfy changed requirements, rather than merely recognizing paraphrases. | **400/500 first-attempt correct** on fresh protected variants, retaining M1 compactness and M2 latency/error targets. Changed conditions, outputs, state interactions and operation order stay unseen until scoring. |
| **4. Broad, faster composition** — proposed | Scale useful coverage and reduce input and execution costs without enlarging the vocabulary. | **1,600/2,000 first-attempt correct**, across **≥25 predeclared families**; **≤256 entries**, **median ≤24**, **p95 ≤64 selections**, **≤5%** single-character bits; complete warm **p50 ≤100 ms**, **p95 ≤500 ms**; zero whole-solution entries and zero observed wrong acceptances. |
| **5. Literature-leading results** — hypothetical | Beat the strongest applicable reproducible methods under matched tasks and requirements. | **≥20% smaller complete encoded packages** than the best applicable compression/library baseline; **≥2× faster complete solving** than the best applicable published compositional baseline; **≥10× faster than a strong autoregressive baseline**, at no lower independent correctness or accepted coverage. Demonstrate on **3 independently constructed task sets**, on **2 hardware configurations**, with **1 independent external reproduction**. Preserve M4 scale and compactness on the algorithm track. |

## Owner decision, 2026-10-22

The owner approved the M1 admission path: list the 363 metadata-eligible JavaScript
problems with their remaining qualification needs, admit candidates beyond the current
150 as they pass the normal checks, plan newly qualified solutions for the gap to 500,
and freeze the 500-problem population before M1 qualification. Also approved: a frozen
source-rewriting experiment on the 150, then vocabulary search at scale and a held-out
measure. Thresholds and the protected reservation are unchanged. Work moves to a
Jupiter-driven session; see [DRIVER_HANDOFF.md](DRIVER_HANDOFF.md).

## 2026-10-22 progress: frozen 500 and shared-style rewrites

- **The 500 are frozen** ([admission500-v1](admission500-v1/README.md),
  [population-500.json](admission500-v1/evidence/population-500.json)): the 150 earlier
  development problems, all 213 metadata-eligible candidates from ledger revision 1810 (each
  passing source, receipt, contract and literal-harness checks), and 137 newly written and
  independently qualified problems (174 submissions; 37 failures retained). That is 168 easy,
  281 medium and 51 hard, with 48,405 corpus cases. No M1 measurement preceded the freeze, and
  the protected 66 stayed closed.
- **Shared-style rewrites** ([style150-v1](style150-v1/README.md), [style150-v2](style150-v2/README.md)):
  all 150 rewrites qualify with strict parity. The best joint arm represents the 150 in 9,337
  eight-bit selections, median 53.5 and p95 141 (previously 12,337, 74 and 198). On 30 problems
  held out of dictionary fitting, the style cuts selections 13.4%. v1's span proposer scored
  unchosen variants; v2 fixes it, and both runs are kept.
- **First M1 measurement on the frozen 500** ([scale500-v1](scale500-v1/README.md)): **M1 not met.**
  All 350 rewrites of the other problems qualify. The best arm (256 entries, 8 bits, ILS) uses
  43,065 selections, median 63.5, p95 191, 54% single-character, with no whole-solution
  entries; the gates are 32, 96 and 10%. Against the admitted sources the rewrites cut
  selections 66%, mostly because they are about 3x shorter (bytes per selection rise only
  2.67 to 2.97). Dictionaries fitted on 400 problems cost only 1-3% more on the 100 held out
  of fitting. ILS adds under 1%, so the remaining gap needs a different representation, not
  more search. All five predictions were met as frozen.
- **Six-bit Jupiter supplement** ([sixbit-v1](sixbit-v1/README.md)): complete. No verdict changes.
  Canonical any-substring coverage also needs 79 entries (solver-proven, not certified).

## Owner direction, 2026-10-22 evening (with Amendment 1)

The sequence is control, then components, then a scorer only after search headroom is shown.
This is a staged recommendation, not blanket authorization.
- **First:** the compaction-only control [minify-control-v1](minify-control-v1/FREEZE.md)
  (original vs minified vs rewritten sources; fixed and refitted dictionaries).
- **Then:** typed, parameterized components ([structural-v1](structural-v1/DRAFT.md), a draft
  until the control reports). They are audited for disguised solutions and fully charged, and
  compared on a development-validation partition. The final held-out set is not reopened
  after component changes.
- **Scorer:** no learned scorer before stronger conventional search shows real headroom.
  Training needs explicit approval.
- No bit/hex model and no blocked 400-step run.
- M1 thresholds and M2's non-autoregressive rule are unchanged. Offline representation results
  do not establish M2 or M3.

**Control result** ([minify-control-v1](minify-control-v1/README.md)). Minifying the originals
(layout only, all 500 still qualified) makes them 22.4% shorter but saves only 10.1% of
selections with refitted 256-entry dictionaries (147,360 to 132,522). The shared-style rewrites
save a further 66.5% (44,364; median 65.5, p95 199), and all 500 programs improve. Their text
is 60% shorter than the minified sources (names, idioms, removed checks), with 19% more bytes
per selection. Dictionaries barely transfer across styles. M1 is not met. Seven of eight
predictions held; K1 (compaction worth at least 25%) did not.

**Structural components** ([structural-v1](structural-v1/README.md), dev-val 100 only): negative.
31 typed components (counting, queue, graph, tree folds) were audited and fully charged. Only 4,
10 and 19 had support on the original, minified and rewritten sources. Search removed them all
on the original and minified sources. On the rewrites it kept two counting components: −0.12% at
256 entries (8,937 vs 8,948, more programs worse than better) and +0.76% at 128. Operand charges
erase the skeleton savings, because the shared style already makes recurring idioms literal text.
The final held-out 100 was not opened. No scorer: every search stopped at a local optimum under
its cap.

## Owner direction, 2026-10-23 (operand cost)

Relayed from Mars. Next, reduce operand-selection cost instead of adding components:
- declare each identifier once per program, then reference it by role (input, index,
  accumulator, queue, output);
- count every action;
- compare against the shared-style and minified baselines on untouched programs, reporting
  median, p90 and how many programs improve or worsen;
- keep correctness fixed with independent execution tests;
- test unfamiliar human users separately from solver compression;
- predeclare promotion criteria. The 32-selection goal remains, and a small median gain that
  worsens most programs is not enough.

Rename-only is a secondary attribution control. The weak structural-v1 256-entry candidate
(T-R-256) is **not confirmed or shipped**. No BITS update until a candidate beats the live profiles.

**roles-v1** ([FREEZE.md](roles-v1/FREEZE.md)) implements this on dev-val 100:
- arms: bind (B), rename-only (N) and literal (L) on the minified and shared-style pools;
- every action counted, and every decoded program execution-tested;
- promotion criteria frozen before any arm. The final held-out 100 stays closed.

The human study is planned separately ([HUMAN_STUDY.md](roles-v1/HUMAN_STUDY.md)), and it is not
run or simulated.

**Result** ([roles-v1](roles-v1/README.md), dev-val 100): not promoted. Every action is counted,
and all 1,200 decoded programs pass every case.
- **Minified sources:** binding cuts actions 23.9% at 256 entries (27,198 to 20,701; all 100
  programs better) and 19.0% at 128.
- **Rename-only control:** cuts 49.6% at 256 (to 13,700). Declaring the original names gives back
  about half of what role naming saves, and naming explains 74% of the gap from the minified to
  the shared-style sources.
- **Shared-style rewrites:** roles add nothing. Search deleted every slot; L-R stays best at
  9,048 actions, median 64.5.
- **Verdict:** no B arm passes against the shared-style baseline at either width. M1 is not moved.
  All seven predictions held. The final held-out 100 was not opened.

## Measurement rules

- Freeze problem IDs, family/difficulty mix, interfaces, mutation/numerical and
  complexity requirements, independent oracles, budgets and candidate identity
  before qualification. No duplicate/paraphrase inflation of problem counts.
  Retain unsupported cases in the denominator. M1 may fit its known source
  corpus; that is representation qualification, not held-out solving.
- For M2–5, the primary result is the first emitted program, before repair or
  search. Report later attempts separately. Public checks can reject a program;
  independent scoring stays outside the query path. Abstentions and timeouts
  are unsolved. Zero observed wrong acceptances is a finite-sample target, not a
  proof of zero error; report uncertainty intervals and per-family outcomes.
- Input cost includes every literal needed for the complete program and its
  helpers, names, constants and syntax. Compute selection quantiles over
  independently correct assemblies, alongside coverage, and report cost for
  failed attempts too. The fallback fraction is single-character selection bits
  divided by all selection bits for those assemblies. No free source escapes,
  substitutions, hidden tables or problem-specific answer bodies disguised as
  helpers. Report entry sizes and reuse across distinct problems as well.
- Seven/eight bits buy **one selection**, not a whole solution. At eight bits,
  32 selections cost 256 input bits. Packet framing, padding and dictionary
  bytes are additional: the current codec charges **41 header bytes per
  program**. Report payload bits, complete packets, dictionary, decoder and
  model storage separately; show both one-program and amortized package costs.
  Human controls, navigation and correction inputs are an additional measured
  interaction cost, not free selections.
- Complete warm latency includes retrieval, prediction, assembly, validation
  and public checking. Freeze hardware, input lengths and check budgets;
  include timeout/abstention attempts rather than timing successes alone.
  Report cold startup, memory and offline library/training compute separately.
- M3 and M4 require fresh protected requirements and answers after development
  freezes. Familiar bases are allowed for variant tests; also report novel
  families separately. Preserve the existing protected 66-problem reservation;
  this plan neither opens nor replaces it. Report M4 by family/difficulty and
  familiar versus unseen composition, not only the aggregate.

## What “beats the literature” means

Use the [research map](RESEARCH.md) to select and pin strong implementations at
experiment freeze. FSST/OptFSST are encoding controls; Stitch/babble address
library learning; synthesis systems require a separate problem-to-program
comparison. Match source, allowed rewrites, data, representation constraints,
correctness requirements and runtime budgets where applicable. Parameterized
libraries and flat strings need separately labeled arms. Do not infer a
solving win from compressed bytes, or an algorithm-library win from punctuation.

For M5, predeclare comparator versions, adaptations, tuning budgets, cost
formula, datasets and statistical analysis. Charge all side information, with
model/decoder costs explicit. The paired 95% intervals must support the claimed
improvement, and preserve all failures. Three task sets means three distinct
populations, not three partitions of the same 20 examples. A method is not a
universal literature winner: the claim names the actual methods, tasks and
tradeoffs beaten. Numerical superiority alone does not establish novelty;
identify the new mechanism and isolate its contribution with ablations.

## Starting checkpoint

[Scale-v2](scale-v2/README.md) represents **80/80 exposed development programs**
using 256 entries, median **63** selections and p95 **168**, with **53.2%**
single-character selection bits. It has no whole-program entries and no
autonomous-assembly result. This is progress toward M1, not M1 qualification.
The next work is reducing fallback and program length while broadening the
development corpus; preserve each frozen successor and its complete evidence.

## Latest same-corpus refinement

[Token-boundary proposal refinement](scale150-refine-v1/README.md) represents the
same 150 development problems with 12,337 eight-bit selections, median 74,
p95 198, 58.09% character bits and 22,296 package bytes. A matched deeper
AST/span control reaches 12,738 selections. Both 7/8-bit comparisons, storage
alternatives and subset regressions are retained; 1,800 packets independently
decode. This remains far above the M1 cost gates and below its coverage gate.
No source qualification, protected-data boundary or live dictionary changed.

## Latest development expansion

[Scale150-v1](scale150-v1/README.md) reaches 150/150 known development
representations. The 256-entry input arm uses 12,790 selections, median 77,
p95 205, 60.43% character bits and 22,773 dictionary-plus-packet bytes.
All constructor support is encoded. 162 source variants pass 11,878 checks;
1,200 packets independently decode. Shared 125 change from 9,836 to 9,840
selections; new 25 cost 2,950. Both 128/7 and 256/8 arms retain full costs.

M1 remains unmet. The current metadata inventory permits at most 363 distinct
JavaScript problems before further qualification checks, so at least 37 more
admissions are needed for 400 coverage. Admission remains user-owned. Freeze
the concrete 500-problem population before milestone qualification; M1 permits
fitting its familiar source corpus, without opening protected reservations.
Next: bounded exact dictionary refinement on the same 150, then another frozen
expansion using only already qualified development material.

## Previous 125-problem expansion

[Scale125-v1](scale125-v1/README.md) freezes 25 additions across seven structural
families and reaches 125/125 exposed development representations. At 256 entries:
9,836 selections, median 67, p95 185, 57.84% character bits, 18,253 package bytes.
Original 100 remain at 6,613 selections; new 25 add 3,223. The bounded dictionary
search found no further input gain. Both 128/7 and 256/8 arms retain all costs.

M1 is not met. No concrete frozen 500-problem qualification manifest was located
in current contract records; this is a qualification-population gap, not permission
to relabel development fitting. The [separate evaluation protocol](scale125-v1/EVALUATION.md)
preserves all thresholds and protected reservations. Next expansion requires a
new frozen 125-to-150 stage, with frozen-dictionary transfer measured first.

## Previous 100-problem checkpoint

[Scale100-v1](scale100-v1/README.md) supplies 100 exposed development problems.
The [matrix successor](matrix-kernels-v1/README.md), building on the qualified
[window rewrite](window-count-v1/README.md), uses **6,613 eight-bit selections**,
median **57**, p95 **148**, and **53.20%** character bits. Its **14,005-byte** package
is 25 bytes larger than the matched window baseline. The seven-bit input candidate
improves median but worsens storage/tail/fallback; retain the reported alternatives.
Four source rewrites pass 4,584 checks; 2,800 packets decode independently.
M1 is **not met**; 100 exposed programs cannot qualify the frozen 500-problem target.

| Milestone | Current evidence | Next decisive work |
|---|---|---|
| 1 | 100 tested development problems; verified shared heap/DP rows; exact ranking beats estimated ranking | Reduce callback/binding fragmentation; extend shared helpers to windows and backtracking, retaining storage/tail controls. Broaden to a frozen 500-problem qualification only with explicit mix and support accounting. |
| 2 | No autonomous literal assembly result | Establish first-attempt description-to-sequence prediction on development data, distinct from stored-sequence lookup; measure correctness and complete latency. |
| 3 | No fresh semantic-variant result | Freeze the composer and qualify development behavior before opening separately reserved variants. |
| 4 | No broad autonomous result | Broaden family coverage after M1–3 gates; count failures and unsupported cases. |
| 5 | Literature mapped, no matched superiority result | Pin applicable comparator implementations and matched cost contracts; compression and solving need separate experiments. |

These are dependencies, not completion claims. Current work stays in literals;
recognition, admission ledgers and protected evaluation remain untouched.

## 2026-10-21 continuation: current development and M6 proposal

The preceding milestone 1–5 definitions and numerical thresholds are unchanged.
Earlier development checkpoints remain historical. Completed language-specific
aggregate receipts and known limitations are in
[RESULTS.md](research-loop-v1/RESULTS.md): 150 exposed JavaScript problems and a
separately qualified 25-problem Python baseline. A smaller corpus cannot qualify
400/500; neither language meets compactness gates. All framing, helper code,
Python indentation/imports and dictionary storage remain counted. The frozen 500
population/admission gap is explicit and protected evaluation remains reserved.

A fluid [research feedback loop](RESEARCH_LOOP.md) evolves problem sets, correct
source alternatives and vocabulary sets **between frozen comparisons**. The
[matched baseline protocol](BASELINE_PROTOCOL.md) isolates source-only,
dictionary-only and joint effects against stronger fixed-source methods. Failed
or mixed results guide the next bounded experiment without erasing their records
or changing milestone thresholds.

| Additional milestone | Win condition | Gate |
|---|---|---|
| **6. Publication-worthy novel discovery** — proposed | A precise new mechanism or substantive finding survives strong comparison and independent scrutiny. | Pass every M6 gate in [RESEARCH_LOOP.md](RESEARCH_LOOP.md): defensible prior-art distinction; attributable result under matched strong baselines/ablations and full costs; correctness/representation integrity; appropriately frozen evaluation; reproducibility and independent review; owner-approved publication decision. No claim of venue acceptance or current achievement. |

M6 does not authorize a public push, paper submission, external message or new
representation implicitly. Recursive/cyclic dictionaries and ring all-reduce
remain proposals with their own decoder/resource/coordination obligations.
An offline encoding result remains distinct from autonomous assembly and unseen
semantic generalization, regardless of whether it motivates a useful paper.

## 2026-10-23 correction and fixed-source cost diagnostic

The owner's forwarded correction supersedes the earlier interpretations that
local search stopping establishes no search headroom or that a new representation
is mathematically necessary. The historical runs and numbers remain unchanged.
A local optimum is not a global bound, and general-compressor rates cannot be
used as a lower bound for a 256-entry exact-string dictionary.

[The frozen cost diagnostic](cost-decomposition-v1/README.md) reproduces the
L-R development baselines with 800 exact packet decodes. At 256 entries on
100 dev-val programs, syntax is 50.2% of byte-fraction-attributed selections;
identifiers are the largest single-character tail (48.2%). A fit-witnessed
unlimited-string oracle reaches median 21/p95 75, against measured 63.5/211,
but relaxes dictionary capacity. The capacity-aware bound on the fixed 400 is
also too weak to establish feasibility or impossibility. These are explicitly
optimistic diagnostics, not legal candidate dictionaries or scorer headroom.
M1 thresholds and held-out/protected reservations remain unchanged. Next is a
matched conventional search ablation on dev-fit, followed by fixed dev-val
measurement; no training, BITS update or source publication is authorized.

**Global dictionary selection** ([lagrange-select-v2](lagrange-select-v2/README.md), dev-val 100): not ready.
A per-occurrence Lagrangian relaxation over 223,244 fit-witnessed strings certifies that no dictionary made of the
96 characters plus pool entries can need fewer than 21,215 dev-fit selections at 256 entries (32,700 at 128);
the best found needs 25,924 (41,247). Exact search started from the Lagrangian primal ends 0.7-1.05% below the
local-search control on fit and 0.2-0.9% on dev-val, with many programs worse. The remaining pool gap (at most
18.2% of total fit selections at 256) is not a median bound, and its attainability is not shown. No scorer case.

**Exact-optimum search audit** ([mip-audit-v2](mip-audit-v2/README.md), dev-fit sub-instances only): on all 18 random
subsets of 20/30/40 dev-fit programs with 32 learned slots, HiGHS reaches a solver-optimal pool dictionary that
scores 2.36-8.86% below where the shared matched80-v3 local search ends (exact canonical rescoring; median gaps
5.25%, 3.71%, 2.95%).
A local optimum is therefore not the best dictionary at this scale; the gap shrinks with subset size, so full-scale
headroom is untested. Proposed next: an exact large-neighbourhood search on the full problem.

**Exact large-neighbourhood search** ([mip-lns-v1](mip-lns-v1/README.md), dev-val 100): not ready. Exact HiGHS repairs
on the full 300 dev-fit programs cut selections 3.26% at 256 entries and 1.41% at 128 below the shared local
search's optimum; dev-val actions fall 2.59% and 0.87%. At 256 more programs worsen than improve (45 vs 33) and the
median rises by one, so the larger fit gain is concentrated. Stacking with item 13's naming is the next shared item.

**Multi-character naming palette** ([palette-names-v1](palette-names-v1/README.md), dev-val 100): null. The frozen
palette drawn from item 13's dictionary held only 3 multi-character names, because of 160 learned entries only 10
are identifier-shaped and 9 of those are reserved words. No call introduced one. Every searched arm equals item 13
on dev-val (8,504 actions), so item 13 stays the current best. The palette idea is untested beyond this rule and
this dictionary.

**Breadth-aware exact LNS** ([breadth-lns-v1](breadth-lns-v1/README.md), dev-val 100): not ready. Forbidding fit
regressions inside each repair protects breadth (0 programs worse) but gains almost nothing. In 16 of 18
cold-started repairs, HiGHS found no feasible point within 300 s, although the current dictionary is always
feasible (fit −14 selections, dev-val −2 actions). Equal relative weights cut fit 1.50% but made dev-val slightly worse (9,053 vs
9,048 actions, 51 programs worse, median 64.5 → 67.5). The plain objective again gives the largest total gain
(dev-val −2.59%) with a concentrated cost (43 programs worse).

**Breadth-aware repairs on item 13** ([breadth13-v1](breadth13-v1/README.md), dev-val 100): no successor. The plain
objective cuts dev-val actions 1.78% (8,353) and gives the lowest p95 yet (169 selections), but the median rises and
36 programs get worse. Relative weighting lowers the median (62.0) and improves 48 programs, but 35 get worse and the
character fraction rises. The nonregression repair again accepts nothing when cold-started. Item 24 remains the
current best.

**Nonregression repair with direct HiGHS** ([warm-nonregress-v1](warm-nonregress-v1/README.md), dev-val 100): a
breadth-safe successor of item 13. 8,377 dev-val actions (−1.49%), median 62.0, 26 programs better and 0 worse. Warm
and cold starts follow identical trajectories, so the warm start is not what helps. The stall in items 22 and 29
is therefore a solver-path difference, not a missing start: item 26's direct model solves the same first snapshots
to optimality in about 160 s. The interface, configuration and model build all differ; which one matters is not
isolated. It does not beat item 24 (8,336 actions, lower fraction), so item 24 remains the current
best.

**New current best: nonregression repair stacked on item 24** ([nonregress24-v1](nonregress24-v1/README.md), dev-val
100). Item 37's breadth-safe direct-HiGHS repair, continued from item 24, gives 8,285 dev-val actions (−0.61% vs
item 24), with 21 programs better and 0 worse. The median stays at 61.5 selections, the p95 goes 197 → 195, and the
single-character fraction goes 49.60% → 49.54%. It passes every frozen gate. The matched uncapped model gains more on
fit, and reaches p95 165, but fails on the median and the fraction (20 programs worse). The M1 gates of median 32, p95
96 and 10% remain far off.

**Tail-weighted nonregression repair from item 43** ([tailcap-v1](tailcap-v1/README.md), dev-val 100): no successor.
The tail-weighted and flat arms reach the identical dictionary through the same 2 moves: dev-val 8,283 actions (−2),
0 programs worse, p95 unchanged at 195. The single-character fraction rises by 0.012 points, so the frozen fraction
check fails. Item 43 stays the current best. Its LNS neighbourhood looks nearly exhausted under the caps.

**New current best by a small margin: fixed-order capped repair from item 43** ([lexfrac-v1](lexfrac-v1/README.md),
dev-val 100). Both arms reach the identical dictionary: 8,283 dev-val actions (−2), 2 programs better and 0 worse,
single-character fraction 49.542% → 49.505%. It passes every frozen gate, so it is selected (flat, on the name tie).
The lexicographic C objective made no difference. The fraction gain over item 48's equal-N result comes from the
fixed universe ID order, through canonical tie-breaking. The M1 gaps are unchanged in substance.

**Larger nonregression neighbourhoods from item 43** ([widenbhd-v1](widenbhd-v1/README.md), dev-val 100): no new
current best. k = 80 with 600 s repairs gives a successor of item 43 (8,283 actions, 0 worse). It ties item 51 on
actions with a slightly higher fraction (49.530% vs 49.505%), so the record-time replacement has no eligible
candidate. k = 120 accepted nothing: all 5 repairs hit the 600 s limit. Item 43's region looks close to a local
optimum for capped exact repairs at these budgets.

**Python: the JS breadth-safe repair transfers partially** ([python-nonregress-v1](python-nonregress-v1/README.md),
9 Python dev-val). At 256 entries, from item 31's anchor: fit −2.7% (16 programs better, 0 worse), dev-val 935 → 929
actions (4 better, 0 worse), median 98 → 97 actions. The single-character fraction rises (56.91% → 57.39%), so it is
not a successor, and it is 2.1% below R against the 5% bar, so it is not ready. At 128 entries nothing moved: k = 32
frees every learned entry and all repairs hit the 120 s limit.

**Python: fraction drift blocks breadth-safe gains** ([python-lexfrac-v1](python-lexfrac-v1/README.md), 9 Python dev-val):
no successor.
- **w8:** the lexicographic N-then-C arm reaches 927 actions (5 programs better, 0 worse vs item 31) and keeps the
  fraction 0.53 points below its flat control. It is still above the anchor (57.41% vs 56.91%).
- **w7:** with k = 8 the repair finds headroom that k = 32 missed: 1,420 → 1,402 actions, all 9 programs better. The
  fraction still rises (74.27% → 74.59%).

On Python, removing selections mostly removes multi-character ones, so the fraction rises.
