# Per-binding exact-cost naming

[Freeze](FREEZE.md) pushed in `c306b899f`; [review/run receipt](REVIEW.md). [Evidence](evidence/results.json) publishes only metadata. Source bodies, dictionaries, mappings, candidate traces and cases stay private.

Development-ready selection: **['scope_joint', 256]**. This is offline optimization supplied with a known program. It establishes neither autonomous assembly nor fresh generalization.

Validation programs are rewritten by the encoder under a dictionary sealed on fit. The validation comparison is therefore source-plus-encoder optimization versus fixed source, with independent qualification after all choices are sealed.

At 256 entries, scope_joint uses 8,504 validation actions versus 9,048 for control (6.01% fewer), with 75 better/21 same/4 worse programs. Single-character fraction falls from 55.14% to 49.89%, and raw package bytes from 15,255 to 14,724. The fixed-dictionary scope arm also passes readiness: 8,576 actions (5.22% fewer), 73 better/27 same/0 worse. Frozen ranking selects scope_joint. Its median/p95 remain 61.5/199 selections and character fraction remains far above M1’s gates; readiness is not M1 qualification.

## Costs and qualification

| Width | Arm | Split | Decoded | Qualified | Changed | Selections | Median | p90 | p95 | Worst | <=32 / <=96 | Actions | Single-char | Package bytes |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 128 | control | fit | 300/300 | 300/300 | 0 | 41684 | 107.0 | 256 | 303 | 1173 | 10/128 | 41984 | 79.22% | 49725 |
| 128 | control | validation | 100/100 | 100/100 | 0 | 14014 | 103.5 | 267 | 320 | 716 | 5/45 | 14114 | 78.67% | 17225 |
| 128 | global | fit | 300/300 | 300/300 | 54 | 41382 | 107.0 | 255 | 303 | 1173 | 10/129 | 41682 | 78.94% | 49460 |
| 128 | global | validation | 100/100 | 100/100 | 16 | 13906 | 103.5 | 260 | 320 | 716 | 5/46 | 14006 | 78.42% | 17133 |
| 128 | global_joint | fit | 300/300 | 300/300 | 54 | 41382 | 107.0 | 255 | 303 | 1173 | 10/129 | 41682 | 78.94% | 49460 |
| 128 | global_joint | validation | 100/100 | 100/100 | 16 | 13906 | 103.5 | 260 | 320 | 716 | 5/46 | 14006 | 78.42% | 17133 |
| 128 | scope | fit | 300/300 | 300/300 | 95 | 41054 | 107.0 | 251 | 300 | 1167 | 10/129 | 41354 | 78.53% | 49171 |
| 128 | scope | validation | 100/100 | 100/100 | 33 | 13776 | 103.0 | 260 | 318 | 703 | 5/47 | 13876 | 77.90% | 17021 |
| 128 | scope_joint | fit | 300/300 | 300/300 | 95 | 41042 | 106.5 | 251 | 299 | 1172 | 12/131 | 41342 | 77.48% | 49167 |
| 128 | scope_joint | validation | 100/100 | 100/100 | 33 | 13770 | 103.0 | 258 | 320 | 696 | 5/45 | 13870 | 76.64% | 17021 |
| 256 | control | fit | 300/300 | 300/300 | 0 | 26108 | 68.0 | 162 | 188 | 930 | 48/216 | 26408 | 54.06% | 40615 |
| 256 | control | validation | 100/100 | 100/100 | 0 | 8948 | 63.5 | 169 | 211 | 501 | 13/69 | 9048 | 55.14% | 15255 |
| 256 | global | fit | 300/300 | 300/300 | 202 | 25288 | 65.0 | 155 | 181 | 914 | 49/219 | 25588 | 50.98% | 39795 |
| 256 | global | validation | 100/100 | 100/100 | 73 | 8616 | 62.5 | 158 | 203 | 489 | 16/70 | 8716 | 51.50% | 14923 |
| 256 | global_joint | fit | 300/300 | 300/300 | 208 | 25136 | 64.5 | 155 | 181 | 912 | 51/221 | 25436 | 50.68% | 39660 |
| 256 | global_joint | validation | 100/100 | 100/100 | 72 | 8582 | 61.5 | 158 | 203 | 488 | 16/70 | 8682 | 51.19% | 14906 |
| 256 | scope | fit | 300/300 | 300/300 | 217 | 24915 | 64.5 | 151 | 177 | 893 | 49/221 | 25215 | 50.00% | 39422 |
| 256 | scope | validation | 100/100 | 100/100 | 73 | 8476 | 62.5 | 156 | 197 | 477 | 16/70 | 8576 | 50.61% | 14783 |
| 256 | scope_joint | fit | 300/300 | 300/300 | 218 | 24750 | 64.0 | 150 | 176 | 886 | 52/222 | 25050 | 49.81% | 39270 |
| 256 | scope_joint | validation | 100/100 | 100/100 | 72 | 8404 | 61.5 | 154 | 199 | 477 | 17/70 | 8504 | 49.89% | 14724 |

