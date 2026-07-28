# Residual faction parity restart

Date: 2026-07-28  
Evidence label: clean corrected diagnostic  
Verdict: no universal faction correction nominated

## Registered evidence

- Preregistration:
  [`residual-faction-parity-v1-restart.json`](preregistrations/residual-faction-parity-v1-restart.json)
- Local raw report:
  `20260728T150423583Z-balance-audit-0-8-19-9efa959dbfba-m3t4-residual-faction-parity-v1-restart-fresh-20260728-6400x4-faction-swap-cli.json`
- Raw report SHA-256:
  `4d9c1bef8216068166fcfcfae4dd90e63bb2654894458004c6dfa95dd342157d`
- Games: 6,400
- Runs per arm: 400
- Player count: four
- LLM calls: zero
- Source commit:
  `d9d2766ceb4fd36a7d365acba8e21bacb36c8fd2`
- Source dirty: false
- Engine fingerprint:
  `sha256:880e0e5b113113ea174cde1da1458a6a733348011e849818bdfdc22920b90e79`

The physical mechanics are the canonical four-lever package. This diagnostic
changes no playable rule.

## Paired results

| Comparison | Win-share delta | Mandate delta | Rank advantage |
| --- | ---: | ---: | ---: |
| Dario vs Sam, Balanced/weighted | +13.375 pp | +2.4475 | +0.5125 |
| Dario vs Sam, Balanced/greedy | -4.500 pp | -0.7125 | -0.2925 |
| Dario vs Sam, Trust/weighted | +9.125 pp | +1.5325 | +0.3400 |
| Dario vs Sam, Power/weighted | +9.250 pp | +1.9450 | +0.4550 |
| Sam vs Mark, Power/weighted | -0.500 pp | -0.5100 | -0.0600 |
| Sam vs Mark, Power/greedy | +1.958 pp | +0.4800 | +0.2525 |
| Dario vs Mark, Balanced/weighted | +5.625 pp | +1.2150 | +0.2425 |
| Dario vs Mark, Balanced/greedy | -9.500 pp | -1.3075 | -0.4975 |

## Ability realization

The corrected ledger confirms that Dario’s abilities were active:

- Balanced/weighted Dario removed 445 Scrutiny through Audited Deployment,
  invoked Emergency Pause 398 times, and completed 38 Responsible Scaling
  sales.
- Greedy Dario removed 710 Scrutiny and invoked Emergency Pause in all 400
  games, but completed no Responsible Scaling sales.
- Against Mark, balanced/weighted Dario completed 55 Responsible Scaling sales;
  greedy Dario completed none.

Emergency Pause usually reached an existing Trust cap: it blocked one Wild
Action in nearly every game while adding only 0–39 total Trust per 400-game
arm. Its frequent use is real but does not explain the direction reversal,
because both backends invoked it at almost identical rates.

## Interpretation

The Dario comparison reverses sign under the greedy backend against both Sam
and Mark. A universal printed Dario nerf would therefore correct the weighted
policy while worsening the greedy matchup. That fails the preregistered
main-effect criterion.

Sam is approximately neutral against Mark when piloted by Power Broker:
`-0.500` percentage points under weighted selection and `+1.958` under greedy.
This confirms that Sam’s negotiation economy can convert under a compatible
strategy and does not justify a universal printed buff.

The remaining variation is faction-by-policy behavior, not evidence of an
unconditional faction loophole. No physical rule is nominated from this
diagnostic.

## Balance decision

Retain the canonical faction stats and four-lever package unchanged. The
existing registered three-, four-, and five-player confirmation remains the
balance authority: its bounds passed, no strategy or faction dominance was
registered, and its verdict remained `inconclusive_precision_not_reached`
because interaction intervals require physical evidence.

The corrected ability telemetry is eligible for promotion as an executable
evidence improvement. It must not be described as a new balance rule.

