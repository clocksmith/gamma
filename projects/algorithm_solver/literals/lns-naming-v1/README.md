# Exact dictionary repairs with per-binding naming

[Freeze](FREEZE.md); [review/run receipt](REVIEW.md); [evidence](evidence/results.json). Private sources, dictionaries, packets, cases and repair traces remain private.

Selected incremental successor: **none**. This is adaptive consumed-development evidence, not independent confirmation, autonomous assembly or M1 qualification.

The lowest validation total is lns_joint/adaptive:8335actions versus8504for the seed (1.99%fewer), or7.88%below originalR. But its median actions rise62.5→65 and37programs worsen versus seed (35better/28same). Every LNS view also misses the original-control strict-median gate. No incremental successor is selected; lower total cost does not override the breadth and median rules.

All dictionaries start from item13 scope_joint256. Ordinary and lns_joint alternate naming with dictionary fitting; lns_fixed preserves fit source bytes. Every dictionary gets a fixed item13 validation view and a common two-call naming view. Only LNS candidates passing readiness against R and incremental checks against item13, seed and ordinary under the same view can be selected.

| Arm | Split | Decoded/qualified | Selections | Median/p90/p95/worst | <=32/96 | Actions | Character codes/fraction | Raw package | With decoder sources |
| --- | --- | --- | ---: | --- | --- | ---: | --- | ---: | ---: |
| seed_fixed_seed | fit | 300/300 | 24750 | 64.0/150/176/886 | 52/222 | 25050 | 12328/49.81% | 39270 | 52280 |
| seed_fixed_seed | validation | 100/100 | 8404 | 61.5/154/199/477 | 17/70 | 8504 | 4193/49.89% | 14724 | 27734 |
| seed_adaptive | fit | 300/300 | 24750 | 64.0/150/176/886 | 52/222 | 25050 | 12328/49.81% | 39270 | 52280 |
| seed_adaptive | validation | 100/100 | 8404 | 61.5/154/199/477 | 17/70 | 8504 | 4193/49.89% | 14724 | 27734 |
| ordinary_fixed_seed | fit | 300/300 | 24714 | 64.0/150/176/886 | 52/222 | 25014 | 12258/49.60% | 39234 | 52244 |
| ordinary_fixed_seed | validation | 100/100 | 8404 | 61.5/154/199/477 | 17/70 | 8504 | 4193/49.89% | 14724 | 27734 |
| ordinary_adaptive | fit | 300/300 | 24714 | 64.0/150/176/886 | 52/222 | 25014 | 12258/49.60% | 39234 | 52244 |
| ordinary_adaptive | validation | 100/100 | 8404 | 61.5/154/199/477 | 17/70 | 8504 | 4193/49.89% | 14724 | 27734 |
| lns_joint_fixed_seed | fit | 300/300 | 24013 | 64.0/141/176/881 | 51/230 | 24313 | 11824/49.24% | 39045 | 52055 |
| lns_joint_fixed_seed | validation | 100/100 | 8283 | 64.0/154/176/471 | 14/72 | 8383 | 4133/49.90% | 15115 | 28125 |
| lns_joint_adaptive | fit | 300/300 | 24013 | 64.0/141/176/881 | 51/230 | 24313 | 11824/49.24% | 39045 | 52055 |
| lns_joint_adaptive | validation | 100/100 | 8235 | 64.0/154/176/470 | 14/72 | 8335 | 4077/49.51% | 15067 | 28077 |
| lns_fixed_fixed_seed | fit | 300/300 | 24208 | 64.0/145/187/889 | 53/230 | 24508 | 12069/49.86% | 39189 | 52199 |
| lns_fixed_fixed_seed | validation | 100/100 | 8298 | 64.0/155/174/493 | 15/74 | 8398 | 4158/50.11% | 15079 | 28089 |
| lns_fixed_adaptive | fit | 300/300 | 24208 | 64.0/145/187/889 | 53/230 | 24508 | 12069/49.86% | 39189 | 52199 |
| lns_fixed_adaptive | validation | 100/100 | 8259 | 64.0/155/174/492 | 15/74 | 8359 | 4107/49.73% | 15040 | 28050 |

One Finish, complete dictionary, 41-byte frame and eight-bit selections charged. Decoder source storage is separate; the offline solver/runtime installation is not a complete measured deployment footprint. Every failed choice remains in its denominator.

