# Character-aware dictionary objectives

[Freeze](FREEZE.md) pushed as `bc14c1331`; [trial-cap amendment](AMENDMENT-1.md) pushed as `5860ab34d`; [review/run receipt](REVIEW.md), [evidence](evidence/results.json). Private source, dictionary, sequence and trace artifacts remain private.

Ready pair selected by the frozen ranking: **['seed', 'canonical']**. This is consumed-development readiness against original R/L-R256, not independent confirmation or M1. All sources are fixed to item13 scope_joint256; its selection itself used dev-val outcomes.

The strongest penalty lowers validation character codes4129→3876 (6.13%) while actions rise8504→8944 (5.17%). The registered10%character reduction within5%extra actions is not achieved. w1 still passes original-control readiness but uses8more actions than the seed. The frozen ranking retains seed/canonical; its tie ordering does not prefer fewer characters once action/package costs tie. No new action-improving candidate is selected.

Integer objective4N+wC uses penalties w=0,1,4,16. Positive-weight views can use more actions for fewer character codes. Canonical and shortest_min_char views compare dictionaries under common encoders; weighted views compare the combined dictionary-plus-weighted-encoder procedure. The seed weighted view hasw0, so positive-weight versus seed weighted is not a same-policy contrast. All input charges and M1 gates remain unchanged.

| Dictionary | Encoder | Split | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Character codes | Character fraction | Package |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| seed | canonical | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12328 | 49.81% | 39270 |
| seed | canonical | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 14724 |
| seed | shortest_min_char | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12139 | 49.05% | 39270 |
| seed | shortest_min_char | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4129 | 49.13% | 14724 |
| seed | weighted | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12139 | 49.05% | 39270 |
| seed | weighted | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4129 | 49.13% | 14724 |
| w0 | canonical | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12328 | 49.81% | 39270 |
| w0 | canonical | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 14724 |
| w0 | shortest_min_char | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12139 | 49.05% | 39270 |
| w0 | shortest_min_char | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4129 | 49.13% | 14724 |
| w0 | weighted | fit | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12139 | 49.05% | 39270 |
| w0 | weighted | validation | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4129 | 49.13% | 14724 |
| w1 | canonical | fit | 24764 | 64.0 | 151 | 176 | 886 | 52/223 | 25064 | 12248 | 49.46% | 39265 |
| w1 | canonical | validation | 8412 | 61.5 | 154 | 201 | 479 | 17/70 | 8512 | 4177 | 49.66% | 14713 |
| w1 | shortest_min_char | fit | 24764 | 64.0 | 151 | 176 | 886 | 52/223 | 25064 | 12059 | 48.70% | 39265 |
| w1 | shortest_min_char | validation | 8412 | 61.5 | 154 | 201 | 479 | 17/70 | 8512 | 4113 | 48.89% | 14713 |
| w1 | weighted | fit | 24764 | 64.0 | 151 | 176 | 886 | 52/223 | 25064 | 12059 | 48.70% | 39265 |
| w1 | weighted | validation | 8412 | 61.5 | 154 | 201 | 479 | 17/70 | 8512 | 4113 | 48.89% | 14713 |
| w4 | canonical | fit | 25084 | 65.0 | 154 | 179 | 900 | 48/221 | 25384 | 11826 | 47.15% | 39504 |
| w4 | canonical | validation | 8559 | 62.0 | 153 | 202 | 478 | 15/69 | 8659 | 4103 | 47.94% | 14779 |
| w4 | shortest_min_char | fit | 25084 | 65.0 | 154 | 179 | 900 | 48/221 | 25384 | 11511 | 45.89% | 39504 |
| w4 | shortest_min_char | validation | 8559 | 62.0 | 153 | 202 | 478 | 15/69 | 8659 | 4002 | 46.76% | 14779 |
| w4 | weighted | fit | 25086 | 65.0 | 154 | 179 | 900 | 48/221 | 25386 | 11507 | 45.87% | 39506 |
| w4 | weighted | validation | 8559 | 62.0 | 153 | 202 | 478 | 15/69 | 8659 | 4002 | 46.76% | 14779 |
| w16 | canonical | fit | 25847 | 68.0 | 157 | 185 | 909 | 43/216 | 26147 | 11445 | 44.28% | 40183 |
| w16 | canonical | validation | 8842 | 63.0 | 158 | 202 | 493 | 13/68 | 8942 | 4043 | 45.72% | 14978 |
| w16 | shortest_min_char | fit | 25847 | 68.0 | 157 | 185 | 909 | 43/216 | 26147 | 10909 | 42.21% | 40183 |
| w16 | shortest_min_char | validation | 8842 | 63.0 | 158 | 202 | 493 | 13/68 | 8942 | 3877 | 43.85% | 14978 |
| w16 | weighted | fit | 25869 | 68.0 | 157 | 185 | 909 | 42/216 | 26169 | 10895 | 42.12% | 40205 |
| w16 | weighted | validation | 8844 | 63.0 | 158 | 202 | 493 | 13/68 | 8944 | 3876 | 43.83% | 14980 |

