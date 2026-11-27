# Winning-path margin validity

Date: 2026-07-28  
Evidence label: preregistered fresh-seed telemetry diagnostic  
Verdict: exact-tie classification materially undercounts mixed winners, but
Infrastructure Compounder fails construct validity and must be diagnosed before
the balance gate can be reinterpreted

## Identity

- Raw local report:
  `20260728T084937777Z-unified-matrix-audit-0-8-17-ab3289f35527-m3t4-winning-path-margin-validity-v1-fresh-20260728-7990x4-unified-matrix-cli.json`
- Report SHA-256:
  `b2305bf1c957dcda638f0710724199eec25d5f1bca66e3db7eca2d4887f1bb61`
- Source commit:
  `1a92071be6832912b91056794424074498e38b3c`
- Source dirty: `false`
- Executable: `0.8.17`
- Engine: `selected-rules` `0.10.17`
- Physical candidate: `0.5.0-rc.18-test`
- Ruleset fingerprint:
  `sha256:ab3289f3552743367e0fa43d804f6621a424fedf22185b2a084f6ee53afcb7be`
- Preregistration: `winning-path-margin-validity-v1`
- Root seed: `m3t4-winning-path-margin-validity-v1-fresh-20260728`
- Matrix matches: `7,990`
- Complete matches per arm: `3,960`
- LLM calls: `0`

## Integrity

- Integrity violations: `0`
- Policy fallbacks: `0`
- Registered or diagnostic dominance cells: `0`
- Registered or diagnostic pairwise dominance cells: `0`
- Source clean: `true`
- Registered precision reached: `false`
- Maximum core confidence-sequence half-width: `0.2980`

The smaller diagnostic run also placed the package faction range barely outside
the provisional bound at three (`15.16` points) and five (`16.29`), while four
remained inside (`12.41`). Those results do not replace the larger
`11,998`-game package estimate; this study was registered for classifier
validity.

## Margin result

The preregistered artifact threshold was at least `25%` of five-player
candidate winner credit within one lane-score point. The observed share was
`56.70%`.

| Players | Mean top–second gap | Exact ties | Within 0.5 | Within 1 | Within 2 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 3 | 1.258 | 18.86% | 27.19% | 58.90% | 84.32% |
| 4 | 1.292 | 19.28% | 25.83% | 56.48% | 84.85% |
| 5 | 1.340 | 19.08% | 23.04% | 56.70% | 83.58% |

The current categorical classifier recognizes only exact ties as hybrids. It
therefore labels more than one third of all candidate winners pure even though
their second lane lies within one meaningful action/resource point.

At five players, the most common primary-to-secondary pairs were:

- Adoption → Research: `474.0` winner credit.
- Research → Adoption: `434.5`.
- Research → Legitimacy: `75.5`.
- Adoption → Legitimacy: `72.5`.
- Research → Infrastructure: `61.0`.
- Adoption → Infrastructure: `55.0`.

This confirms a material exact-tie artifact. It does not by itself prove that
every desired strategic identity is viable.

## Persona construct validity

Three authored specialists align strongly with their intended lane as either
primary or secondary:

- Capability Rusher: Research in `96.7%` of winner credit.
- Market Maximalist: Adoption in `97.9%`.
- Trust Governor: Legitimacy in `66.2%`.

Infrastructure Compounder does not:

- Infrastructure primary: `3.0/221.0` winner credit.
- Infrastructure secondary: `26.0/221.0`.
- Infrastructure present in the top two: only `13.1%`.
- Its wins are principally Research with Adoption second.

The preregistration says failed persona construct validity must not be used to
reinterpret the gate. The exact-tie classifier is brittle, but the
Infrastructure policy or lane definition is also wrong.

## Decision

1. Keep the physical game and four-lever package unchanged.
2. Do not lower the entropy threshold or retroactively relabel this package a
   pass.
3. Diagnose Infrastructure Compounder's authored action weights, target
   scoring, and realized decisions.
4. Determine whether the policy fails to pursue legal infrastructure or
   whether infrastructure is correctly functioning as support that the lane
   formula mismeasures.
5. Correct and fresh-seed-validate the policy/diagnostic owner before any new
   physical scoring proposal.

## Surface audit

- Physical rulebook, cards, semantic graph, generated gameplay data, browser
  game, and reference aids: no mechanical change.
- Simulator: added top-versus-second winner lane margin telemetry.
- Tests: winner credit is complete and margin shares must be monotonic across
  exact, half-point, one-point, and two-point thresholds.
- Evidence: raw report archived locally; this receipt records the preregistered
  interpretation and the failed construct-validity condition.
- Playtest documentation: unchanged because no rule candidate was promoted.

## Validity boundary

Lane scores are descriptive summaries of decisions and end state, not causal
values of actions. This diagnostic cannot establish human strategy,
negotiation, timing, or fun.
