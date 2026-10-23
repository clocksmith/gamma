# Exact minimum character fraction for fixed dictionaries

[Freeze](FREEZE.md) pushed as `c956bb322`; [review/run receipt](REVIEW.md); [evidence](evidence/results.json). Private source, dictionary and sequence artifacts remain private.

This diagnostic minimizes the aggregate ratio C/N over every segmentation of each fixed source/codebook pair. It uses consumed development sources to choose separate coefficients for each split. It is not a transferable fitted encoder, a new candidate or a change to previous canonical results.

None of these fixed validation source/codebook pairs can reach the 10% character-fraction gate under any segmentation. The exact optima and their additional action costs are below; changing sources or dictionaries is outside this conclusion.

| Seed | Split | Exact minimum C/N | Minimum fraction | 10% reachable? | Actions at optimum | Extra actions vs canonical | Iterations | Independent minimum sum |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| R128 | fit | 16781/21433 | 78.30% | False | 43166 | 1182 | 2 | 0 |
| R128 | validation | 3733/4801 | 77.75% | False | 14503 | 389 | 2 | 0 |
| R256 | fit | 4693/9801 | 47.88% | False | 29703 | 3295 | 3 | 0 |
| R256 | validation | 4921/10119 | 48.63% | False | 10219 | 1171 | 3 | 0 |
| naming256 | fit | 1238/2809 | 44.07% | False | 28390 | 3340 | 2 | 0 |
| naming256 | validation | 4218/9605 | 43.91% | False | 9705 | 1201 | 2 | 0 |

At the final p/q, every path has summed transformed cost q*C-p*N at least zero, and the decoded witness attains zero. A separate forward DAG replays that minimum with integer arithmetic. The witness also has the fewest total selections among paths attaining this ratio. This proves only the fixed-source, fixed-dictionary fraction optimum; other dictionaries or source rewrites are outside the certificate.

| Seed | Policy | Split | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |
| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| R128 | canonical | fit | 41684 | 107.0/256/303/1173 | 10/128 | 41984 | 33021/79.22% | 49725 | 62735 |
| R128 | canonical | validation | 14014 | 103.5/267/320/716 | 5/45 | 14114 | 11025/78.67% | 17225 | 30235 |
| R128 | min_char | fit | 41684 | 107.0/256/303/1173 | 10/128 | 41984 | 33021/79.22% | 49725 | 62735 |
| R128 | min_char | validation | 14014 | 103.5/267/320/716 | 5/45 | 14114 | 11025/78.67% | 17225 | 30235 |
| R128 | min_fraction | fit | 42866 | 110.5/262/308/1183 | 6/117 | 43166 | 33562/78.30% | 50762 | 63772 |
| R128 | min_fraction | validation | 14403 | 107.5/268/322/719 | 4/42 | 14503 | 11199/77.75% | 17565 | 30575 |
| R256 | canonical | fit | 26108 | 68.0/162/188/930 | 48/216 | 26408 | 14115/54.06% | 40615 | 53625 |
| R256 | canonical | validation | 8948 | 63.5/169/211/501 | 13/69 | 9048 | 4934/55.14% | 15255 | 28265 |
| R256 | min_char | fit | 26137 | 68.0/162/188/930 | 48/216 | 26437 | 13871/53.07% | 40644 | 53654 |
| R256 | min_char | validation | 8960 | 63.5/169/211/501 | 13/69 | 9060 | 4850/54.13% | 15267 | 28277 |
| R256 | min_fraction | fit | 29403 | 76.5/185/205/964 | 30/196 | 29703 | 14079/47.88% | 43910 | 56920 |
| R256 | min_fraction | validation | 10119 | 71.0/185/227/558 | 7/62 | 10219 | 4921/48.63% | 16426 | 29436 |
| naming256 | canonical | fit | 24750 | 64.0/150/176/886 | 52/222 | 25050 | 12328/49.81% | 39270 | 52280 |
| naming256 | canonical | validation | 8404 | 61.5/154/199/477 | 17/70 | 8504 | 4193/49.89% | 14724 | 27734 |
| naming256 | min_char | fit | 24776 | 64.5/150/176/886 | 52/222 | 25076 | 12122/48.93% | 39296 | 52306 |
| naming256 | min_char | validation | 8412 | 61.5/154/199/477 | 17/70 | 8512 | 4126/49.05% | 14732 | 27742 |
| naming256 | min_fraction | fit | 28090 | 73.0/175/194/918 | 30/202 | 28390 | 12380/44.07% | 42610 | 55620 |
| naming256 | min_fraction | validation | 9605 | 69.5/167/215/530 | 8/64 | 9705 | 4218/43.91% | 15925 | 28935 |

All rows cover and reuse exact-source qualification for 300 fit or 100 validation programs. Every literal selection, one Finish, unchanged seven/eight-bit width, dictionary, 41-byte frame and padding are charged. Full runtime installation storage is unmeasured. Lowering the fraction can consume more learned-symbol selections without removing character selections; the action and storage cost is part of the result.

| Seed | Minimum-ratio validation contrast | Extra actions | Action change | Character-code delta | Fraction change (percentage points) |
| --- | --- | ---: | ---: | ---: | ---: |
| R128 | vs canonical | 389 | 2.76% | 174 | -0.92 |
| R128 | vs min_char | 389 | 2.76% | 174 | -0.92 |
| R256 | vs canonical | 1171 | 12.94% | -13 | -6.51 |
| R256 | vs min_char | 1159 | 12.79% | 71 | -5.50 |
| naming256 | vs canonical | 1201 | 14.12% | 25 | -5.98 |
| naming256 | vs min_char | 1193 | 14.02% | 92 | -5.13 |

| Prediction | Met |
| --- | --- |
| F1 | True |
| F2 | True |
| F3 | True |
| F4 | True |
| F5 | True |

All 3,600 packets and six certificates replay during reporting. Measured run time: 2.52 seconds. Five focused tests include100 exhaustive paired-text examples and denominator/tie/cap checks. Qualification is hash reuse, not fresh execution.

No promotion or canonical encoder change. Component intent preserved; no M1 thresholds, production behavior or owner gates changed. No training, protected opening, source publication, deployment, human study or ledger/catalog/claim write.

Rebuild: `python3 -B projects/algorithm_solver/literals/fraction-certificate-v1/report.py --run /private/fraction-certificate/run-v1 --work /private/literal-admission500-v1`.
