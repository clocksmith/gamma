# Coverage-preserving fraction repair: seeds preserved, no improvement

[Freeze](FREEZE.md); [design](DRAFT.md); [metadata](evidence/results.json); [review](REVIEW.md); [reporting note](REPORTING-NOTE.md).

All1,800witness packets independently replay. Warm starts preserve the seed in
both cohorts; neither improves F. Cold selected dictionaries remain worse
after exact minimum-F re-encoding. All four solver calls reach their time
limits with feasible points, zero reported search nodes and no optimality.
This resolves incumbent preservation for this model/budget, not the quality
of the candidate pool or attainability of10%. No candidate is promoted.

complete; independently replayed.

| Cohort | Seed F | Warm F | Cold F | Warm gain | Entries warm | Parent exact bound |
|---|---:|---:|---:|---:|---:|---:|
| R | 110156 | 110156 | 192792 | 0 | 249 | -27266 |
| naming | 94121 | 94121 | 173398 | 0 | 249 | -28259 |

All following seed and feasible-witness rows use exact **minimum-F paths**, with ties by minimum N and then entry IDs. These are not minimum-N encodings. Actions include one Finish per program; median/p90/p95 below count selections only.

| Cohort | Witness | F | C | Character fraction | N | Actions | Median N | p90 N | p95 N | N change vs seed |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| R | seed | 110156 | 13871 | 48.5781% | 28554 | 28854 | 74.5 | 180 | 199 | +0 |
| R | warm | 110156 | 13871 | 48.5781% | 28554 | 28854 | 74.5 | 180 | 199 | +0 |
| R | cold | 192792 | 23560 | 55.0364% | 42808 | 43108 | 112.0 | 268 | 312 | +14254 |
| naming | seed | 94121 | 12122 | 44.7323% | 27099 | 27399 | 71.0 | 166 | 193 | +0 |
| naming | warm | 94121 | 12122 | 44.7323% | 27099 | 27399 | 71.0 | 166 | 193 | +0 |
| naming | cold | 173398 | 21334 | 53.4124% | 39942 | 40242 | 106.0 | 241 | 282 | +12843 |

| Cohort | Witness | Dictionary entries | One-owner entries / share | Near-whole entries / share | Both / share |
|---|---|---:|---:|---:|---:|
| R | seed | 249 | 3 / 1.20% | 0 / 0.00% | 0 / 0.00% |
| R | warm | 249 | 3 / 1.20% | 0 / 0.00% | 0 / 0.00% |
| R | cold | 256 | 5 / 1.95% | 0 / 0.00% | 0 / 0.00% |
| naming | seed | 249 | 3 / 1.20% | 0 / 0.00% | 0 / 0.00% |
| naming | warm | 249 | 3 / 1.20% | 0 / 0.00% | 0 / 0.00% |
| naming | cold | 256 | 6 / 2.34% | 0 / 0.00% | 0 / 0.00% |

Entry-share denominators include every dictionary entry, including unused entries and singletons. One-owner means occurrence in exactly one distinct source, not use by one packet. Near-whole retains the inherited threshold: entry length at least 90% of any containing source. The overlap column is both conditions. These are descriptive size/support statistics, not semantic reuse or legality tests.

Every singleton is charged. F = 10 C − N targets the aggregate character fraction; exact minimum-F paths may use more selections than minimum-N paths.

Lower F or a lower character fraction does not imply fewer actions or better selection quantiles. Signed seed comparisons and the lower_fraction_with_higher_N flag in metadata expose that tradeoff under the same minimum-F policy. No minimum-N counterfactual is computed by this reporting addition.

Only the replayed parent integer bound covers the full substring class. Solver bounds/statuses are numerical restricted-pool evidence.

One-owner and near-whole strings remain relaxation witnesses with semantic reuse unresolved. No M1 candidate or full-class impossibility claim follows. Item 23’s failed qualification remains recorded; unchanged sources reuse only exact item 13 passing hashes.

No validation or protected population was loaded. Sources, vocabularies, q and packets remain private.

The two pools contain2,004/1,779entries and179,677/175,023occurrence arcs.
Whole-job elapsed is1,210.373seconds. Cold solver flow objectives418,322/402,369
are distinct from exact re-encoded dictionary objectives192,792/173,398; the
independent minimum-F path computation improves the returned flows but still
loses to the seeds. Raw numerical restricted-model dual bounds−106,010/−101,526
remain solver evidence. The stronger exact full-class parent bounds−27,266/
−28,259 stay separate and inconclusive.
