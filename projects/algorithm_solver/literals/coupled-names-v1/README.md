# Dictionary-guided coupled names

[Freeze](FREEZE.md) pushed as `29442036f`; [review and run receipt](REVIEW.md). [Evidence](evidence/results.json) contains sanitized metadata only. Private sources, dictionaries, mappings, traces and cases remain private.

Selected incremental successor: **none**. Readiness is consumed-development input evidence, not M1 or independent confirmation. This is offline optimization supplied with a known source; it does not establish autonomous composition.

Coupled naming saves seven validation actions versus the seed and ordinary continuation (5 better/95 same/0 worse). Both coupled arms remain ready versus the original control but fail the incremental successor gate: absolute character codes decline4193→4191 while fraction rises49.89%→49.91% because total selections fall faster. No successor is selected; the frozen fraction rule is unchanged.

Historical control/seed are hash-bound replays from item13. The seed was selected by item13’s frozen ranking using dev-val outcomes; further gains are adaptive development evidence, not an independent generalization estimate. Ordinary arms continue naming; coupled arms add simultaneous proposals and additional scoring work. Fixed comparisons share a dictionary; joint comparisons follow different complete source/dictionary trajectories. Validation uses original/seed choices and a frozen naming policy under fit-sealed dictionaries. No validation refit or test-driven repair.

| Arm | Split | Decoded | Qualified | Selections | Median | p90 | p95 | Worst | <=32/96 | Actions | Character codes | Character fraction | Raw package |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| control | fit | 300 | 300 | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 14115 | 54.06% | 40615 |
| control | validation | 100 | 100 | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 4934 | 55.14% | 15255 |
| seed | fit | 300 | 300 | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 12328 | 49.81% | 39270 |
| seed | validation | 100 | 100 | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 14724 |
| ordinary | fit | 300 | 300 | 24714 | 64.0 | 150 | 176 | 886 | 52/222 | 25014 | 12258 | 49.60% | 39234 |
| ordinary | validation | 100 | 100 | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 14724 |
| coupled | fit | 300 | 300 | 24691 | 64.0 | 149 | 176 | 886 | 52/222 | 24991 | 12240 | 49.57% | 39211 |
| coupled | validation | 100 | 100 | 8397 | 61.5 | 154 | 199 | 477 | 17/70 | 8497 | 4191 | 49.91% | 14717 |
| ordinary_joint | fit | 300 | 300 | 24714 | 64.0 | 150 | 176 | 886 | 52/222 | 25014 | 12258 | 49.60% | 39234 |
| ordinary_joint | validation | 100 | 100 | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 4193 | 49.89% | 14724 |
| coupled_joint | fit | 300 | 300 | 24691 | 64.0 | 149 | 176 | 886 | 52/222 | 24991 | 12240 | 49.57% | 39211 |
| coupled_joint | validation | 100 | 100 | 8397 | 61.5 | 154 | 199 | 477 | 17/70 | 8497 | 4191 | 49.91% | 14717 |

One Finish per program; dictionary, 41-byte packet headers, payload and padding are charged. Source bytes, decoder-inclusive packages and per-program storage are in evidence. Offline tooling bytes are a conservative source dependency inventory, not complete installed runtime storage. Failed candidates remain in cost tables and invalidate readiness.

| Arm | Better/same/worse vs control | Better/same/worse vs seed | Ready | Successor | Failed readiness | Failed successor |
| --- | --- | --- | --- | --- | --- | --- |
| control | 0/100/0 | 4/21/75 | False | False | actions_5_percent, median_lower, p90_lower, improved_60 | ready, actions_lower, median_nonincrease, p90_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| seed | 75/21/4 | 0/100/0 | True | False | None | actions_lower |
| ordinary | 75/21/4 | 0/100/0 | True | False | None | actions_lower |
| coupled | 76/20/4 | 5/95/0 | True | False | None | fallback_nonincrease |
| ordinary_joint | 75/21/4 | 0/100/0 | True | False | None | actions_lower |
| coupled_joint | 76/20/4 | 5/95/0 | True | False | None | fallback_nonincrease |

| Contrast | Validation action delta | Better/same/worse |
| --- | ---: | --- |
| ordinary minus seed | 0 | 0/100/0 |
| coupled minus ordinary | -7 | 5/95/0 |
| ordinary_joint minus seed | 0 | 0/100/0 |
| coupled_joint minus ordinary_joint | -7 | 5/95/0 |
| coupled_joint minus seed | -7 | 5/95/0 |

| Arm | Round | Dictionary trials/stop | Ordinary trials/moves | Coupled trials/moves | States/proposals/caps |
| --- | ---: | --- | --- | --- | --- |
| ordinary | 1 | 1/fixed_dictionary | 74976/21 | 0/0 | 0/0/0 |
| ordinary | 2 | 1/fixed_dictionary | 69917/0 | 0/0 | 0/0/0 |
| coupled | 1 | 1/fixed_dictionary | 74976/21 | 156/13 | 484526/156/0 |
| coupled | 2 | 1/fixed_dictionary | 71431/5 | 128/0 | 457434/128/0 |
| ordinary_joint | 1 | 907/local_optimum | 74976/21 | 0/0 | 0/0/0 |
| ordinary_joint | 2 | 907/local_optimum | 69917/0 | 0/0 | 0/0/0 |
| coupled_joint | 1 | 907/local_optimum | 74976/21 | 156/13 | 484526/156/0 |
| coupled_joint | 2 | 907/local_optimum | 71431/5 | 128/0 | 457434/128/0 |

Caps count state truncations plus proposal truncations; bounded search is not a global optimum. Validation counters and all stop reasons are in evidence. Historical search counters remain separately attributed to item13.

| Prediction | Met |
| --- | --- |
| C1 | True |
| C2 | False |
| C3 | False |
| C4 | True |
| C5 | True |
| C6 | True |

All final choices seal before execution. Distinct changed programs: 324/324 passed, 32,466/32,466 strict case checks; unchanged R reuses its pinned qualification. Finite parity checks and reused development cases do not establish universal equivalence or fresh generalization.

Measured run wall time: 98.40 seconds. Nine focused synthetic tests and compilation/import/help checks passed before launch; unchanged judge/lane infrastructure retains A’s 37 passing checks.

Owner gate: any selected successor requires a separately frozen confirmation population and explicit permission for protected/held-out access. Candidate artifacts are private coupled-names/run-v1/<selected>-256; dictionary/fit-seal hashes are in evidence. No training, deployment, publication, human study, ledger/catalog/claim write, autonomous-solving claim or M1 threshold change. Component intent preserved, canonical decoder and production boundaries unchanged.

Rebuild: `python3 -B projects/algorithm_solver/literals/coupled-names-v1/report.py --run /private/path/to/coupled-names/run-v1`.
