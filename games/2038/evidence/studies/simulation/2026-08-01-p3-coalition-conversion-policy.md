# Three-player Coalition conversion-policy isolation

**Date:** 2026-08-01 (America/New_York)  
**Verdict:** `persistent_conversion_warning_policy_not_corrective`  
**Rule decision:** No canonical rule change. Do not promote the treatment as the
baseline deterministic Coalition policy.

## Question and frozen identity

This preregistered study asked whether a bounded deterministic policy that
deliberately spends causally necessary Deal Flow Runway on infrastructure closes
Coalition Lab's three-player warning without changing a rule.

- Preregistration: `p3-coalition-conversion-policy-v1`
- Preregistration fingerprint:
  `sha256:5d4987341a8fe3b85c408709b952389336cd6ac80452373ef6260c82003c1a22`
- Source commit: `e7df6e213eaea516aacd1612b925d65510c66bf2`
- Source state: clean detached checkout
- Executable: `0.8.34`
- Physical candidate wrapper: `0.5.0-rc.34-test`
- Engine: `selected-rules` `0.10.33`
- Ruleset fingerprint:
  `sha256:794cc2c34eb745b4fc88a997e1c9000f4fd496e8cff0e4a8fa7a5c23da5f65df`
- Mechanics fingerprint:
  `sha256:177bd5d41de561ee92a86154f7a7df999c1b5da97586e39f594ca9f5762dcabe`
- Engine fingerprint:
  `sha256:3604d37947fdc0f9841640cba0d83935e9915522ee18ad88ddb5760dafe1c2a7`
- Variant: canonical, empty overlay; variant fingerprint
  `sha256:1ac3e84d078271ff8dcf682d158e433818b8b4fad8df5c84f6a7c14ec6a7d4dc`
- Seed: `frontier-2038-p3-coalition-conversion-policy-2026-08-01-v1`
- Mandates: variable
- Projection: batch
- Profiles: focal `balanced_operator`; opponents `capability_rusher` and
  `trust_governor`
- Backends: homogeneous greedy and homogeneous weighted fields
- LLM calls: zero

The matrix contained five comparator rosters, all three focal seats, and both
deterministic backends: 30 cells. Each cell ran 200 exact common-seed pairs,
for 6,000 pairs and 12,000 complete matches. Thirty-one outer worker threads
ran one inner simulator worker per arm. Result ordering was restored by
comparison, arm, and match index. No match was quarantined.

Raw report:
`evidence/studies/simulation/2026-08-01-p3-coalition-conversion-policy-v1.raw.json`

Raw SHA-256:
`23edca7778f07f156af9a8205b83fba3a01276b5ea8c0ba10ec809902e52b745`

The automatic frozen-checkout archive has identical bytes and hash:
`20260802T013001323Z-balance-audit-0-8-34-794cc2c34eb7-frontier-2038-p3-coalition-conversion-policy-2026-08-01-v1-12000x3-faction-swap-cli.json`.

## Primary paired result

Effects are treatment minus null-treatment baseline for the same Coalition
seat, factions, profiles, backend, Mandate draw, board, and seed. Two-sided 98%
Student-t intervals use 5,999 degrees of freedom for the aggregate result.

| Outcome | Mean effect | 98% interval | Half-width | Registered precision |
|---|---:|---:|---:|---:|
| Coalition Mandate | -0.313 | [-0.411, -0.215] | 0.098 | <= 0.500 |
| Coalition win credit | -1.15 pp | [-2.04, -0.26] pp | 0.89 pp | <= 3.00 pp |
| Coalition rank advantage | -0.033 | [-0.050, -0.015] | 0.017 | descriptive |
| Causally necessary Deal Flow spend | +0.104 | [+0.086, +0.122] | 0.018 | activation >= +0.100 |
| Synchronous attributed Mandate | +0.014 | [+0.002, +0.025] | 0.011 | mechanism only |

Precision was reached. The behavior-activation gate passed narrowly: the
treatment caused more Deal Flow credit to be spent through legal economic
actions. The policy-correction gate failed in the opposite direction because
Mandate, win credit, and rank all worsened with intervals below zero.

The registered persistent-warning gate passed. Its activation and precision
conditions were met; the upper Mandate endpoint was below +1; and no seat,
comparator, or backend reversal explained the aggregate. This gate permits a
later one-lever rules experiment. It does not promote or prove a rule change.

