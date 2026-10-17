# Algorithm solver comparison: codex-v1-checkpoint-20261017

Status: partial. Held out from our pipeline; prior model exposure unknown.

Initial comparison on a small frozen sample; not a ranking. Results describe the named solver with the contract budgets, not other backends or budgets. Frontier CLI solvers very likely saw these 2024-2025 problems; compare routes, not absolute rates.

Contract: `[run-contract] run_name=codex-v1 pairs_input_spec=contracts/sample_manifest.json@40da673a01f4 resume_from=none resume_stage=none decode=harness default (not greedy) eval_dataset_paths=data/derived/problems.jsonl,data/derived/tests device=cuda schedule=none runtime_mode=normal_rocm sweep_mode=live model=gpt-6-astra@harness-mana solver=codex thinking=high route_wall_seconds=120 first_max_new_tokens=1024 repair_max_new_tokens=1024 repairs=1`

Solver: `codex`

## Recognition (known-problem lookup)

not run here: lookup does not depend on the solver; see the baseline-v2 run

## Solving (held-out problems)

135/150 problems finished all four routes; 121 of them have independent tests. Intervals resample problems.

| route | independent pass | example pass (all) | first-attempt independent | p50 / p95 route s | p50 / p95 time to checked answer s | budget exhausted |
|---|---|---|---|---|---|---|
| lookup | 0.000 [0.000, 0.000] (n=121) | 0.000 [0.000, 0.000] (n=135) | n/a | 0.105 / 0.359 | 0.105 / 0.359 | 0 |
| model_alone | 0.802 [0.727, 0.868] (n=121) | 0.926 [0.881, 0.963] (n=135) | 0.802 [0.727, 0.868] (n=121) | 10.66 / 110.063 | 10.87 / 110.108 | 8 |
| retrieval | 0.802 [0.727, 0.868] (n=121) | 0.933 [0.889, 0.970] (n=135) | 0.793 [0.719, 0.860] (n=121) | 10.626 / 103.766 | 11.443 / 104.146 | 7 |
| classify_template | 0.777 [0.703, 0.851] (n=121) | 0.926 [0.881, 0.963] (n=135) | 0.777 [0.703, 0.851] (n=121) | 10.491 / 110.037 | 10.829 / 110.089 | 8 |

Paired against model_alone (problems with independent tests):

| route | solved here only | solved by model_alone only | difference [95% CI] |
|---|---|---|---|
| lookup | 0 | 97 | -0.8017 [-0.8678, -0.7273] |
| retrieval | 2 | 2 | 0.0 [-0.0331, 0.0331] |
| classify_template | 1 | 4 | -0.0248 [-0.0579, 0.0083] |

Per-source counts (independent / example passes):

- lookup: cf: 0/0 of 35; lcb: 0/0 of 50; lcd: 0/0 of 50
- model_alone: cf: 16/27 of 35; lcb: 39/48 of 50; lcd: 42/50 of 50
- retrieval: cf: 16/27 of 35; lcb: 40/49 of 50; lcd: 41/50 of 50
- classify_template: cf: 16/28 of 35; lcb: 38/47 of 50; lcd: 40/50 of 50

Mean stage seconds:

- lookup: embed=0.127, match=0.012, public_judge=0.088; GPU peak None GB
- model_alone: generate=21.083, public_judge=0.041, repair_generate=16.754; GPU peak None GB; generation stopped by {'eos': 131, 'max_time': 8}; CLI calls 139, with tool items 0, reported cost $0 (notional on subscription), models ['gpt-6-astra']
- retrieval: generate=20.606, public_judge=0.04, repair_generate=16.949, retrieve=0.138; GPU peak None GB; generation stopped by {'eos': 134, 'max_time': 7}; CLI calls 141, with tool items 0, reported cost $0 (notional on subscription), models ['gpt-6-astra']
- classify_template: classify=0.002, generate=19.842, public_judge=0.042, repair_generate=16.447; GPU peak None GB; generation stopped by {'eos': 133, 'max_time': 8}; CLI calls 141, with tool items 0, reported cost $0 (notional on subscription), models ['gpt-6-astra']

## Evidence levels

- `example_passed`: passes the public examples shown in the statement
- `independent_tests_passed`: passes the problem's full hidden test set (LeetCodeDataset asserts, LiveCodeBench private tests, Codeforces official tests marked complete)
- `benchmark_judge_accepted`: not evaluated in this run (LiveCodeBench's own judge was not run)

Full numbers, thresholds, classifier metrics and per-route outcome counts are in report.json.