Costs describe all encoded candidates; any unqualified candidate invalidates readiness and its cost is not a qualified improvement. Changed final sources undergo all frozen cases with strict observation parity. Unchanged R sources reuse hash-bound qualification. Case reuse and finite parity checks are development evidence, not universal equivalence or unseen correctness. Each packet decodes independently to its selected source hash. One Finish is included in actions. Headers are 41 bytes; padding and dictionary storage are charged. Decoder-inclusive and one-program storage plus offline tooling source bytes are in the evidence; complete installed runtime footprint is unmeasured.

## Paired validation

| Width | Arm | Better/same/worse vs baseline | Better/same/worse vs searched control | Ready | Failed readiness predicates |
| ---: | --- | --- | --- | --- | --- |
| 128 | control | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 128 | global | 16/84/0 | 16/84/0 | False | actions_5_percent, median_lower, improved_60 |
| 128 | global_joint | 16/84/0 | 16/84/0 | False | actions_5_percent, median_lower, improved_60 |
| 128 | scope | 33/67/0 | 33/67/0 | False | actions_5_percent, improved_60 |
| 128 | scope_joint | 56/16/28 | 56/16/28 | False | actions_5_percent, improved_60, worsened_at_most_25 |
| 256 | control | 0/100/0 | 0/100/0 | False | actions_5_percent, median_lower, p90_lower, improved_60 |
| 256 | global | 73/27/0 | 73/27/0 | False | actions_5_percent |
| 256 | global_joint | 73/26/1 | 73/26/1 | False | actions_5_percent |
| 256 | scope | 73/27/0 | 73/27/0 | True | None |
| 256 | scope_joint | 75/21/4 | 75/21/4 | True | None |

## Source/search contrasts

| Width | Contrast | Validation action delta | Better/same/worse |
| ---: | --- | ---: | --- |
| 128 | global minus control | -108 | 16/84/0 |
| 128 | scope minus global | -130 | 22/78/0 |
| 128 | global_joint minus global | 0 | 0/100/0 |
| 128 | scope_joint minus scope | -6 | 41/15/44 |
| 128 | scope_joint minus global_joint | -136 | 53/15/32 |
| 256 | global minus control | -332 | 73/27/0 |
| 256 | scope minus global | -140 | 28/71/1 |
| 256 | global_joint minus global | -34 | 22/71/7 |
| 256 | scope_joint minus scope | -72 | 42/43/15 |
| 256 | scope_joint minus global_joint | -178 | 48/40/12 |

## Search accounting

