# Research loop: completed development checkpoints

These results motivate the [continuous feedback loop](../RESEARCH_LOOP.md) and
[matched baseline protocol](../BASELINE_PROTOCOL.md). They measure offline
representation of supplied correct source. No autonomous synthesis, protected
generalization, M1 achievement or literature-superiority claim follows.

## Language-specific matched width comparison

| Language / exposed population | Entries / bits | Selections | Median / p95 / worst | Payload bits | Character selections | Dictionary + packet bytes |
|---|---:|---:|---:|---:|---:|---:|
| JavaScript 150 | 128 / 7 | 20,155 | 117.5 / 292 / 431 | 141,085 | 79.087% | 1,675 + 23,857 = 25,532 |
| JavaScript 150, shared-helper candidate | 256 / 8 | 12,325 | 72.5 / 198 / 305 | 98,600 | 58.037% | 3,900 + 18,475 = 22,375 |
| Python 25 | 128 / 7 | 4,568 | 158 / 296 / 324 | 31,976 | 64.864% | 808 + 5,031 = 5,839 |
| Python 25 | 256 / 8 | 2,684 | 90 / 193 / 205 | 21,472 | 45.417% | 2,044 + 3,709 = 5,753 |

All rows retain their full language-specific denominators, with zero whole-solution
entries. Eight bits wins input cost in both matched comparisons. JavaScript's
separate smaller-package 256-entry control is 12,337 selections, median 74,
p95 198 and 22,296 bytes: the helper saves 12 selections but adds 79 package bytes.
Preserve both tradeoffs. Python's eight-bit package saves 86 bytes versus seven-bit;
that small storage difference should not be confused with its larger input gain.
Every packet charges 41 framing bytes. Python seven-bit padding is 72 bits;
eight-bit padding is zero. Full numeric metrics are in
[language-aggregate.json](evidence/language-aggregate.json).

