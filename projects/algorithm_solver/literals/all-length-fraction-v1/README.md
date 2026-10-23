# All-length shared-pool character-fraction certificate

[Freeze](FREEZE.md); [prelaunch amendment](AMENDMENT-1.md); [metadata evidence](evidence/results.json). Private pools, multipliers, dictionaries, sources and packets are not published.

This diagnostic bounds F=10C−N over all segmentations and all capacity-feasible dictionaries in each stated pool. A strictly positive integer lower bound excludes a 10% character fraction for that complete 300-program fit cohort/model. A nonpositive bound is inconclusive unless a decoded feasible witness reaches F<=0. These are fixed-source/pool bounds, not M1-wide impossibility or source-rewriting conclusions. No validation source values were loaded.

| Cohort | Model | Pool / occurrence edges | Exact numerator / denominator | Integer lower bound | Best feasible F | Excludes 10% | Iterations / stop / seconds |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| R | flex256 | 308304/1370583 | 22195638563/1000000 | 22196 | 110156 | True | 2000/iteration_limit/462.67 |
| naming | flex256 | 291196/1319319 | 13724320177/1000000 | 13725 | 94121 | True | 2000/iteration_limit/450.76 |

The pool includes shared substrings of every length >= 2, plus pinned seed learned entries and 96 optional characters, excluding fit whole-source/body bans. flex256 permits any 256 entries and relaxes item 24 reserved-character constraints. Bounds do not cover arbitrary one-owner strings beyond seed exceptions, banned strings, source alternatives, arbitrary program subsets, quantile requirements, held-out data or 400-of-500 coverage. Both pools were independently rebuilt from pinned fit inputs before certificate replay. Exact-string bans still permit near-whole shared strings such as a body minus one character. This enlarged relaxation makes a positive lower bound valid, but its witnesses are not claims of M1-legal representations.

| Cohort/model | Witness | Entries / character entries | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | F | Raw / decoder-source package |
| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | --- |
| R/flex256 | best | 256/96 | 28554 | 74.5/180/199/964 | 37/199 | 28854 | 13871/48.58% | 110156 | 43061/56071 |
| R/flex256 | seed | 256/96 | 28554 | 74.5/180/199/964 | 37/199 | 28854 | 13871/48.58% | 110156 | 43061/56071 |
| naming/flex256 | best | 256/96 | 27099 | 71.0/166/193/918 | 38/206 | 27399 | 12122/44.73% | 94121 | 41619/54629 |
| naming/flex256 | seed | 256/96 | 27099 | 71.0/166/193/918 | 38/206 | 27399 | 12122/44.73% | 94121 | 41619/54629 |

Witnesses minimize F within their own dictionaries, then N and lexicographic IDs. This is not minimum ratio or canonical minimum-N segmentation. Every stored packet decodes exactly; one Finish, eight-bit selections, 41-byte frames, full dictionary and per-program/amortized storage count. Qualified source hashes are reused from item 13; no fresh runtime qualification or autonomous solving is claimed. Item 23 retained its later unchanged-source exit 137 failure.

| Cohort/model | Primal proposals / coverage failures | Legacy seed pool additions | Max entry length | Pool / total arm seconds |
| --- | --- | ---: | ---: | ---: |
| R/flex256 | 240/240 | 0 | 326 | 0.49/466.59 |
| naming/flex256 | 240/240 | 0 | 322 | 0.48/454.58 |

Generated witnesses are retained separately even when worse than the seed; missing optional coverage proposals are discarded as infeasible and counted, without repair. Floating bounds guide search only. Quantized nonnegative multipliers, integer shortest paths, top-capacity entry sums and separate forward replay establish each reported certificate.

| Prediction | Met |
| --- | --- |
| A1 | True |
| A2 | True |
| A3 | False |
| A4 | True |
| A5 | True |

1200 final witness packets decode; total run wall time 466.86 seconds. Six pool tests include 500 exhaustive shared-pool instances and 300 suffix-array/LCP comparisons; four occurrence tests compare 150 old/new graphs and 100 brute-force match sets; five unchanged dual tests include 60 dictionary-bound and 60 path instances; compile/import/help and identity checks passed. Reporting rebuilds both pools, verifies pinned qualification source hashes, and replays exact certificates with the independent Aho-Corasick forward matcher, all witness packets and full cost aggregates without optimization.

No selected successor or readiness decision. Component intent preserved; canonical decoder and production boundaries unchanged. Training, held-out/protected opening, independent confirmation, publishing private sources, deployment and human studies remain owner-gated. Full installed runtime storage remains unmeasured.

Rebuild with the pinned NumPy Python: `python -B projects/algorithm_solver/literals/all-length-fraction-v1/report.py --run /private/all-length-fraction/run-v1 --work /private/literal-admission500-v1`.
