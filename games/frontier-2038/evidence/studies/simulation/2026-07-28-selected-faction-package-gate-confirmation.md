# Selected faction package — enforced-gate confirmation

Date: 2026-07-28  
Evidence label: preregistered fresh-seed package-interaction simulation matrix  
Verdict: faction package confirmed; overall balance gate correctly remains red
on winning-path diversity

## Identity

- Raw local report:
  `20260728T073159099Z-unified-matrix-audit-0-8-14-ab3289f35527-m3t4-selected-faction-package-gate-confirmation-v1-fresh-2026072-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `94f5e80ac4e343fa8460009cc24abe9a06d8d3cdf43a04fb25f2911073dd85df`
- Source commit:
  `f7ddd98479b7abf2381384120ed216d5265c90d0`
- Source dirty: `false`
- Executable: `0.8.14`
- Engine: `selected-rules` `0.10.14`
- Physical candidate: `0.5.0-rc.15-test`
- Ruleset fingerprint:
  `sha256:ab3289f3552743367e0fa43d804f6621a424fedf22185b2a084f6ee53afcb7be`
- Preregistration: `selected-faction-package-gate-confirmation-v1`
- Root seed:
  `m3t4-selected-faction-package-gate-confirmation-v1-fresh-20260728`
- Matrix matches: `11,998`
- Complete matches per arm: `5,964`
- LLM calls: `0`

## Gate result

- Status: `outside_provisional_bounds`
- Integrity violations: `0`
- Policy fallbacks: `0`
- Registered homogeneous dominance cells: `0`
- Diagnostic dominance cells: `0`
- Registered and diagnostic pairwise dominance cells: `0`
- Credible meta cycles: `0`
- Registered precision reached: `false`
- Maximum core confidence-sequence half-width: `0.2523`

Exactly three enforced checks failed:

| Players | Winning-path entropy | Floor |
| --- | ---: | ---: |
| 3 | 0.5711 | 0.60 |
| 4 | 0.5998 | 0.60 |
| 5 | 0.5350 | 0.60 |

The corrected evaluator therefore converted a previously implicit limitation
into an explicit red verdict. It did not allow acceptable dominance intervals
or faction parity to hide a declared path-diversity failure.

## Faction package confirmation

The package passed every faction-range check:

| Players | Faction range | Highest | Lowest |
| --- | ---: | --- | --- |
| 3 | 13.41 pp | Demis 38.87% | Sam 25.46% |
| 4 | 12.19 pp | Dario 31.29% | Sam 19.10% |
| 5 | 13.36 pp | Dario 25.99% | Sam 12.63% |

The four-player result remains a compact competitive band. Three and five
remain inside the provisional `15`-point guard.

Common-seed focal movement also reproduced:

| Faction | Players | Win-share delta | Mandate delta | Rank delta |
| --- | ---: | ---: | ---: | ---: |
| Demis | 3 | -11.584 pp | -1.037 | -0.197 |
| Demis | 4 | -9.859 pp | -1.202 | -0.295 |
| Demis | 5 | -6.696 pp | -0.792 | -0.260 |
| Elon | 3 | +10.897 pp | +1.342 | +0.234 |
| Elon | 4 | +9.714 pp | +1.329 | +0.321 |
| Elon | 5 | +6.096 pp | +1.281 | +0.367 |
| Jensen | 3 | -4.643 pp | -0.339 | -0.097 |
| Jensen | 4 | -3.183 pp | -0.328 | -0.107 |
| Jensen | 5 | -4.560 pp | -0.400 | -0.147 |

Demis preserved full Capability and changed Research selection by only
`+7/+7/+5`. Elon changed Build selection by `+5/+9/+17` across cohorts of
`1,092/1,400/1,624` appearances. Jensen retained essentially identical rival
license demand: `473→474`, `946→941`, and `1,477→1,473`.

## What the path result actually says

The winning path with the largest share is Adoption:

| Players | Adoption | Research | Largest hybrid | Top-share bound |
| --- | ---: | ---: | ---: | ---: |
| 3 | 46.53% | 29.32% | Research–Adoption 9.51% | 55% |
| 4 | 46.28% | 28.07% | Research–Adoption 14.26% | 55% |
| 5 | 50.53% | 27.78% | Research–Adoption 15.05% | 55% |

Every top-share check passes. The entropy failure arises because two major
lanes dominate while several classified hybrid and support lanes are rare. It
does not show an action collapse: action entropy is `0.938/0.937/0.935`, and
opening top share is only `12.21%/12.12%/12.35%`.

This is a genuine strategic-diversity diagnostic, but not yet a rule diagnosis.
The current report does not attribute winning Mandate sources and action
profiles to each path, so it cannot distinguish:

1. Customer scoring being too efficient;
2. infrastructure and legitimacy functioning as support rather than visible
   winning identities;
3. the winner classifier splitting rare hybrids too finely; or
4. deterministic policies undervaluing a legal counter-line.

## Decision

1. Keep the three faction-conversion levers selected for explicit physical
   approval.
2. Keep overall balance status red.
3. Add winner-path Mandate-source, action, faction, and outcome telemetry before
   proposing a global rule lever.
4. Preregister the diagnostic on fresh seeds.
5. Do not change Sam, Grid-Ready, AGI, Realignment, Training, or the economy
   from this report.

## Surface audit

- Physical rulebook, faction cards, semantic graph, and generated game data:
  unchanged.
- Simulator and immutable executable: corrected outcome checks only.
- Browser prototype and Simulation Lab: canonical gameplay unchanged.
- Evidence: this receipt records the fresh enforced-gate run.
- Tests: `106/106` passed before execution; release and content gates passed.

## Validity boundary

The package remains a simulation-selected candidate, not an automatically
promoted physical rule. The path diagnosis remains deterministic-policy
evidence. Human negotiation, comprehension, perceived choice, and memorable
betrayal still require the controlled physical test.
