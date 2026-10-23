# mip-lns-v1: exact LNS cuts dev-fit selections 1.4% / 3.3% and dev-val actions 0.9% / 2.6%; not ready

## Provenance

- **Design:** [FREEZE.md](FREEZE.md) (`825400377`) plus pre-launch [amendment 1](AMENDMENT-1.md)
  (`2aff1872e`: full-capacity repairs, solver-objective checks, live receipts). Codex reviewed and
  approved both (gamma-team LOG 19:03Z and 19:04Z).
- **Run:** one launch, two width processes pinned to cores 28–29 and 30–31, both exited 0.
- **Evidence:** [evidence/results.json](evidence/results.json) holds per-arm aggregates, per-problem
  dev-val actions, the full fit trajectory of every move (status, exact score, acceptance), dictionary
  hashes and seal hashes. Dictionaries and pool strings stay private.
- **Independent replay:** Codex replayed the live receipts against the canonical `literals.py`
  encoder and `bitpack` (LOG 20:15Z; script SHA `bee93f51...`, receipt kept privately). It checked all
  27 accepted incumbents up to that snapshot:
  - recorded exact and solver objectives;
  - legal capacity and fallback;
  - body exclusion and two-owner support;
  - strict monotone acceptance.

  The replay covers the LNS snapshot only, not the later moves or the polish.

## Result

| | 128 entries | 256 entries |
| --- | ---: | ---: |
| LNS moves / accepted | 27 / 6 | 54 / 26 |
| Solver status (optimal / time limit) | 22 / 5 | 53 / 1 |
| **Dev-fit selections: control → lns (after polish)** | 41,684 → **41,096 (−1.41%)** | 26,108 → **25,258 (−3.26%)** |
| lns_raw (no polish) dev-fit | 41,134 | 25,268 |
| **Dev-val actions: control → lns** | 14,114 → **13,991 (−0.87%)** | 9,048 → **8,814 (−2.59%)** |
| Median / p90 actions | 104.5 → 103.5 / 268 → 265 | 64.5 → **65.5 (worse)** / 170 → 159 |
| Programs better / same / worse | 67 / 3 / 30 | 33 / 22 / **45** |
| Single-character fraction | 78.67% → 78.30% | 55.14% → 54.87% |
| Package bytes | 17,225 → 17,138 | 15,255 → **15,744 (+3.2%)** |

**Control continuation.** It finds no improving move (779 and 907 trials) and reproduces both
pinned baselines exactly.

**Polish.** It adds little after LNS: 38 and 10 fit selections. Every polish stopped at a local
optimum, and all 400 programs decode in every arm.

## Predictions (scored as frozen)

| | Prediction | Outcome |
| --- | --- | --- |
| L1 | control reproduces the baselines on fit and dev-val | **Met** |
| L2 | LNS improves fit by at least 1.5% at 256 and at least 0.5% at 128 | **Met.** 3.26% and 1.41% (after polish) |
| L3 | lns beats control on dev-val at both widths, but by less than 5% | **Met.** −2.59% and −0.87% |
| L4 | everything decodes, audit clean | **Met** |
| L5 | no M1 indicator met | **Met** |

## Readiness (frozen bar, against the pinned L-R baseline)

Neither width is ready.

| Width | Actions | Median / p90 | Better / worse | Fraction | Package |
| --- | --- | --- | --- | --- | --- |
| 128 | 0.87% fewer (needs 5%) | both lower | 67 better (needs 60) / 30 worse (allowed 25) | lower | lower |
| 256 | 2.59% fewer (needs 5%) | median one action worse | 33 better / 45 worse | lower | 3.2% higher (within 105%) |

## What it shows

**Exact search finds better dictionaries at full scale.** The exact repairs found dictionaries 3.3%
better on 256-entry dev-fit selections than the shared local search's optimum. That confirms the
[mip-audit-v2](../mip-audit-v2/README.md) sub-instance result at the full 300 programs. The solver
proved most repairs optimal within its tolerances, and acceptance always rested on exact canonical
rescoring.

**About 80% of the 256-entry fit gain carries to the dev-val total, but its distribution worsens.**
More programs got worse than better, and the median rose by one action. The gain is concentrated in
some programs, so fitting harder on dev-fit trades breadth for total. At 128 entries the gain is
smaller but broad: 67 programs better against 30 worse.

**It is not a candidate,** and it does not touch M1. It does show where conventional search still
has room. Gamma-team board item 15, agreed with Codex, stacks these repairs onto item 13's ready naming candidate, under the readiness and successor
rules.

**No scorer case.** This is conventional search, and scorer training would still need the owner.
