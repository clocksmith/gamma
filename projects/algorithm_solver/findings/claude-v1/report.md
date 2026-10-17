# Algorithm solver comparison: claude-v1

Status: complete. Held out from our pipeline; prior model exposure unknown.

Initial comparison on a small frozen sample; not a ranking. Results describe the named solver with the contract budgets, not other backends or budgets. Frontier CLI solvers very likely saw these 2024-2025 problems; compare routes, not absolute rates.

Contract: `[run-contract] run_name=claude-v1 pairs_input_spec=contracts/sample_manifest.json@40da673a01f4 resume_from=none resume_stage=none decode=harness default (not greedy) eval_dataset_paths=data/derived/problems.jsonl,data/derived/tests device=cuda schedule=none runtime_mode=normal_rocm sweep_mode=live model=claude-opus-5-5@harness-mana solver=claude thinking=high route_wall_seconds=120 first_max_new_tokens=1024 repair_max_new_tokens=1024 repairs=1`

Solver: `claude`

## Recognition (known-problem lookup)

not run here: lookup does not depend on the solver; see the baseline-v2 run

## Solving (held-out problems)

150/150 problems finished all four routes; 121 of them have independent tests. Intervals resample problems.

| route | independent pass | example pass (all) | first-attempt independent | p50 / p95 route s | p50 / p95 time to checked answer s | budget exhausted |
|---|---|---|---|---|---|---|
| lookup | 0.000 [0.000, 0.000] (n=121) | 0.000 [0.000, 0.000] (n=150) | n/a | 0.104 / 0.349 | 0.104 / 0.349 | 0 |
| model_alone | 0.826 [0.752, 0.893] (n=121) | 0.947 [0.907, 0.980] (n=150) | 0.818 [0.744, 0.884] (n=121) | 6.361 / 90.067 | 6.527 / 90.31 | 7 |
| retrieval | 0.826 [0.752, 0.893] (n=121) | 0.947 [0.907, 0.980] (n=150) | 0.826 [0.752, 0.893] (n=121) | 6.957 / 89.925 | 7.238 / 90.154 | 7 |
| classify_template | 0.818 [0.744, 0.884] (n=121) | 0.953 [0.920, 0.987] (n=150) | 0.818 [0.744, 0.884] (n=121) | 6.259 / 76.529 | 6.772 / 77.098 | 6 |

Paired against model_alone (problems with independent tests):

| route | solved here only | solved by model_alone only | difference [95% CI] |
|---|---|---|---|
| lookup | 0 | 100 | -0.8264 [-0.8926, -0.7521] |
| retrieval | 1 | 1 | 0.0 [-0.0248, 0.0248] |
| classify_template | 0 | 1 | -0.0083 [-0.0248, 0.0] |

Per-source counts (independent / example passes):

- lookup: cf: 0/0 of 50; lcb: 0/0 of 50; lcd: 0/0 of 50
- model_alone: cf: 17/43 of 50; lcb: 40/49 of 50; lcd: 43/50 of 50
- retrieval: cf: 17/44 of 50; lcb: 39/48 of 50; lcd: 44/50 of 50
- classify_template: cf: 17/44 of 50; lcb: 40/49 of 50; lcd: 42/50 of 50

Mean stage seconds:

- lookup: embed=0.143, match=0.011, public_judge=0.066; GPU peak None GB
- model_alone: generate=14.309, public_judge=0.04, repair_generate=20.015; GPU peak None GB; generation stopped by {'eos': 150, 'max_time': 7}; CLI calls 157, with tool items 0, reported cost $5.6705 (notional on subscription), models ['claude-opus-5-5']
- retrieval: generate=14.297, public_judge=0.039, repair_generate=26.169, retrieve=0.153; GPU peak None GB; generation stopped by {'eos': 149, 'max_time': 7}; CLI calls 156, with tool items 0, reported cost $6.9784 (notional on subscription), models ['claude-opus-5-5']
- classify_template: classify=0.002, generate=14.699, public_judge=0.039, repair_generate=14.049; GPU peak None GB; generation stopped by {'eos': 150, 'max_time': 6}; CLI calls 156, with tool items 0, reported cost $6.086 (notional on subscription), models ['claude-opus-5-5']

## Evidence levels

- `example_passed`: passes the public examples shown in the statement
- `independent_tests_passed`: passes the problem's full hidden test set (LeetCodeDataset asserts, LiveCodeBench private tests, Codeforces official tests marked complete)
- `benchmark_judge_accepted`: not evaluated in this run (LiveCodeBench's own judge was not run)

Full numbers, thresholds, classifier metrics and per-route outcome counts are in report.json.
