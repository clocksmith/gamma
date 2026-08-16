# Exact-ecology package precision confirmation v1

**Date:** 2026-08-15

**Status:** automated simulation gate passed; explicit human approval required

**Game / rules / engine:** `0.14.7` / `0.8.0-rc.8-test` / `0.16.6`

**Source commit:** `146494995adf8b0d1534ba6363d8b9e8fad3aab7`

**Source state:** clean

## Question

Does the unchanged frozen exact-ecology strategy package preserve the prior
balance and profile-identity passes while reaching the unified matrix's
registered confidence-sequence precision target?

## Method

[`exact-ecology-package-precision-confirmation-v1.json`](preregistrations/exact-ecology-package-precision-confirmation-v1.json)
froze the exact Trust, Capacity, AGI, and Infrastructure profile artifacts,
fresh seeds, all supported player counts, fixed and variable Mandates, four
deterministic backend regimes, balanced faction and seat rotation, and the
canonical physical rules. Sampling could stop only after reaching the
registered `0.12` maximum core half-width or the `36,000`-match cap.

The run stopped at registered precision after `25,440` matrix matches and
seventy adversarial matches, for `25,510` matches total. The deterministic
backends were homogeneous weighted, homogeneous greedy, alternating weighted
first, and alternating greedy first. No rule overlay or post-result profile
tuning was used.

## Verdict

The package passed every preregistered automated simulation check. It is
eligible to be presented for explicit human approval, but is not yet promoted
to the canonical strategy catalog.

| Measure | Result | Bound |
| --- | ---: | ---: |
| Failed balance checks | 0 | 0 |
| Marginal dominance cells | 0 | 0 |
| Diagnostic dominance cells | 0 | 0 |
| Pairwise dominance cells | 0 | 0 |
| Diagnostic pairwise dominance cells | 0 | 0 |
| Integrity violations | 0 | 0 |
| Policy fallbacks | 0 | 0 |
| Maximum core half-width | 0.1191 | at most 0.1200 |

The machine status is `no_credible_dominance_at_registered_precision`, with
`precisionReached: true` and `automatedPass: true`. The report's remaining
promotion blockers are the tracked receipt supplied here and explicit human
approval. This receipt does not itself supply that approval.

## Supported-count results

| Players | Matches | Faction range | Seat range | Profile range | AGI emergence | Path entropy |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 8,560 | 8.82 pp | 0.91 pp | 12.57 pp | 15.47% | 0.6712 |
| 4 | 8,368 | 10.94 pp | 0.76 pp | 12.33 pp | 18.02% | 0.6345 |
| 5 | 8,512 | 10.36 pp | 2.38 pp | 10.49 pp | 21.48% | 0.6058 |

All action, opening, winning-path, fallback, and forced-no-op checks passed at
three, four, and five players. Action entropy remained between `0.9033` and
`0.9047`; opening entropy remained between `0.7171` and `0.7185`. The
five-player path-entropy result passed the registered `0.60` floor narrowly,
so human testing should continue to watch repeated strategic routes at five.

The registered three-player Infrastructure Compounder plus greedy-backend cell
won `39.58%` of `1,848` appearances. Its posterior mean was `39.38%`, with a
`37.17%–41.59%` posterior interval. It did not enter diagnostic dominance. The
same defect measured `60.76%` before exact-ecology Infrastructure training.

## Identity checks

- Infrastructure Compounder averaged `2.43` Builds per appearance and retained
  mean Mandate of `16.67 / 16.29 / 16.22` at three, four, and five players.
  Its authored unpowered-Generator and two-Facility transition rules were
  unchanged.
- Trust Governor averaged `1.73` Influence selections per appearance, while
  Research remained its largest Core Action at `3.86` selections per
  appearance. It reached Trust four in approximately `94.57%` of appearances
  and retained mean Mandate of `16.48 / 16.60 / 16.93`.
- Capacity Operator averaged `2.24` Builds and `6.65` combined Research and
  Deploy selections per appearance. Its mean Mandate was
  `16.86 / 16.78 / 17.06`.
- AGI Candidate supplied `2,436 / 4,660` AGI-declaration winner credits
  (`52.27%`), more than any other profile. Its mean Mandate was
  `14.97 / 15.13 / 15.36`, and AGI Dossier remained its largest Program action
  weight at `40.31`.

## Frozen strategy artifacts

| Profile | Source | SHA-256 |
| --- | --- | --- |
| Trust Governor | `2026-08-15-current-trust-evolution-v1.raw.json` | `a2a26d027b06d85c75178e6c6c468aa6ad3c5ae32b82292e3d84caeca173a462` |
| Capacity Operator | `proposals/capacity-operator-v1.json` | `186bb26d4eaf01fedbb03bb3e7e0ad89a4aa6e544dcf6737142be70a7672b6f7` |
| AGI Candidate | `proposals/full-ecology-agi-candidate-v1.json` | `3bca97e398eab032ae5befe322f266f67b21119ed68848f2cc2f4661016c94a6` |
| Infrastructure Compounder | `proposals/exact-ecology-infrastructure-candidate-v1.json` | `af0cefe1680c20469430dc94cfa78572ac6150d1e9e7234708a468e6872e3566` |

## Result artifacts

- Seed: `mandate-2038-exact-ecology-package-precision-confirmation-v1`
- Raw report:
  `2026-08-15-exact-ecology-package-precision-confirmation-v1.raw.json`
- Local archive:
  `20260816T085423771Z-unified-matrix-audit-0-14-7-03ac2fbdec61-mandate-2038-exact-ecology-package-precision-confirmation-v1-25510x4-unified-matrix-cli.json`
- Raw and archive SHA-256:
  `e07d51ca114784a4cbdc375ded22b6f412f19fa78771ca4ec82620e15169ba20`

## Audited surfaces

- Canonical rulebook: no change.
- Machine-readable physical mechanics: no change.
- Starting resources and faction setup: no change.
- Core Actions and legal action resolution: no change.
- Scoring and Mandate thresholds: no change.
- Browser prototype: no change.
- Reference cards and player aids: no change.
- Physical component specification: no change.
- Simulator: no post-result change; executable `0.14.7` retained exact strategy
  artifact provenance for this run.
- Strategy catalog: no change pending explicit human approval.
- Playtest documentation: this dated receipt records the result and limits.

## Decision boundary

Do not change starts, Core Actions, scoring, factions, or physical rules from
this result. Their registered ranges and integrity checks passed. The measured
imbalance was corrected by the frozen strategy package, principally the
Infrastructure Compounder's decision weights and transitions, without changing
the game players receive.

Simulation cannot establish human counterplay, negotiation quality, fun,
teachability, duration, table readability, or physical handling. A promotion
would mean that these four profiles become the canonical automated playtest
ecology; it would not certify the game as permanently or universally balanced.
