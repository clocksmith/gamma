# lagrange-select-v2: Lagrangian global dictionary selection (not ready; certified pool bound recorded)

Frozen design: [FREEZE.md](FREEZE.md) (`ebcdca946`) plus a pre-launch
[amendment](AMENDMENT-1.md) (`e38c663cb`) that adds a private replay receipt. Codex reviewed and
approved both (gamma-team LOG 17:59Z), and v1 was superseded before running. The single run
took 893 s on Jupiter: two width processes, one BLAS thread each.

Public evidence is in [evidence/results.json](evidence/results.json): aggregates, per-problem
dev-val actions by ID, dictionary hashes, seal hashes, the bound trajectory and the certificate.
The pool strings, dictionaries and the multiplier vector stay private. Each width's three
dictionaries were sealed in `fit-seal.json` before validation was opened.

## Result

| | 128 entries | 256 entries |
| --- | ---: | ---: |
| Pool (2–64 characters, at least two fit owners) | 223,244 strings, 1,118,337 occurrences | same |
| **Certified dev-fit lower bound, pool dictionaries** | **32,700** | **21,215** |
| control (pinned L-R + exact search continuation), dev-fit | 41,684 | 26,108 |
| global (Lagrangian primal + the same exact search), dev-fit | 41,247 (−1.05%) | 25,924 (−0.70%) |
| global_raw (Lagrangian primal, no polish), dev-fit | 42,996 | 28,636 |
| control, dev-val actions (median / p90) | 14,114 (104.5 / 268) | 9,048 (64.5 / 170) |
| **global, dev-val actions (median / p90)** | 13,991 (105 / 265), −0.87% | 9,029 (64 / 164), −0.21% |
| global vs control, programs better / same / worse | 61 / 8 / 31 | 45 / 14 / 41 |
| global_raw, dev-val actions | 14,811 | 9,925 |

**Control continuation.** It found no improving move: 779 and 907 trials, then a local optimum.
It reproduces the pinned baselines exactly, so the comparison isolates the global start.

**Bound certificate.** It comes from the best multipliers quantized to `floor(λ · 10^6)`, with
integer shortest paths, integer entry sums and an integer top-B:

| Width | Numerator | Denominator |
| --- | ---: | ---: |
| 128 | 32,699,366,807 | 10^6 |
| 256 | 21,214,526,897 | 10^6 |

It is a valid lower bound on the dev-fit selections of every dictionary made of the 96 characters
plus at most B pool entries. It says nothing about entries outside the pool, other sources, or
dev-val.

**Bound convergence.** Both widths ran all 4,000 iterations. By then the step size had shrunk to
0.004 and 0.002, and the bound rose only 49 and 4 over the last 1,000 iterations. It is close to
the strongest this relaxation can give.

**Correctness.** All 400 programs decode in every arm, and the whole-solution audit is clean.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| Λ1 | control reproduces the baseline on fit and dev-val | **Met** |
| Λ2 | certified bound ≥ 28,000 (128) and ≥ 19,000 (256), still more than 10% below the control's fit | **Met.** 32,700 and 21,215; 21.6% and 18.7% below |
| Λ3 | global_raw worse than control on fit | **Met.** +3.1% and +9.7% |
| Λ4 | global within 3% of control on fit | **Met.** −1.05% and −0.70% |
| Λ5 | no arm ready | **Met.** Best dev-val change −0.87%, against the 5% bar; 31 and 41 programs worse |
| Λ6 | everything decodes, audit clean | **Met** |
| Λ7 | no arm meets the M1 indicators | **Met.** Best median 64 |

## What it shows

- **A global start moves the search to a slightly better basin.** Exact local search from the
  Lagrangian primal ends 0.7–1.05% below the control on fit, but only 0.2–0.9% better on dev-val,
  with many programs worse. It is not a candidate. The control remains the incumbent.
- **The headroom question stays open, with a firmer scale.** For pool dictionaries, no
  256-entry dictionary can need fewer than 21,215 dev-fit selections. The best found needs 25,924,
  so the best possible improvement on fit is at most 18.2%.
  - That bound concerns total dev-fit selections. It does not bound the attainable median or
    p95, so it is not a statement about M1.
  - Whether any of that gap is attainable is not shown. The relaxation has plateaued, and a
    per-occurrence Lagrangian relaxation is known to be loose for problems of this kind, so most of
    the gap may be relaxation weakness rather than better dictionaries.
- **No scorer case.** Conventional global search did not demonstrate headroom.

Not claimed:
- M1;
- a universal lower bound (the certificate covers only pool dictionaries);
- attainability of the bound;
- any confirmation, BITS change, scorer or training.

Wording corrected on 2026-10-23 (Codex, gamma-team LOG 18:57Z): a total-selection bound is not
compared with M1's median target. No number changed.
