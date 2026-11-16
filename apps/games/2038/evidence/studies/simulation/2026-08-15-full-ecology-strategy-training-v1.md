# Full-ecology strategy training v1

**Date:** 2026-08-15  
**Status:** AGI Candidate nominated; Trust Governor rejected  
**Game / rules / engine:** `0.14.5` / `0.8.0-rc.6-test` / `0.16.4`  
**Source commit:** `aaa894b75989d5e88873dcfc3d42403d899ebbda`  
**Source state:** clean

## Question

Can AGI Candidate and Trust Governor approach neutral win share across the full
three-, four-, and five-player opponent ecology while preserving their named
strategy and leaving the physical game unchanged?

## Frozen method

[`full-ecology-strategy-training-v1.json`](preregistrations/full-ecology-strategy-training-v1.json)
registered two independent five-generation, six-candidate jobs. Each candidate
played twelve matches from every focal seat at each supported player count.
Those matches were divided evenly across all six circular opponent windows, so
every non-target profile appeared equally. Candidate ordering minimized the
largest miss from `1 / player count`, then mean miss, then ordinary fitness.

Each job evaluated 4,320 matches. Mutation could change action, decision, and
negotiation weights. It could not change setup, factions, Core Actions, legal
actions, scoring, Dossier requirements, or physical components.

## AGI Candidate

| Measure | Authored baseline | Training nominee |
| --- | ---: | ---: |
| Largest supported-count miss | 6.67 pp | 5.00 pp |
| Mean supported-count miss | 4.77 pp | 3.98 pp |
| Three-player win share | 38.89% | 30.56% |
| Four-player win share | 27.08% | 20.83% |
| Five-player win share | 26.67% | 25.00% |
| Three-player mean score | 15.28 | 15.61 |
| Four-player mean score | 15.19 | 15.90 |
| Five-player mean score | 14.13 | 17.32 |

The nominee is the only evaluated candidate that both improved the baseline's
largest miss and retained a mean score of at least fourteen at every supported
count. Dossier remains its largest Program weight (`40.310`), ahead of Agent
Swarm (`4.749`) and every other Program. It advances only to a fresh holdout.

## Trust Governor

| Measure | Authored baseline | Final training champion |
| --- | ---: | ---: |
| Largest supported-count miss | 8.33 pp | 3.33 pp |
| Mean supported-count miss | 6.32 pp | 1.11 pp |
| Three-player win share | 25.00% | 33.33% |
| Four-player win share | 17.71% | 25.00% |
| Five-player win share | 16.67% | 16.67% |
| Three-player mean score | 14.75 | 15.97 |
| Four-player mean score | 15.04 | 15.04 |
| Five-player mean score | 15.07 | 15.35 |

The final champion retained Influence and scrutiny-removal preferences and was
competitively closer to neutral. It failed the preregistered score floor of
sixteen at all three counts. No evaluated Trust candidate both improved the
baseline's largest miss and passed every score floor. Trust Governor is
therefore rejected rather than nominated for another adaptive run.

## Artifacts

- AGI raw report: `2026-08-15-full-ecology-agi-training-v1.raw.json`
- AGI SHA-256:
  `3090d31535178e92177536640ddf911134cbe110b1bc25eaf5a377983e43940c`
- AGI proposal:
  `proposals/full-ecology-agi-candidate-v1.json`
- Trust raw report: `2026-08-15-full-ecology-trust-training-v1.raw.json`
- Trust SHA-256:
  `2d48b0e4647eb00598f2dbeafe426e8be78b20994e3e3eb54e9120ae0df1f0a8`

## Decision boundary

This training result nominates one AGI policy artifact. It does not promote a
profile or establish game balance. The AGI proposal must be frozen by hash
before one fresh-seed unified holdout. Trust remains the previously frozen
candidate used by the corrected ecology study. Starting resources and Core
Actions remain unchanged because faction and seat ranges passed, while this
study changed only simulated policy.

Simulation cannot establish human counterplay, fun, negotiation quality,
teachability, duration, or physical handling.
