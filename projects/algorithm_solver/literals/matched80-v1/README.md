# Matched 80-problem literal experiment (frozen design)

Goal v2:2a/2b, Track A development optimization. Frozen **2026-10-21 22:49 EDT**
at parent `8e9593c3f` before any arm ran. [contract.json](contract.json) pins every
input by SHA-256 and states each rule below; this page summarizes it. Results go in
`run-v1/` and a separate report; this commit contains no outcomes.

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

## Limits

All 80 problems are exposed development material, so nothing here is a generalization
or autonomous-composition result. Results do not establish human learnability,
readability or fluency. Macros, cursor actions, six-bit capacity tests, BITS changes
and protected problems are out of scope. Promotion requires a predeclared matched
confirmation and independent review.