Difficulty is versioned metadata, not inferred from source length or case count.
JavaScript has **79 easy, 54 medium and 17 hard**. The downloaded
[Doocs snapshot](https://github.com/doocs/leetcode/blob/88c8c2c29f19c186d7cc05c9db17245d9ae3df43/solution/result.json)
(commit `88c8c2c29f19c186d7cc05c9db17245d9ae3df43`) and
[newfacade snapshot](https://huggingface.co/datasets/newfacade/LeetCodeDataset/tree/215604aeed660029df7de2fea5a4d7b6ed476a08)
(revision `215604aeed660029df7de2fea5a4d7b6ed476a08`) agree on difficulty
and slug for all 150 IDs, with no missing matches. This is snapshot-canonical
verification, not a fresh live LeetCode check. Exact downloaded-file SHA-256,
fetch-receipt provenance and the verification commitment are in
[language-aggregate.json](evidence/language-aggregate.json).

A versioned discrepancy is preserved: the last 50 experiment annotations counted
9 easy / 29 medium / 12 hard; canonical snapshots give **8 / 30 / 12**.
Problem 122, Best Time to Buy and Sell Stock II, was annotated easy in that
experiment and is medium in both pinned snapshots. Historical freezes and
admission ledgers were not rewritten. The full 150-program canonical count above
is unchanged; this corrects the stage annotation, not a source or measurement.

Python's separate 25-program metadata panel has **5 easy, 15 medium and 5 hard**.
These exposed samples are not representative random benchmark samples. The two
languages use different populations, so do not compare their averages as a
matched cross-language result. Only aggregate metadata provenance is released;
no downloaded program source or case records accompany this update.

## Rewrites and qualification

The JS experiment starts from 1,006 qualified alternatives on 150 problems and
adds 12 bounded postorder-fold alternatives across four tree problems. The complete
runtime helper source, callbacks, names and punctuation are counted. The
supported rewrite applies to finite acyclic ordinary trees with the original
numeric constraints; proxies, getters, cycles, arbitrary side effects and
exception-sensitive reflection are outside the contract. It retains O(n) work
and O(h) stack, with different constants; maximum-stack behavior is not proved.
The four original controls and 12 variants pass 1,584 execution checks on 396
independent cases. Across primary/follow-up arms, 1,500 packets independently
decode and their source choices are re-minimized. Generic candidate shortlisting
misses the shared helper; an explicitly frozen helper-priority swap finds the
small tradeoff. This identifies candidate starvation rather than solver failure.

Python independently qualifies 25 problems and 100 variants on 10,260 checks over
2,565 cases, plus 36 Unicode/large-integer probes; 250 packets independently audit.
Rewrites use AST formatting, nonoperational annotation removal, bijective local
binding renaming and optional compact indentation. No algorithm/helper rewrite
is implemented by this baseline. All imports, indentation and wrappers remain
counted. Annotation reflection/tracing/source introspection are outside its
call-level contract. Original 256 control: 3,624 selections; source-only: 3,219;
dictionary-only: 3,247; joint: 2,684. The initial all-variant search plateau is
retained; selected-path proposal repair produces the reported joint successor.
Finite tests are evidence over the declared domain, not universal equivalence.

## Restricted occurrence-flow comparator: negative result

The first completed diagnostic freezes four previously qualified JavaScript
originals, 1,269 UTF-8 bytes, 45 mandatory observed characters and 320 optional
shared substrings. Candidates span 2–32 characters and require support in two
distinct problems. This is an independently written restricted adaptation of
[ConvexTok](https://arxiv.org/html/2605.22821v1), not the original implementation.
The original paper optimizes token count over its own token/alphabet construction;
Gamma's observed-character pool, whole-body exclusions and package objective are
different. No author code was copied; an original-code license was not verified.
The paper is CC BY 4.0. [Casel et al.](https://link.springer.com/article/10.1007/s00224-020-10013-w)
provides the separate one-level grammar-cost context, not a transplanted theorem
for these packets or equivalent-source search.

At 128/7 and 256/8, exact-flow LP/MIP, rounded dictionaries and exact-marginal
add-only greedy all reach 1,021 selections in this pool. Only two noncharacter
entries are useful; 47 entries suffice, with 99.216% character selections. The
restricted package optima are 1,364 bytes at7 bits and 1,490 at8 bits. Full-capacity
Det/Bias rounding stores unused entries and wastes bytes. LP/MIP objective and
constraint checks are numerical to stated tolerances; they are not formal
rational certificates or a bound over all possible strings/equivalent programs.

The run used one thread, 11.71 seconds solver/search time and 87.3 MiB peak RSS,
within its 320-second/1-GiB budget. Twelve enumerable fixture cells and 36 rounding
checks passed; 96 packets and eight flow vectors were independently audited.
The [numeric report](evidence/flow-aggregate.json) retains every arm, lower bound,
incumbent, padding/storage cost and limitation. The result motivates a stronger
candidate-generation comparison, not a claim that Gamma beats ConvexTok.

[model.py](model.py) and [test_model.py](test_model.py) are independent method code
and small synthetic fixtures. With an existing Python environment containing
NumPy and SciPy 1.15.2, run `python test_model.py`; it writes fixture-tests.json
beside the test. No model download is needed. The unchanged decoder/deployment
footprint is not measured here and is not silently included in package bytes.

## Publication and reproducibility boundary

This release contains only docs, method code, synthetic fixtures, aggregates and
[SHA-256 commitments](evidence/private-receipt-hashes.json). Private programs,
inputs, dictionaries, packet selections and detailed source traces are omitted.
Consequently the public package can reproduce synthetic solver checks but cannot
reproduce the corpus measurements by itself. Hashes are not substitute data.
Permitted reproducible corpus artifacts and independent review remain unmet M6
requirements. M1 still requires at least 400 of a frozen 500, median at most 32,
p95 at most 96 and character bits at most 10%, with the exact existing constraints.
Neither language qualifies, and protected data/admission ownership are unchanged.
