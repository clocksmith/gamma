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
