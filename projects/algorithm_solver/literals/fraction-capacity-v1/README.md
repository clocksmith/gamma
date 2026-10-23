# Capacity-aware character-fraction certificate

[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Private pools, multipliers, dictionaries, sources and packets are not published.

This diagnostic bounds F=10C−N over all segmentations and all capacity-feasible dictionaries in each stated pool. A strictly positive integer lower bound excludes a10%character fraction for that complete300-program fit cohort/model. A nonpositive bound is inconclusive unless a decoded feasible witness reaches F<=0. These are fixed-source/pool bounds, not M1-wide impossibility or source-rewriting conclusions. No validation source values were loaded.

| Cohort | Model | Pool / occurrence edges | Exact numerator / denominator | Integer lower bound | Best feasible F | Excludes10% | Iterations / stop / seconds |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| R | fixed96 | 223244/1118337 | 33594937177/1000000 | 33595 | 109717 | True | 2000/iteration_limit/495.96 |
| R | flex256 | 223340/1194444 | 20730350858/1000000 | 20731 | 110156 | True | 2000/iteration_limit/491.84 |
| naming | fixed96 | 212544/1082251 | 18291911339/1000000 | 18292 | 94121 | True | 2000/iteration_limit/638.45 |
| naming | flex256 | 212640/1158284 | 12775517446/1000000 | 12776 | 94121 | True | 2000/iteration_limit/638.22 |

The pool is shared2–64byte strings plus pinned seed learned entries, with fit whole-source/body exclusions. fixed96 reserves96characters and permits160learned entries. flex256 permits any256entries from learned pool plus all96characters; it relaxes item24 reserved-character constraints. Bounds do not cover excluded/longer/unshared strings beyond seed exceptions, source alternatives, arbitrary program subsets, quantile requirements, held-out data or400of500coverage.

| Cohort/model | Witness | Entries / character entries | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | F | Raw / decoder-source package |
| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |
| R/fixed96 | best | 256/96 | 43563 | 118.0/252/295/1146 | 2/112 | 43863 | 15328/35.19% | 109717 | 57347/70357 |
| R/fixed96 | generated | 256/96 | 43563 | 118.0/252/295/1146 | 2/112 | 43863 | 15328/35.19% | 109717 | 57347/70357 |
| R/fixed96 | seed | 256/96 | 28554 | 74.5/180/199/964 | 37/199 | 28854 | 13871/48.58% | 110156 | 43061/56071 |
| R/flex256 | best | 256/96 | 28554 | 74.5/180/199/964 | 37/199 | 28854 | 13871/48.58% | 110156 | 43061/56071 |
| R/flex256 | seed | 256/96 | 28554 | 74.5/180/199/964 | 37/199 | 28854 | 13871/48.58% | 110156 | 43061/56071 |
| naming/fixed96 | best | 256/96 | 27099 | 71.0/166/193/918 | 38/206 | 27399 | 12122/44.73% | 94121 | 41619/54629 |
| naming/fixed96 | generated | 256/96 | 44111 | 121.0/253/292/1080 | 1/105 | 44411 | 14253/32.31% | 98419 | 57879/70889 |
| naming/fixed96 | seed | 256/96 | 27099 | 71.0/166/193/918 | 38/206 | 27399 | 12122/44.73% | 94121 | 41619/54629 |
| naming/flex256 | best | 256/96 | 27099 | 71.0/166/193/918 | 38/206 | 27399 | 12122/44.73% | 94121 | 41619/54629 |
| naming/flex256 | seed | 256/96 | 27099 | 71.0/166/193/918 | 38/206 | 27399 | 12122/44.73% | 94121 | 41619/54629 |

Witnesses minimizeF within their own dictionaries, then N and lexicographic IDs. This is not minimum ratio or canonical minimumN segmentation. Every stored packet decodes exactly; one Finish, eight-bit selections,41-byte frames, full dictionary and per-program/amortized storage count. Qualified source hashes are reused from item13; no fresh runtime qualification or autonomous solving is claimed. Item23 retained its later unchanged-source exit137 failure.

| Cohort/model | Primal proposals / coverage failures | Legacy seed pool additions | Total arm seconds |
| --- | --- | ---: | ---: |
| R/fixed96 | 240/0 | 0 | 505.39 |
| R/flex256 | 240/240 | 0 | 500.93 |
| naming/fixed96 | 240/0 | 0 | 647.31 |
| naming/flex256 | 240/240 | 0 | 649.67 |

Generated witnesses are retained separately even when worse than the seed; missing optional coverage proposals are discarded as infeasible and counted, without repair. Floating bounds guide search only. Quantized nonnegative multipliers, integer shortest paths, top-capacity entry sums and separate forward replay establish each reported certificate.

| Prediction | Met |
| --- | --- |
| B1 | True |
| B2 | True |
| B3 | False |
| B4 | True |
| B5 | True |
| B6 | True |

3000 final witness packets decode; total run wall time 650.07 seconds. Five tests include60exhaustive dictionary-bound instances and60exhaustive path comparisons; compile/import/help and identity checks passed. Reporting replays all exact certificates and witnesses without optimization.

No selected successor or readiness decision. Component intent preserved; canonical decoder and production boundaries unchanged. Training, held-out/protected opening, independent confirmation, publishing private sources, deployment and human studies remain owner-gated. Full installed runtime storage remains unmeasured.

Rebuild with the pinned NumPy Python: `python -B projects/algorithm_solver/literals/fraction-capacity-v1/report.py --run /private/fraction-capacity/run-v1 --work /private/literal-admission500-v1`.
