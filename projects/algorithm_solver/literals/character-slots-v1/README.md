# Coverage-constrained character-slot selection

[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Private sources, dictionaries and packets remain private.

Selected successor: **optional**. Optional retains 92 character entries and covers 100/100 validation programs. Adaptive consumed-development evidence; no M1 qualification or independent confirmation.

| Arm | Split | Encoded / source-qualified | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |
| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| seed | fit | 300/300 | 24750 | 64.0/150/176/886 | 52/222 | 25050 | 12328/49.81% | 39270 | 52280 |
| seed | validation | 100/100 | 8404 | 61.5/154/199/477 | 17/70 | 8504 | 4193/49.89% | 14724 | 27734 |
| fixed96 | fit | 300/300 | 24344 | 65.0/146/176/887 | 53/229 | 24644 | 12289/50.48% | 39283 | 52293 |
| fixed96 | validation | 100/100 | 8328 | 62.5/154/200/503 | 16/72 | 8428 | 4203/50.47% | 15067 | 28077 |
| optional | fit | 300/300 | 24167 | 64.0/142/181/882 | 54/229 | 24467 | 12063/49.92% | 39129 | 52139 |
| optional | validation | 100/100 | 8236 | 61.5/154/197/476 | 17/74 | 8336 | 4085/49.60% | 14998 | 28008 |

Qualification is reused by exact source hash from item15 seed_fixed_seed, not new execution. Every encoded packet is independently decoded. Partial totals exclude unencodable rows and are not complete-cohort gains; failures remain regressions. One Finish, eight-bit selections, complete dictionary and 41-byte frames are charged; per-program and amortized costs are in evidence.

| Arm | Comparator | Full-cohort action delta | Better/same/worse | Failed checks |
| --- | --- | ---: | --- | --- |
| seed | R | -544 | 75/21/4 | None |
| seed | seed | 0 | 0/100/0 | actions_lower |
| seed | fixed96 | 76 | 32/43/25 | actions_lower |
| fixed96 | R | -620 | 70/20/10 | None |
| fixed96 | seed | -76 | 25/43/32 | worsened_at_most_25, median_nonincrease, fallback_nonincrease |
| fixed96 | fixed96 | 0 | 0/100/0 | actions_lower |
| optional | R | -712 | 74/21/5 | None |
| optional | seed | -168 | 33/53/14 | None |
| optional | fixed96 | -92 | 31/63/6 | None |

| Arm | Character / learned entries | Reserved unseen / observed chars | Fit start/end | Accepted/attempted | Stop/seconds |
| --- | --- | --- | --- | --- | --- |
| seed | 96/160 | 7/89 | Pinned | 0/0 | Pinned |
| fixed96 | 96/160 | 7/89 | 24750/24344 | 5/12 | move_limit/1359.99 |
| optional | 92/164 | 7/85 | 24750/24167 | 5/12 | move_limit/1261.98 |

The optional arm frees observed characters only; all fit-unseen characters remain reserved. Exact selected-entry flow has no free character arcs. Both arms use the same bounded repair budget and fixed sources, with no polish or validation repair. Status0 concerns only a restricted candidate repair; time-limited feasible results are not optimality certificates.

| Prediction | Met |
| --- | --- |
| A1 | True |
| A2 | True |
| A3 | True |
| A4 | True |
| A5 | True |
| A6 | False |

1200 final packets decoded; run wall time 1361.45 seconds. Four synthetic tests include40exhaustive mixed-entry MILPs; compile/import/help and pinned identity checks passed. Reporting replays all accepted dictionaries and final packets without refitting.

Item23 retains its unchanged-source1079 exit137 failure. Item15 was independently frozen and launched before that outcome; reusing its passing receipt here does not revise or retry item23. Finite development qualification is not universal equivalence.

Component intent preserved; canonical codec and production boundaries unchanged. No hidden escape or missing coverage repair. Decoder source inventory is charged separately; complete installed runtime footprint remains unmeasured. Protected opening, confirmation, deployment, training, publication and human studies remain owner-gated.

Rebuild: `python3 -B projects/algorithm_solver/literals/character-slots-v1/report.py --run /private/character-slots/run-v1 --work /private/literal-admission500-v1`.
