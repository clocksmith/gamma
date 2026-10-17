# Algorithm solver comparison: baseline-v2

Status: partial. Held out from our pipeline; prior model exposure unknown.

Initial comparison on a small frozen sample; not a ranking. Results describe the named solver with the contract budgets, not other backends or budgets. Frontier CLI solvers very likely saw these 2024-2025 problems; compare routes, not absolute rates.

Contract: `[run-contract] run_name=baseline-v2 pairs_input_spec=contracts/sample_manifest.json@40da673a01f4 resume_from=none resume_stage=none decode=greedy eval_dataset_paths=data/derived/problems.jsonl,data/derived/tests device=cuda schedule=none runtime_mode=normal_rocm sweep_mode=live model=Qwen/Qwen3.5-4B@851bf6e806ef thinking=False route_wall_seconds=120 first_max_new_tokens=1024 repair_max_new_tokens=1024 repairs=1`

Solver: `qwen`

## Recognition (known-problem lookup)

200/200 queries in 125 groups. Rates are per group with 95% bootstrap intervals over groups.

- Correct decision rate: 0.956 [0.928, 0.980] (n=125)
- Wrong-match rate: 0.024 [0.004, 0.048] (n=125)
- Abstain rate on known problems: 0.033 [0.007, 0.060] (n=75)
- Exact+paraphrase groups correct: 0.980 [0.950, 1.000] (n=50)
- Sibling-family groups correct: 0.860 [0.760, 0.940] (n=25); wrong: 0.080 [0.020, 0.160] (n=25)
- Absent groups correctly abstained: 0.980 [0.940, 1.000] (n=50)
- Returned solutions passing the true problem's hidden tests: 144/146
- Lookup latency p50/p95 (s): 0.096 / 0.205

Outcomes by query kind:

| kind | outcomes |
|---|---|
| absent_exact | correct_abstain=49, wrong_match=1 |
| exact | correct_match=50 |
| paraphrase | abstain=2, correct_match=48 |
| sibling_paraphrase | abstain=3, correct_match=43, wrong_match=4 |

## Solving (held-out problems)

22/150 problems finished all four routes; 22 of them have independent tests. Intervals resample problems.

| route | independent pass | example pass (all) | first-attempt independent | p50 / p95 route s | p50 / p95 time to checked answer s | budget exhausted |
|---|---|---|---|---|---|---|
| lookup | 0.000 [0.000, 0.000] (n=22) | 0.000 [0.000, 0.000] (n=22) | n/a | 0.086 / 0.178 | 0.086 / 0.177 | 0 |
| model_alone | 0.136 [0.000, 0.273] (n=22) | 0.273 [0.091, 0.455] (n=22) | 0.136 [0.000, 0.273] (n=22) | 110.123 / 110.183 | 110.197 / 110.258 | 12 |
| retrieval | 0.182 [0.045, 0.364] (n=22) | 0.318 [0.136, 0.500] (n=22) | 0.182 [0.045, 0.364] (n=22) | 88.623 / 110.186 | 88.78 / 110.252 | 10 |
| classify_template | 0.136 [0.000, 0.273] (n=22) | 0.273 [0.091, 0.455] (n=22) | 0.136 [0.000, 0.273] (n=22) | 110.111 / 110.203 | 110.178 / 110.271 | 13 |

Paired against model_alone (problems with independent tests):

| route | solved here only | solved by model_alone only | difference [95% CI] |
|---|---|---|---|
| lookup | 0 | 3 | -0.1364 [-0.2727, 0.0] |
| retrieval | 1 | 0 | 0.0455 [0.0, 0.1364] |
| classify_template | 0 | 0 | 0.0 [0.0, 0.0] |

Per-source counts (independent / example passes):

- lookup: lcd: 0/0 of 22
- model_alone: lcd: 3/6 of 22
- retrieval: lcd: 4/7 of 22
- classify_template: lcd: 3/6 of 22

Mean stage seconds:

- lookup: embed=0.088, match=0.012, public_judge=0.072; GPU peak None GB
- model_alone: generate=51.389, public_judge=0.086, repair_generate=28.376; GPU peak 10.55 GB; generation stopped by {'eos': 17, 'max_new_tokens': 9, 'max_time': 12}
- retrieval: generate=51.47, public_judge=0.076, repair_generate=28.202, retrieve=0.097; GPU peak 11.57 GB; generation stopped by {'max_new_tokens': 8, 'max_time': 10, 'eos': 19}
- classify_template: classify=0.002, generate=61.782, public_judge=0.083, repair_generate=27.104; GPU peak 10.81 GB; generation stopped by {'max_new_tokens': 11, 'max_time': 13, 'eos': 16}

## Evidence levels

- `example_passed`: passes the public examples shown in the statement
- `independent_tests_passed`: passes the problem's full hidden test set (LeetCodeDataset asserts, LiveCodeBench private tests, Codeforces official tests marked complete)
- `benchmark_judge_accepted`: not evaluated in this run (LiveCodeBench's own judge was not run)

Full numbers, thresholds, classifier metrics and per-route outcome counts are in report.json.
