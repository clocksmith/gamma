# Exact greedy chains (development only)

Built by `../engine_exact.c` (heap keyed by a bound that never rises, so each pick is the best available) on CodeNet
`primary`, policy `s1-whole`, L = 16, 4,096 entries. Not frozen and not scored on any test set.

| File | What |
| --- | --- |
| `exact-open.txt` | exact open token gain (mode `exact-entry`), 2.3 h on one core |
| `exact-closed.txt` | exact closed token gain (mode `exact-closed`), 1.6 h |
| `verify-exact-open.tsv`, `verify-exact-closed.tsv` | `../verify_greedy.c` brute force at every 400th / 200th step: 10 of 10 and 20 of 20 picks are the best available |
| `dev-exact.json` | `../dev_eval.py` on `train` and `dev` only: exact and lazy chains against BPE on the equal-size grid |

On `dev` at 3,924 fragments, exact open token gain is +6.0% against BPE (lazy: +6.4%) and exact closed token gain is
-1.7% (lazy: -1.5%); at 84 fragments -11.8% and -0.3% (lazy: -11.9% and -0.3%). The reversal is not a product of
lazy evaluation. `engine_exact.c` at build time had SHA-256 e5ad53f171ae56e1... (the cuts guard added later does not apply
here: no cuts were used).
