# Matched 80-problem literal experiment (frozen design)

Goal v2:2a/2b, Track A development optimization. Frozen **2026-10-21 22:49 EDT**
at parent `8e9593c3f` before any arm ran. [contract.json](contract.json) pins every
input by SHA-256 and states each rule below; this page summarizes it. The design was
committed at `492ff3c6c` before any arm ran; the [outcome](#outcome-2026-10-21) below
was added afterwards. Generated tables are in [RESULTS.md](RESULTS.md).

## Question

On the same 80 exposed development problems, how much does the candidate pool
change literal-vocabulary costs: a readable designed menu, recurrence-mined
fragments, or both? Exact reconstruction is the requirement; coverage, input bits,
storage and fallback reliance are reported side by side, never blended.

## Inputs and evidence classes

- Sources: the 240-row [scale-v2 manifest](../scale-v2/generated/manifest.json); this
  experiment uses its 80 canonical and 80 compact programs.
- Correctness: the stored [scale-v2 receipt](../scale-v2/qualification/report.json)
  and the [fresh-copy rerun](../scale-v2/qualification-rerun-v1/README.md), kept as
  distinct evidence. No candidate source is executed here; every packet must decode,
  through the canonical [codec](../readable-v1/literal_codec.py), to a qualified hash.
- Designed pool: [designed/pool.json](designed/pool.json), owner-approved, 86 canonical
  and 41 compact readable pieces, each witnessed in at least two problems. Queue, set,
  `Map` counting and adjacency pieces have no witnesses in this corpus and are retained
  as exclusions. Readable pieces apply mainly to canonical sources because compact
  sources rename identifiers per problem.
- Component qualification: [qualify_components.cjs](designed/qualify_components.cjs)
  executes 228 contract checks; 123 pieces pass and 4 layout pieces are parse-checked
  only, identically on Mars (node 22.20.0) and Jupiter (node 22.22.1). These are
  author-written checks in minimal contexts, pending independent review; they do not
  establish interchangeable semantics in every program.
- Labels: [labels/labels.json](labels/labels.json) from the pinned LeetCodeDataset
  (revision `215604ae`, both file hashes verified): 69 Easy, 9 Medium, 2 Hard, with a
  primary-tag precedence frozen in [extract_labels.py](labels/extract_labels.py).

## Arms

| Kind | Arms | What varies |
| --- | --- | --- |
| Fixed | designed / mined / combined x 128 / 256 x canonical / compact (12) | candidate pool only |
| Joint | designed / mined / combined x 128 / 256 (6) | per-problem canonical or compact choice, from both fixed starts |
| Control | unchanged scale-v2 search, canonical and compact | must reproduce stored marginal results |

Every arm shares the charged 96-entry ASCII/newline fallback, exact shortest
segmentation, measured-gain admission with reclaim and bounded swaps, and one shortlist
ranking identical across pools. Fixed trajectories are capped at 2,200 exact trials
(300 s safety limit); 128 and 256 are snapshots of one trajectory. Joint arms use
joint-v1 bounds per start and preserve the best fixed incumbent; their inherited
fixed-search cost is disclosed, not hidden. The search has no random seeds.

## Predictions (stated before results)

1. On canonical sources, combined uses no more selections than mined at each size.
2. Designed-only uses more selections than mined at each size; the gap is the measured
   cost of a readable-only menu.
3. Fewer designed entries are admitted in compact combined arms than in canonical ones.
4. Each joint arm uses no more selections than its best fixed arm.

## Reproduce

From this directory with Python 3 and Node 22 (no downloads):

```sh
python3 -B -m unittest test_run -v
node designed/qualify_components.cjs designed/pool.json /tmp/receipt.json
python3 -B run.py --output run-v1
```

`run.py` refuses to start if any pinned input changed and refuses an existing output.
`make_contract.py` wrote `contract.json` once; `designed/build_pool.py` and
`labels/extract_labels.py` (run on 128 against the pinned raw files) rebuild their
outputs and also refuse to overwrite.

## Outcome (2026-10-21)

Run on Mars (Python 3.14.2) in 268 s; all 14 jobs completed and no arm reached its time
limit, so results are fixed by the trial caps. Every one of the 18 arms covers **80/80**
programs, each packet verified against its qualified hash by the canonical codec. The
unchanged scale-v2 control reproduced all four stored results with identical
dictionaries (canonical 16,932 / 7,866; compact 10,155 / 6,413 selections).
[RESULTS.md](RESULTS.md) has every metric; [results.json](results.json) adds per-tag and
primary-tag breakdowns, peak memory and inherited joint search costs;
[preparation.json](preparation.json) records preparation costs.

| Selections | designed | mined | combined | joint (same pool) |
| --- | ---: | ---: | ---: | ---: |
| canonical, 128 | 28,607 | 20,063 | 18,940 | - |
| canonical, 256 | 25,720 | 10,906 | 10,735 | - |
| compact, 128 | 11,794 | 10,950 | 10,659 | designed 11,754 / mined 10,670 / combined 10,659 |
| compact, 256 | 11,593 | 7,472 | 7,303 | designed 11,481 / mined 7,468 / combined 7,302 |

Predictions:

1. **Holds.** Combined uses fewer selections than mined on canonical source (-5.6% at
   128, -1.6% at 256), and also on compact (-2.7%, -2.3%).
2. **Holds.** A designed-only readable menu costs 1.43x / 2.36x mined selections on
   canonical source and 1.08x / 1.55x on compact. Designed-only 256-entry arms use more
   input bits than their 128-entry arms (canonical 205,760 vs 200,249; compact 92,744 vs
   82,558): a pool of 86 or 41 pieces cannot pay for the eighth bit.
3. **Fails as measured.** Compact combined arms contain more designed-piece matches
   than canonical ones (10 vs 5 at 128, 23 vs 12 at 256). The measure classifies entries
   by text, not by which proposer found them: short compact pieces such as `=0;` and
   `if(` are also found by mining, and mined-only arms contain such matches too.
4. **Holds.** Joint arms never lose the fixed incumbent; improvements are 0.0-2.6%.
   Every joint arm chose compact source for all 80 problems, so gains come from
   vocabulary moves, not source switching.

**Ranking caveat.** The shared shortlist ranking frozen to keep pools comparable is
weaker than scale-v2's span-count ranking: the matched mined arms use 7.8-38.6% more
selections than the stored scale-v2 results, and the best matched arm (joint combined
256, 7,302) does not improve on the stored 6,413. Pool comparisons are valid under this
ranking only; whether the designed pool's small gain survives under a stronger ranking is
untested, because span-count ranking does not apply to designed pieces.

**Failure inspection.** The same programs are costliest in every arm: #1046 (a
hand-written heap, 634 selections and 76% single characters even in the best arm), #4
(the only Hard binary search), #824, #976, #844 and #748. Heap operations occur in too
few problems to meet the two-witness rule. Designed canonical arms spell out recurring
names (`result`, `items`, `values`) and statement tails (`) {`, `];`); complete readable
statements are too coarse to recur. Designed compact arms spell out declarations
(`let b`, `const b`) and block endings, which cannot be identifier-free pieces.

Proposed next steps, not run: make shortlist ranking an explicit matched factor in a new
frozen experiment; test a finer readable policy (names and statement tails) as a separate
arm; extend heap and queue support only once more problems witness it. Component checks
still await independent review; nothing here changes BITS or a live dictionary.

## Limits

All 80 problems are exposed development material, so nothing here is a generalization
or autonomous-composition result. Results do not establish human learnability,
readability or fluency. Macros, cursor actions, six-bit capacity tests, BITS changes
and protected problems are out of scope. Promotion requires a predeclared matched
confirmation and independent review.
