# Known-incumbent initialization for exact repairs

[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [metadata evidence](evidence/results.json). Models, start vectors, dictionaries, sources and packets remain private.

Recommend for a future frozen search: **True**. Warm/cold paired exact costs: 8 better, 0 same, 0 worse, 0 unavailable. No candidate promotion, validation or M1 claim.

Post-hoc search-incumbent attribution: after each condition retains the better of the supplied seed and its returned dictionary, warm is 0 better, 8 same and 0 worse. Returning a better nonimproving solver point does not improve the existing search incumbent. This additional attribution leaves frozen W1–W6 and the tool-recommendation rule unchanged.

Eight snapshots start independently from the same item13 source/dictionary seed. Every pair shares one hashed model, objective, candidate order, budget and solver options. Only warm receives the algebraically checked complete incumbent. Order is balanced; calls run sequentially on the same core. No prior frozen search is rerun or revised.

| Trial/type | Order | Cold exact / flow objective | Warm exact / flow objective | Warm−cold exact | Cold/warm optimal | Cold/warm call seconds |
| --- | --- | --- | --- | ---: | --- | --- |
| 0/fixed96 | cold first | 29523/45470.0 | 24750/24750.0 | -4773 | False/False | 91.19/91.85 |
| 1/fixed96 | warm first | 29546/45608.0 | 24750/24750.0 | -4796 | False/False | 90.92/91.25 |
| 2/fixed96 | cold first | 29069/45452.0 | 24750/24750.0 | -4319 | False/False | 91.20/91.02 |
| 3/fixed96 | warm first | 29786/45103.0 | 24750/24750.0 | -5036 | False/False | 90.72/91.06 |
| 4/optional | cold first | 28901/44478.0 | 24750/24750.0 | -4151 | False/False | 90.62/90.74 |
| 5/optional | warm first | 28678/43573.0 | 24750/24750.0 | -3928 | False/False | 90.76/90.69 |
| 6/optional | cold first | 29118/45536.0 | 24750/24750.0 | -4368 | False/False | 90.43/90.64 |
| 7/optional | warm first | 28831/44463.0 | 24750/24750.0 | -4081 | False/False | 90.52/90.66 |

Exact cost independently re-encodes the chosen dictionary and can be below a time-limited feasible flow objective. Solver optimality concerns only that bounded repair model; it is not a global vocabulary certificate. Missing feasible points remain failed calls with no invented cost.

| Group | Condition | Feasible/nonworse/improving/optimal | Calls | Complete call / solver seconds | Decoded |
| --- | --- | --- | ---: | --- | ---: |
| all | cold | 8/0/0/0 | 8 | 726.37/724.49 | 2400 |
| all | warm | 8/8/0/0 | 8 | 727.91/725.75 | 2400 |
| fixed96 | cold | 4/0/0/0 | 4 | 364.04/363.00 | 1200 |
| fixed96 | warm | 4/4/0/0 | 4 | 365.18/364.04 | 1200 |
| optional | cold | 4/0/0/0 | 4 | 362.33/361.49 | 1200 |
| optional | warm | 4/4/0/0 | 4 | 362.73/361.71 | 1200 |

Per-result selection/action quantiles, character counts/fractions, dictionary/packet and one-program/amortized costs are in evidence. Each is an independent300-program dictionary result: their summed costs are a matched diagnostic, not a new shared vocabulary. Every encoded program pays one Finish, eight-bit selections,41-byte frame and full dictionary storage. Decoder source inventory is separately charged; full runtime footprint is unmeasured.

| Prediction | Met |
| --- | --- |
| W1 | True |
| W2 | True |
| W3 | False |
| W4 | False |
| W5 | True |
| W6 | True |

4800 packets independently decode; total wall time 374.93 seconds. Start feasibility/model hashes are rebuilt without solving during reporting. Four synthetic tests include32exhaustive comparisons against both direct conditions and SciPy, plus zero-time incumbent retention. Source qualification reuses item15 by exact hash; no case rerun. Item23 failure remains unchanged.

The version-pinned internal HiGHS binding is research-local. Component intent and canonical decoder preserved; no production API, training, protected opening, source publication, ledger/catalog/claim write, deployment or human study.

Rebuild with pinned SciPy Python: `python -B projects/algorithm_solver/literals/seeded-repair-v1/report.py --run /private/seeded-repair/run-v1 --work /private/literal-admission500-v1`.
