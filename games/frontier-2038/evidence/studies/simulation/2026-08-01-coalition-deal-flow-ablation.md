# Coalition Deal Flow causal ablation

**Date:** 2026-08-01

**Evidence label:** Simulation / deterministic paired causal study

**Status:** Valid complete study; mixed causal response; no rule candidate and
no canonical rule change selected.

## Registered execution

- Preregistration: `coalition-deal-flow-ablation-v1`, committed before results
  at `bff79d45`.
- Exact source: commit `bff79d457698ba9633125d689fea76e9613b6e3a`,
  `sourceDirty: false`.
- Executable game `0.8.30`; selected-rules engine `0.10.29` under
  `three-to-five-grid-ready-v1`.
- Ruleset fingerprint:
  `sha256:fc8bd0450b923b4b613ad9f5f855ea1f3832d1468b9be7496ba7f439e0d3ac4d`.
- Engine fingerprint:
  `sha256:f02f7c9c49b3244cd1a2e6bf5f5b4d07b8ea021946bb2ff91ca8971113a576fe`.
- Root seed:
  `frontier-2038-coalition-deal-flow-ablation-2026-08-01-v1`.
- The balance matrix contained 9,600 complete games: 4,800 canonical and
  4,800 matched-seed intervention games across three, four, and five players.
  The intervention paused only Coalition Lab's `deal_flow` trigger; underlying
  trades remained legal and executable.
- A separate 70-game adversarial diagnostic slice was retained and was not
  pooled into the balance aggregate.
- Batch projection used seven workers and stable run-index restoration. There
  were zero policy fallbacks, zero integrity violations, and a combined forced
  no-op rate of `0.02824%`.
- No LLM provider was enabled or called.
- Raw local report:
  `evidence/studies/simulation/2026-08-01-coalition-deal-flow-ablation-v1.raw.json`.
  SHA-256:
  `a9d7da7507b87dbc60ef81814f3868fcb80b270bb8302f917ea81ca44e60abbf`.

## Paired causal results

The table reports paused-Deal-Flow minus canonical outcomes for Coalition Lab
on 4,800 matched seed pairs. Negative win credit means Deal Flow helped the
canonical Coalition arm.

| Players | Policy backend | Coalition appearances | Win-credit delta | Mandate-score delta | Rank-advantage delta |
| --- | --- | ---: | ---: | ---: | ---: |
| 3 | Weighted | 394 | -2.157 pp | -0.145 | -0.028 |
| 3 | Greedy | 388 | 0.000 pp | 0.000 | 0.000 |
| 4 | Weighted | 528 | -2.841 pp | -0.460 | -0.097 |
| 4 | Greedy | 512 | -0.586 pp | -0.021 | -0.016 |
| 5 | Weighted | 624 | +0.721 pp | +0.143 | +0.011 |
| 5 | Greedy | 614 | +0.407 pp | -0.080 | -0.010 |
| **All** | **Combined** | **3,060** | **-0.637 pp** | **-0.089** | **-0.023** |

At three players, canonical Coalition won `27.238%` of 782 appearances and
the paused arm won `26.151%`: a raw loss of 1.087 percentage points when Deal
Flow was removed. Mean Mandate score moved from `16.597` to `16.524`, and mean
rank moved from `2.107` to `2.121`. Deal Flow therefore has detectable positive
realized value under the weighted policy, but no realized value under greedy.

Across the canonical arms, Coalition triggered Deal Flow 752 times at three
players, 1,279 times at four players, and 1,817 times at five players. The
paused arms triggered it zero times while retaining their underlying trades.
The causal contrast is mechanically live rather than a dormant intervention.

## Balance gates and interpretation

| Players | Canonical faction range | Paused faction range | Provisional gate |
| --- | ---: | ---: | ---: |
| 3 | 10.35 pp | 11.92 pp | 15 pp |
| 4 | 9.33 pp | 11.07 pp | 15 pp |
| 5 | 13.24 pp | 13.22 pp | 15 pp |

All supported-count observed faction-range gates passed in both arms. No
faction, strategy, interaction, or pairwise cell met the registered credible-
dominance standard. The study remained
`inconclusive_precision_not_reached`; maximum core confidence-sequence
half-width was `0.2761282869139463`.

The preregistered materially-valuable classification required the three-player
pause to reduce Coalition win credit by at least 3 percentage points, worsen
mean rank, and remain nonpositive in both weighted and greedy schedules. It
failed: weighted lost 2.157 points and greedy was exactly unchanged.

The preregistered inert classification required an absolute three-player win
effect no larger than 1 percentage point, an absolute mean-rank effect no
larger than `0.02`, and no schedule reversal of at least 3 points. It also
failed narrowly: the combined raw win difference was 1.087 points, with a
clear weighted/greedy asymmetry.

The registered classification is therefore **mixed**. Deal Flow is neither a
plausible explanation for the full Coalition deficit nor safely inert. The
registered next action is policy-refinement and negotiation-conversion work,
not a faction-rule candidate. In particular, this result does not authorize
the proposed Deal-Flow-to-Trust replacement or any starting-resource change.

The `0.8.30` report's paired comparison families did not expose Mandate mode,
so the registered variable-versus-fixed paired split cannot be recovered from
this batch artifact. Executable `0.8.31` corrects that reporting limitation by
adding the `factionBackendPlayerCountMandateMode` family for future studies. It
does not alter this result or make the present candidate eligible because the
backend-specific materiality gate already failed.

The 70 adversarial games remain an unpooled four-player strategy diagnostic.
Their report status is `diagnostic_not_balance_authority`; they contain no
three-player faction standings and therefore cannot reproduce, weaken, or
reverse the three-player Coalition/Safety signal.

The ordinary matrix again produced zero legal AGI declaration windows. That is
a coverage boundary, not neutral AGI evidence. The separately registered AGI
route coverage study reached a canonical legal window and declaration; see
`2026-08-01-agi-route-coverage.md`.

## Affected-surface audit

- Canonical rulebook and faction card: no change.
- Physical semantics, balance constants, and setup: no change.
- Semantic content and generated gameplay data: no change.
- Simulator: executable `0.8.30` fixed the intervention contract so
  `pausedFactionAbilities` actually suppresses Deal Flow without suppressing
  the underlying trade. That instrumentation change was committed and tested
  before registration and execution. Executable `0.8.31` adds the omitted
  Mandate-mode dimension to future paired reports. Neither delta is a canonical
  rule change.
- Browser prototype: canonical play remains unchanged.
- Reference cards and player aids: no change.
- Tests: the frozen executable passed 167 of 167 tests, `npm run check`, and
  `git diff --check` before study launch.
- Playtest protocol: observe whether Coalition converts its trading and
  promises into Mandate outcomes. Do not introduce a physical rule variant
  from this mixed result.
