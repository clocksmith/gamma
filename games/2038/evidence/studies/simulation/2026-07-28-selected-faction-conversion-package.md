# Selected faction-conversion package

Date: 2026-07-28  
Evidence label: preregistered fresh-seed package-interaction simulation matrix  
Verdict: select the three-lever package for explicit physical-rule approval;
do not claim overall balance certification

## Identity

- Raw local report:
  `20260728T070150987Z-unified-matrix-audit-0-8-13-ab3289f35527-m3t4-selected-faction-conversion-package-v1-fresh-restart-202607-11998x4-unified-matrix-cli.json`
- Report SHA-256:
  `d3e59435445685c37f8268692f103092a87ba217e01a592ee6252327aa18503e`
- Source commit:
  `3011c25bc3b2d20a76692a746e66d71d4e100fe3`
- Source dirty: `false`
- Executable: `0.8.13`
- Engine: `selected-rules` `0.10.13`
- Physical candidate: `0.5.0-rc.14-test`
- Ruleset fingerprint:
  `sha256:ab3289f3552743367e0fa43d804f6621a424fedf22185b2a084f6ee53afcb7be`
- Preregistration: `selected-faction-conversion-package-v1`
- Root seed:
  `m3t4-selected-faction-conversion-package-v1-fresh-restart-20260728`
- Matrix matches: `11,998`
- Complete matches per arm: `5,964`
- Common-seed pairs: `5,964`
- Unmatched pairs: `0`
- Standing mismatches: `0`
- LLM calls: `0`

The package combined only three independently selected, faction-truth-safe
conversion levers:

1. Demis scores one Mandate at Capability 9 and 12; four rival institutions
   restore Capability 12's second Mandate.
2. Elon scores one Mandate only when Industrial Velocity actually reduces the
   price of a completed Facility.
3. Jensen receives New Architecture self-Compute only from accepted rival
   licenses, up to the canonical three-Compute ceiling.

This report validates the interaction of those levers. Their causal direction
comes from the isolated receipts.

## Validity

- Three-player matches: `4,168`
- Four-player matches: `3,952`
- Five-player matches: `3,808`
- Integrity violations: `0`
- Policy fallbacks: `0`
- Forced-no-op rate: `0.3793%`
- Registered homogeneous dominance cells: `0`
- Registered pairwise dominance cells: `0`
- Diagnostic pairwise dominance cells: `0`
- Credible meta cycles: `0`
- Matrix status: `inconclusive_precision_not_reached`
- Maximum core confidence-sequence half-width: `0.2523`

One diagnostic cell remained in the canonical arm: three-player Demis with the
greedy backend. The package removed rather than reproduced that signal. The
broad registered precision target was not reached.

## Faction standings

Candidate win shares and the range between the highest and lowest faction:

| Players | Sam | Mark | Demis | Elon | Dario | Jensen | Range |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 25.81% | 32.20% | 38.84% | 35.70% | 36.18% | 30.27% | 13.03 pp |
| 4 | 21.37% | 22.73% | 26.91% | 23.85% | 30.65% | 24.26% | 9.28 pp |
| 5 | 13.71% | 19.42% | 18.53% | 19.09% | 26.36% | 22.70% | 12.64 pp |

All three ranges are below the provisional `15` percentage-point faction
bound. Four-player results form a compact band around parity. Sam remains
policy-sensitive at five players; the prior controlled Power Broker evidence
shows that willing-partner skill is an intended, realizable bottleneck rather
than authority for an automatic Sam rules bonus.

## Paired focal movement

The deltas below compare the package with canonical rules on common seeds,
weighted over the registered weighted and greedy backends. A positive rank
delta means better placement.

| Faction | Players | Appearances | Win-share delta | Mandate delta | Rank delta |
| --- | ---: | ---: | ---: | ---: | ---: |
| Demis | 3 | 1,098 | -13.206 pp | -1.033 | -0.200 |
| Demis | 4 | 1,336 | -9.281 pp | -1.129 | -0.278 |
| Demis | 5 | 1,568 | -6.218 pp | -0.812 | -0.251 |
| Elon | 3 | 1,098 | +13.297 pp | +1.415 | +0.251 |
| Elon | 4 | 1,392 | +7.435 pp | +1.325 | +0.304 |
| Elon | 5 | 1,624 | +6.681 pp | +1.297 | +0.405 |
| Jensen | 3 | 986 | -4.412 pp | -0.319 | -0.085 |
| Jensen | 4 | 1,280 | -4.805 pp | -0.369 | -0.127 |
| Jensen | 5 | 1,568 | -3.922 pp | -0.375 | -0.145 |

Every selected lever continued in its isolated direction at every supported
player count.

## Faction truth and action choice

- Demis retained every point of Capability. Scientific Method preserved
  `1,787/2,009/2,296` Capability in the candidate at three, four, and five
  players. Research selections changed from `3,327/4,047/4,844` to
  `3,336/4,055/4,840`: no Research compulsion appeared.
- Elon received `1,580/1,969/2,224` Mandate from actual realized discounts.
  Build selections changed from `2,120/2,670/2,982` to
  `2,113/2,669/2,987`: the reward did not make Build materially more common.
- Jensen retained `457/960/1,521` accepted New Architecture licenses and the
  corresponding rival Compute and payments. His own Compute became
  `457/960/1,505`, so supplier value followed realized demand rather than an
  unconditional allocation.

## Diversity boundary

Action and opening diversity remain comfortably inside their provisional
bounds in every candidate count. No opening exceeds `12.2%`.

Winning-path top share also remains below its `55%` ceiling:

| Players | Action entropy | Opening entropy | Winning-path entropy | Winning-path top share |
| --- | ---: | ---: | ---: | ---: |
| 3 | 0.939 | 0.754 | 0.611 | 43.09% |
| 4 | 0.937 | 0.745 | 0.572 | 49.87% |
| 5 | 0.936 | 0.746 | 0.547 | 50.71% |

The four- and five-player winning-path entropy values are below the provisional
`0.60` floor, and the package makes them slightly lower than canonical. The
direct top-share guard still passes, and the package does not collapse action
selection. This is therefore a separate unresolved balance question, not a
reason to falsify the three faction-conversion effects or to claim that the
game is fully balanced.

## Decision

1. Select the three-lever package as the faction-conversion candidate.
2. Do not promote it into the physical rulebook without explicit user approval.
3. Do not describe the game as balance-certified: registered precision is
   incomplete and winning-path entropy is below its provisional floor at four
   and five players.
4. Make the unified audit enforce the diversity and faction-range bounds it
   already publishes before the next canonical audit.
5. Diagnose winning-path concentration separately before changing a global
   rule. No global economy, Grid-Ready, AGI, Realignment, Training, or Sam rule
   changes are justified by this package report.

## Surface audit

- Canonical rulebook and faction cards: unchanged.
- Semantic graph and generated data: unchanged.
- Simulator: package overlays and exact ability-value telemetry only.
- Browser prototype and Simulation Lab: canonical rules unchanged.
- Reference cards and player aids: unchanged.
- Tests: package classification, Capability preservation, actual-discount
  scoring, demand-coupled allocation, and diversity fields covered.
- Evidence documentation: this receipt and the balance summaries updated.
- Physical components and artwork: unchanged.

## Validity boundary

Deterministic policies do not establish human negotiation quality, perceived
faction identity, Realignment handling, fun, or memorable betrayal. Nor does a
package-interaction report replace the isolated causal receipts. Physical
promotion and balance certification remain separate decisions.
