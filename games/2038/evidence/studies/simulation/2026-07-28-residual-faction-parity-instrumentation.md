# Residual faction parity instrumentation correction

Date: 2026-07-28  
Evidence label: diagnostic result invalidated for ability attribution  
Physical-rule change: none

## Registered question

[`residual-faction-parity-v1.json`](preregistrations/residual-faction-parity-v1.json)
registered eight four-player, common-seed faction swaps before results. The
study asked whether the remaining Dario lead and Sam deficit were broad faction
effects or faction-by-policy effects.

## Raw archive

- Local report:
  `20260728T145041194Z-balance-audit-0-8-19-9efa959dbfba-m3t4-residual-faction-parity-v1-fresh-20260728-6400x4-faction-swap-cli.json`
- SHA-256:
  `32ddb97aa8f5fa3b0375a2e9b5189ed30990c6c3e8652b267732d255130fddc5`
- Games: 6,400
- Runs per arm: 400
- Player count: four
- LLM calls: zero
- Recorded source commit:
  `d5afe5249cf71423fab6b724e57b87aabaf65a88`
- Recorded source state: clean

## Valid result

The paired standings show strong backend sensitivity:

| Comparison | Win-share delta | Mandate delta | Rank advantage |
| --- | ---: | ---: | ---: |
| Dario vs Sam, Balanced/weighted | +10.250 pp | +1.3200 | +0.3700 |
| Dario vs Sam, Balanced/greedy | -3.250 pp | -0.7100 | -0.2400 |
| Dario vs Sam, Trust/weighted | +7.625 pp | +1.6075 | +0.4125 |
| Dario vs Sam, Power/weighted | +13.750 pp | +2.4450 | +0.5400 |
| Sam vs Mark, Power/weighted | +0.250 pp | -0.0275 | +0.0125 |
| Sam vs Mark, Power/greedy | +2.958 pp | +0.3275 | +0.2325 |
| Dario vs Mark, Balanced/weighted | +4.500 pp | +1.4100 | +0.3075 |
| Dario vs Mark, Balanced/greedy | -14.875 pp | -1.3700 | -0.5100 |

The sign reversals reject a universal Dario faction main effect. Sam is
approximately neutral against Mark when Power Broker pilots the focal seat.
These results do not support a printed Dario nerf or Sam buff.

## Invalid attribution

Every Dario arm reported an empty `abilityValues` object. Emergency Pause,
Audited Deployment, and Responsible Scaling changed match state but did not
publish their realized values through the shared faction-ability ledger.
Therefore this report cannot identify which Safety Laboratory mechanism caused
any standings delta. The standings remain descriptive; the ability-attribution
question is invalidated.

## Correction

The engine now records:

- Emergency Pause Runway spent, Trust gained, and Wild Action blocked.
- Audited Deployment Scrutiny removed and Deployments covered.
- Responsible Scaling offers, acceptances, rejections, Safety sold, Runway
  gained, and Trust gained.

A regression test exercises all three recording paths. The registered matrix
must be restarted on a new seed from a clean corrected source before any
ability-level interpretation or physical-rule proposal.