Each row decodes and reuses exact-source qualification for300fit/100validation programs. One Finish each, unchanged8-bit width, dictionary/header/payload/padding charged. Decoder-inclusive packages and offline tooling storage are in evidence; complete installed runtime footprint is unmeasured.

| Dictionary | Encoder | Better/same/worse vs original | Ready | Failed predicates |
| --- | --- | --- | --- | --- |
| seed | canonical | 75/21/4 | True | None |
| seed | shortest_min_char | 75/21/4 | True | None |
| seed | weighted | 75/21/4 | True | None |
| w0 | canonical | 75/21/4 | True | None |
| w0 | shortest_min_char | 75/21/4 | True | None |
| w0 | weighted | 75/21/4 | True | None |
| w1 | canonical | 75/20/5 | True | None |
| w1 | shortest_min_char | 75/20/5 | True | None |
| w1 | weighted | 75/20/5 | True | None |
| w4 | canonical | 58/16/26 | False | actions_5_percent, improved_60, worsened_at_most_25 |
| w4 | shortest_min_char | 58/16/26 | False | actions_5_percent, improved_60, worsened_at_most_25 |
| w4 | weighted | 58/16/26 | False | actions_5_percent, improved_60, worsened_at_most_25 |
| w16 | canonical | 45/7/48 | False | actions_5_percent, improved_60, worsened_at_most_25 |
| w16 | shortest_min_char | 45/7/48 | False | actions_5_percent, improved_60, worsened_at_most_25 |
| w16 | weighted | 44/8/48 | False | actions_5_percent, improved_60, worsened_at_most_25 |

| Dictionary | Common encoder | Validation actions delta vs seed | Character-code delta | Better/same/worse |
| --- | --- | ---: | ---: | --- |
| seed | canonical | 0 | 0 | 0/100/0 |
| seed | shortest_min_char | 0 | 0 | 0/100/0 |
| w0 | canonical | 0 | 0 | 0/100/0 |
| w0 | shortest_min_char | 0 | 0 | 0/100/0 |
| w1 | canonical | 8 | -16 | 5/87/8 |
| w1 | shortest_min_char | 8 | -16 | 5/87/8 |
| w4 | canonical | 155 | -90 | 5/24/71 |
| w4 | shortest_min_char | 155 | -127 | 5/24/71 |
| w16 | canonical | 438 | -150 | 6/8/86 |
| w16 | shortest_min_char | 438 | -252 | 6/8/86 |

| Dictionary | Initial objective | Final objective | Fit N/C | Trials | Moves | Stop | Search seconds |
| --- | ---: | ---: | --- | ---: | ---: | --- | ---: |
| seed | 99000 | 99000 | 24750/12139 | 1 | 0 | fixed_seed | 0.02 |
| w0 | 99000 | 99000 | 24750/12139 | 907 | 0 | local_optimum | 6.51 |
| w1 | 111139 | 111115 | 24764/12059 | 1813 | 1 | local_optimum | 16.40 |
| w4 | 147556 | 146372 | 25086/11507 | 5437 | 5 | local_optimum | 58.55 |
| w16 | 293056 | 277796 | 25869/10895 | 12000 | 13 | trial_limit | 125.21 |

Local/capped stops are bounded search outcomes, not global optimality. The reported Pareto frontier compares actions, absolute character codes and package only; it does not establish median,p95 or fraction gates. Equal vectors remain separate witnesses. Frontier: seed/shortest_min_char, seed/weighted, w0/shortest_min_char, w0/weighted, w1/shortest_min_char, w1/weighted, w4/shortest_min_char, w4/weighted, w16/shortest_min_char, w16/weighted.

| Prediction | Met |
| --- | --- |
| W1 | True |
| W2 | True |
| W3 | False |
| W4 | True |
| W5 | True |

Measured complete run wall time: 127.17 seconds. Seven focused tests passed, including100 exhaustive examples under four weights, cache parity and exact cap retention. All6000packet decodes replay during reporting; source qualification is unchanged hash-bound reuse, not new execution evidence.

Owner gate: any selected pair needs a separately approved confirmation population and frozen dictionary/encoder before protected access. Candidate artifacts: character-objective/run-v1/<arm>, with dictionary/fit-seal hashes and policy identified in evidence. Training, held-out/protected opening, publication, BITS changes, human studies and independent confirmation remain gated. No ledger/catalog/claim write or production/canonical codec change. Component intent preserved.

Rebuild: `python3 -B projects/algorithm_solver/literals/character-objective-v1/report.py --run /private/character-objective/run-v1`.