| Arm | Comparator | Action delta | Better/same/worse | Failed incremental checks |
| --- | --- | ---: | --- | --- |
| seed_fixed_seed | R | -544 | 75/21/4 | See readiness below |
| seed_fixed_seed | item13 | 0 | 0/100/0 | actions_lower |
| seed_fixed_seed | seed_same_view | 0 | 0/100/0 | actions_lower |
| seed_fixed_seed | ordinary_same_view | 0 | 0/100/0 | actions_lower |
| seed_adaptive | R | -544 | 75/21/4 | See readiness below |
| seed_adaptive | item13 | 0 | 0/100/0 | actions_lower |
| seed_adaptive | seed_same_view | 0 | 0/100/0 | actions_lower |
| seed_adaptive | ordinary_same_view | 0 | 0/100/0 | actions_lower |
| ordinary_fixed_seed | R | -544 | 75/21/4 | See readiness below |
| ordinary_fixed_seed | item13 | 0 | 0/100/0 | actions_lower |
| ordinary_fixed_seed | seed_same_view | 0 | 0/100/0 | actions_lower |
| ordinary_fixed_seed | ordinary_same_view | 0 | 0/100/0 | actions_lower |
| ordinary_adaptive | R | -544 | 75/21/4 | See readiness below |
| ordinary_adaptive | item13 | 0 | 0/100/0 | actions_lower |
| ordinary_adaptive | seed_same_view | 0 | 0/100/0 | actions_lower |
| ordinary_adaptive | ordinary_same_view | 0 | 0/100/0 | actions_lower |
| lns_joint_fixed_seed | R | -665 | 63/18/19 | See readiness below |
| lns_joint_fixed_seed | item13 | -121 | 26/27/47 | median_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| lns_joint_fixed_seed | seed_same_view | -121 | 26/27/47 | median_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| lns_joint_fixed_seed | ordinary_same_view | -121 | 26/27/47 | median_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| lns_joint_adaptive | R | -713 | 70/14/16 | See readiness below |
| lns_joint_adaptive | item13 | -169 | 35/28/37 | median_nonincrease, worsened_at_most_25 |
| lns_joint_adaptive | seed_same_view | -169 | 35/28/37 | median_nonincrease, worsened_at_most_25 |
| lns_joint_adaptive | ordinary_same_view | -169 | 35/28/37 | median_nonincrease, worsened_at_most_25 |
| lns_fixed_fixed_seed | R | -650 | 65/18/17 | See readiness below |
| lns_fixed_fixed_seed | item13 | -106 | 23/34/43 | median_nonincrease, p90_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| lns_fixed_fixed_seed | seed_same_view | -106 | 23/34/43 | median_nonincrease, p90_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| lns_fixed_fixed_seed | ordinary_same_view | -106 | 23/34/43 | median_nonincrease, p90_nonincrease, fallback_nonincrease, worsened_at_most_25 |
| lns_fixed_adaptive | R | -689 | 70/15/15 | See readiness below |
| lns_fixed_adaptive | item13 | -145 | 29/35/36 | median_nonincrease, p90_nonincrease, worsened_at_most_25 |
| lns_fixed_adaptive | seed_same_view | -145 | 29/35/36 | median_nonincrease, p90_nonincrease, worsened_at_most_25 |
| lns_fixed_adaptive | ordinary_same_view | -145 | 29/35/36 | median_nonincrease, p90_nonincrease, worsened_at_most_25 |

| Arm | Ready vs R | Incremental successor | Failed readiness |
| --- | --- | --- | --- |
| seed_fixed_seed | True | False | None |
| seed_adaptive | True | False | None |
| ordinary_fixed_seed | True | False | None |
| ordinary_adaptive | True | False | None |
| lns_joint_fixed_seed | False | False | median_lower |
| lns_joint_adaptive | False | False | median_lower |
| lns_fixed_fixed_seed | False | False | median_lower |
| lns_fixed_adaptive | False | False | median_lower |

| Dictionary arm | Round | Before/naming/repair/polish selections | Accepted/attempted repairs | Repair stop/seconds | Polish trials/stop |
| --- | ---: | --- | --- | --- | --- |
| ordinary | 1 | 24750/24714/24714/24714 | 0/0 | None | 907/local_optimum |
| ordinary | 2 | 24714/24714/24714/24714 | 0/0 | None | 907/local_optimum |
| lns_fixed | 1 | 24750/24750/24274/24215 | 5/6 | move_limit/524.41 | 4531/local_optimum |
| lns_fixed | 2 | 24215/24215/24208/24208 | 1/6 | move_limit/696.49 | 907/local_optimum |
| lns_joint | 1 | 24750/24714/24187/24187 | 6/6 | move_limit/549.92 | 907/local_optimum |
| lns_joint | 2 | 24187/24033/24015/24013 | 3/6 | move_limit/613.43 | 2719/local_optimum |

Each MILP optimizes a bounded candidate pool for the selected source snapshot; it does not optimize all retained variants jointly. Exact rescoring and source reselection are recorded separately. Solver status0 is solver-reported optimality of that repair, not an independently certified global optimum. Time-limited feasible solutions are candidates only. LNS receives additional compute beyond ordinary continuation.

| Prediction | Met |
| --- | --- |
| J1 | True |
| J2 | True |
| J3 | True |
| J4 | True |
| J5 | True |
| J6 | False |

Distinct final changed sources: 404/404 qualified, 40328/40328 strict original-case/parity checks. All choices sealed before execution, no retries or repairs. Unchanged R reuses its pinned receipt. Finite reused development cases do not establish universal equivalence. Measured run wall time: 1369.58 seconds.

Component intent preserved; canonical codec and production behavior unchanged. Confirmation, protected data, training, publication, deployment and human studies remain owner-gated. Private selected artifacts: lns-naming/run-v1/<selected>-256. No ledger/catalog/claim writes.

Rebuild with the pinned SciPy Python: `python -B projects/algorithm_solver/literals/lns-naming-v1/report.py --run /private/lns-naming/run-v1`.