## Backend, seat, and comparator pattern

Greedy treatment and control were exactly identical in all 3,000 pairs. The
greedy policy already chose the same highest-ranked decisions, so the
multipliers changed no decision or outcome.

The weighted field activated and worsened:

- Mandate: -0.626, 98% interval [-0.821, -0.431].
- Win credit: -2.30 points, 98% interval [-4.08, -0.52].
- Rank advantage: -0.065, 98% interval [-0.100, -0.030].
- Necessary Deal Flow spend: +0.208, 98% interval [+0.173, +0.243].
- Synchronous attributed Mandate: +0.027, 98% interval [+0.004, +0.050].

All seat means were negative: seat zero -0.312 Mandate, seat one -0.353, and
seat two -0.274. All comparator means were also negative: Platform -0.288,
Imperial -0.208, Vertical -0.279, Safety -0.371, and Foundry -0.418. These are
descriptive families and are not separate multiplicity-adjusted claims.

## Causal telemetry

In the 3,000 weighted treatment games, Coalition earned 7,749 Deal Flow
credits, spent 2,903, and used 1,235 as causally necessary economic funding.
The weighted baseline earned 7,583, spent 2,198, and used 611 causally. Thus
the treatment substantially changed the intended mechanism while still
leaving most earned credits unspent.

The main treatment-minus-baseline necessary-spend changes were:

- Build Facility: 698 versus 273 credits;
- Build Link: 117 versus 34;
- Build Generator: 60 versus 30;
- Mega-Cluster lead payment: 66 versus 36;
- Fusion Demonstrator: 182 versus 157;
- Research Training: 73 versus 65; and
- Recruit: 24 versus 5.

Synchronous Mandate attribution rose from 196 to 278 points, but attributed
Mandate per necessary credit fell from 0.321 to 0.225. In the 762 weighted
pairs where treatment increased necessary credit use, its mean Mandate effect
was -0.894 and win-credit effect was -3.54 points. More spending was therefore
real, but the treatment traded away higher-value timing and action choices.

## Interpretation and decision

This rejects the proposed deterministic intervention. "Spend Deal Flow Runway
more aggressively on infrastructure" is not a corrective explanation for
Coalition's three-player warning. Greedy play was already invariant; weighted
play converted more credits but performed worse. The result is consistent
with opportunity cost, sequencing, and downstream conversion quality mattering
more than raw Runway accumulation or spend count.

It does not prove Coalition's faction rules are underpowered. The treatment is
a deliberately narrow authored policy, not an optimal policy or human
negotiator. A harmful treatment cannot establish that the legal game lacks a
better conversion path.

No rule should change now. If a rules experiment is pursued later, it must be
newly preregistered and alter one Deal Flow conversion lever only; it must not
be silently folded into the canonical candidate. A direct unconditional point
for trading is not supported because it could reward empty trades and bypass
the conversion question. Controlled human faction-and-seat rotation remains
the strongest next independent evidence.

## Exclusions and boundaries

- The earlier strict LLM negotiation study is not pooled.
- Pre-`0.8.34` deterministic matrices are historical context, not part of this
  frozen population.
- Adversarial diagnostics are not pooled balance evidence.
- AGI-route evidence is outside this question.
- The study compares one policy overlay with its null control. It does not
  estimate absolute faction balance or qualify three-player balance.
- "No detected reversal" applies only at this study's declared precision and
  policy population.

## Affected-surface audit

- Canonical rulebook: no legal or numerical rule change; synchronized version
  wrapper only.
- Machine-readable rules and content graph: no mechanical change.
- Simulator: added conservative Deal Flow credit attribution, synchronous
  conversion context, named deterministic treatment, common-seed treatment
  arms, batch projection, and bounded outer-worker reporting.
- Browser rules and state transitions: no gameplay change; displayed build
  identity advanced to `0.8.34`.
- Reference cards and player aids: no gameplay change; release identity only.
- Tests: causal ledger, policy scoring, treatment identity, matrix coverage,
  batch/rich parity, and bounded parallel execution pass.
- Playtest documentation: treatment and causal interpretation boundary added.
- Physical rules: no rule selected or promoted.

Before release, a 30-match `0.8.33` versus `0.8.34` common-seed replay audit
matched every winner, standing, and match metric after removing only the new
Deal Flow telemetry and version-bound scope text. The complete release gate
then passed: 182 tests, `npm run check`, and `git diff --check`.