| Width | Arm | Round | Dictionary trials | Stop | Dictionary seconds | Rewrite trials | Rewrite moves |
| ---: | --- | ---: | ---: | --- | ---: | ---: | ---: |
| 128 | control | 1 | 779 | local_optimum | 6.60 | 0 | 0 |
| 128 | control | 2 | 779 | local_optimum | 6.73 | 0 | 0 |
| 128 | global | 1 | 1 | fixed_dictionary | 0.02 | 67960 | 70 |
| 128 | global | 2 | 1 | fixed_dictionary | 0.04 | 56390 | 0 |
| 128 | global_joint | 1 | 779 | local_optimum | 12.70 | 67960 | 70 |
| 128 | global_joint | 2 | 779 | local_optimum | 18.83 | 56390 | 0 |
| 128 | scope | 1 | 1 | fixed_dictionary | 0.02 | 109177 | 145 |
| 128 | scope | 2 | 1 | fixed_dictionary | 0.04 | 72404 | 0 |
| 128 | scope_joint | 1 | 1557 | local_optimum | 25.92 | 109177 | 145 |
| 128 | scope_joint | 2 | 779 | local_optimum | 18.74 | 73387 | 3 |
| 256 | control | 1 | 907 | local_optimum | 5.66 | 0 | 0 |
| 256 | control | 2 | 907 | local_optimum | 5.79 | 0 | 0 |
| 256 | global | 1 | 1 | fixed_dictionary | 0.03 | 100021 | 412 |
| 256 | global | 2 | 1 | fixed_dictionary | 0.05 | 56359 | 0 |
| 256 | global_joint | 1 | 2719 | local_optimum | 30.02 | 100021 | 412 |
| 256 | global_joint | 2 | 1813 | local_optimum | 28.70 | 61452 | 31 |
| 256 | scope | 1 | 1 | fixed_dictionary | 0.03 | 131611 | 584 |
| 256 | scope | 2 | 1 | fixed_dictionary | 0.04 | 71170 | 1 |
| 256 | scope_joint | 1 | 2719 | local_optimum | 29.61 | 131611 | 584 |
| 256 | scope_joint | 2 | 3625 | local_optimum | 59.49 | 80039 | 44 |

The global and scope policies share budgets but follow different coordinate paths; the larger scope-local feasible set does not guarantee lower cost from this bounded algorithm. Global_joint versus scope_joint compares complete source/dictionary trajectories, whose proposals can diverge.
Historical name-search joint128: 14006 actions. Its guards and search differ; this is not a matched arm.
Historical name-search joint256: 8684 actions. Its guards and search differ; this is not a matched arm.

Dictionary seconds exclude the preceding rewrite call. Total run wall time includes rewriting, validation and qualification. Time-capped comparisons are budget-limited; local termination is not an optimum. Fixed-dictionary arms do no dictionary search. Validation rewrite counts, category attributions, full action distributions and framing/padding are retained in evidence.

| Prediction | Met |
| --- | --- |
| D1 | True |
| D2 | True |
| D3 | True |
| D4 | True |
| D5 | True |
| D6 | True |

Independent execution passed 649/649 distinct changed programs and 62,521/62,521 case checks. No retry or candidate repair.

Measured total wall time: 242.14 seconds. Twelve synthetic scope/graph/budget checks and compilation/import passed before launch; the unchanged judge/lane infrastructure retains A’s 37 passing checks. Source execution is separately recorded above. No test result fed back into rewriting or vocabulary search; failures receive no repair.

Confirmation remains at the owner gate: freeze the exact selected dictionary and encoder on a separately approved population before any protected/held-out opening, with no refit or repair. The private candidate is binding-descent/run-v1/scope_joint-256; its dictionary and fit-seal hashes are in the evidence. Continued development must use a new freeze and does not retroactively confirm this candidate. A ready development arm can only motivate a separately frozen owner-approved confirmation. Final held-out/protected opening, source publication, BITS changes, human studies and training remain gated. The report is the source of truth for readiness against searched control; every failed predicate is listed above.

Component: algorithm_solver literal research. Intent preserved; no production boundary or decoder change, ledger/catalog/claim write, M1 threshold change or autonomous-solving claim.

Rebuild: `python3 -B projects/algorithm_solver/literals/binding-descent-v1/report.py --run /private/path/to/binding-descent/run-v1`.
