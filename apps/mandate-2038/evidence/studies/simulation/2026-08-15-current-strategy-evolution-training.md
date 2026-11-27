# Current-rule strategy evolution training

**Date:** 2026-08-15  
**Status:** two champions nominated for a fresh-seed holdout  
**Game / rules:** `0.14.2` / `0.8.0-rc.3-test`  
**Source commit:** `cb5f1529`  
**Source state:** clean

## Question

Are Trust Governor and Power Broker weak because the physical rules make their
lanes noncompetitive, or because their deterministic profiles became stale
after the Default-game and nineteen-hex simplifications?

## Method

Two independent four-player training jobs evaluated six generations of eight
candidates. Every candidate played 24 games in each seat against the current
canonical opponents under the weighted backend. Mutation changed only action,
decision, and negotiation weights. It could not change rules, starts, scoring,
legal actions, conditional rules, resource values, or hidden information.

## Training observations

| Profile | Authored baseline | Final champion | Best sampled generation |
| --- | ---: | ---: | ---: |
| Trust Governor | 13.54% | 31.25% | 32.81% |
| Power Broker | 23.96% | 38.02% | 41.67% |

Trust's champion reduced its global Influence weight from `4.065` to `1.406`
while increasing Research, Deploy, and Mega-Cluster. Power's champion reduced
Build from `10.201` to `3.268` and increased Research and Deploy. These are
diagnostic signs: the current authored profiles overpay for their named
behavior. The Power profile is especially stale because its defining sale is
unavailable in Default Game.

Training rates are not balance evidence. The champions may be overfit, and the
Power result may describe a competitive generic operator rather than a valid
Power Broker. They advance only to a committed fresh-seed holdout.

## Artifacts

- Trust seed: `mandate-2038-current-trust-evolution-v1`
- Trust raw report: `2026-08-15-current-trust-evolution-v1.raw.json`
- Trust SHA-256:
  `a2a26d027b06d85c75178e6c6c468aa6ad3c5ae32b82292e3d84caeca173a462`
- Power seed: `mandate-2038-current-power-evolution-v1`
- Power raw report: `2026-08-15-current-power-evolution-v1.raw.json`
- Power SHA-256:
  `be77914d441b9b7b46e18c5b1be9ce82c5f012cddc8b64595e5e038c4ba9212a`

## Surface audit

- Physical rules, semantic graph, browser, cards, and starts: unchanged.
- Canonical profiles: unchanged pending fresh-seed evidence.
- Simulation: existing strategy-evolution path only.
- Next authority: `current-strategy-holdout-v1`.

This study tests policy quality. It cannot establish physical balance,
teachability, negotiation quality, or fun.
