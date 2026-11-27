# Early recruitment production plan — results, 2026-10-11

Component: Mandate 2038 study-owned policy comparison. Intent preserved. Economy,
default policies, engine, original balance thresholds, release and deployment
remain unchanged. These are automated simulations, not human playtests.

## Conclusion and decision

The deliberate recruitment plan improves four-player final Mandate against the
unchanged parent by **2.611** (simultaneous interval **[0.532, 4.691]**) and split
winner credit by **18.906 percentage points [7.928, 29.884]**. It exceeds the
frozen one-Mandate primary target with positive score evidence. This is evidence
of a useful recruitment opportunity overlooked by this bot family, rather than
evidence that recruitment is mechanically weak. Keep the economy unchanged.

Full plan acceptance remains **inconclusive**. Against the placement-only control,
four-player score gain is 1.429 with interval [-0.632, 3.490]; the gain beyond
generic positioning is not qualified for the primary score metric. Four-player
winner-credit gain against that control is positive, 12.500 pp [1.075, 23.925].
The five-player winner-credit interval against placement, [-12.459, 35.792] pp,
does not clear the frozen -10 pp noninferiority bound. This is unresolved precision,
not an observed five-player regression: the point difference is +11.667 pp.
Three-/five-player score intervals remain broad. Neither the plan-failure criterion
nor all acceptance criteria pass. Do not change thresholds or extend this allocation.

The bounded comparison is finished. Retain the study candidate without promoting
a default policy or rules change. Ordinary-rules human observation is the next
useful evidence when participants are available; do not coach this opening.
Human discovery, counterplay, negotiation and enjoyment remain unobserved. Prior
failed seat/diversity/balance reports are unchanged, not canceled by this result.

## Frozen design and execution

The [preregistration](2026-10-11-early-recruitment-preregistration.md) and
[runner](2026-10-11-early-recruitment.mjs) define one candidate and two controls.
The parent is the frozen general-trained Balanced profile using greedy decisions.
Placement changes its legal resolution positions, preserving its chosen Action
and mode. Recruitment spends the first Action on a third Org and the second on
productive setup, then uses the same placement rule. Research stopping, trade
and other stages remain parent decisions. No hidden state or outcome search.

Four-player opposition is frozen AGI, Capacity and Market; three-player opposition
is AGI and Market; five adds an unchanged Balanced duplicate. All institution
subsets and both objective modes are crossed with focal seats and institution
rotations. The same scenario seed, institution order, seats and profile bytes
apply to all three arms. Seeds include rotations and are distinct across scenarios.
Normal altered draw consumption and rival responses are retained. No tuning or
adapted opponents; these findings are conditional on this field and greedy backend.

| Players | Independent matched scenarios | Held-out games | Smoke observed + parity replay games |
| --- | ---: | ---: | ---: |
| 3 | 360 | 1080 | 27 + 27 |
| 4 | 960 | 2880 | 48 + 48 |
| 5 | 300 | 900 | 75 + 75 |

**4,860 held-out games**, plus 150 smoke games and 150 rich/unobserved parity
replays. No extra seeds, extensions, incomplete games, fallbacks or launch failures.
Raw files bind clean source `37ae8d050a8df5e72d331bcb8814eec5052b5910`, Linux `128`,
Node 22.22.1, executable 0.24.3, rules 0.14.0-rc.4-test, engine 0.27.3, input and
profile hashes. Exact release verification passed before every launch.

## Outcomes and all frozen intervals

Intervals use the preregistered two-sided fixed-look empirical-Bernstein bounds,
Bonferroni over 12 contrasts, family alpha 0.05; score differences bounded by
[-40, 40], winner-credit differences by [-1, 1]. The statistical unit is one
independently seeded matched scenario. These model-based intervals do not describe
human populations. No inference method or acceptance threshold changed.

| Players | Arm | Mean final Mandate | Mean split winner credit |
| --- | --- | ---: | ---: |
| 3 | parent | 19.903 | 34.722% |
| 3 | placement | 21.011 | 40.000% |
| 3 | recruit | 22.589 | 56.667% |
| 4 | parent | 19.456 | 25.156% |
| 4 | placement | 20.639 | 31.562% |
| 4 | recruit | 22.068 | 44.062% |
| 5 | parent | 19.577 | 23.500% |
| 5 | placement | 20.460 | 26.667% |
| 5 | recruit | 21.953 | 38.333% |

| Players | Recruitment minus control | Mandate gain [interval] | Winner-credit gain pp [interval] |
| --- | --- | --- | --- |
| 3 | parent | 2.686 [-2.125, 7.497] | 21.944 [0.239, 43.649] |
| 3 | placement | 1.578 [-3.129, 6.284] | 16.667 [-4.990, 38.323] |
| 4 | parent | 2.611 [0.532, 4.691] | 18.906 [7.928, 29.884] |
| 4 | placement | 1.429 [-0.632, 3.490] | 12.500 [1.075, 23.925] |
| 5 | parent | 2.377 [-3.209, 7.963] | 14.833 [-9.017, 38.684] |
| 5 | placement | 1.493 [-4.065, 7.052] | 11.667 [-12.459, 35.792] |

## Does the extra Org actually do useful work?

Every candidate recruits on turn one and completes setup on turn two: 1,620/1,620
of each. In four-player games, 695 setups move/equip the third Org directly and
265 use legal Organize reassignment. The added Org is also the acting piece on
2.188 subsequent productive resolutions per game on average. Its engine-order
attributed production supplies **9.890 actual Compute** and 0.108 actual Runway,
versus nominal 11.361 Compute / 0.115 Runway. Caps absorb 1.472 Compute and 0.006
Runway from that Org on average. Actual yield, not nominal yield, is counted.

Recruitment costs exactly two Runway and one Action. Setup costs another Action;
average equipment spending on the third Org is 1.431 Runway (legal discounts and
reassignments included). Total equipment spending is 1.961 candidate versus
2.101 parent, so the whole-plan increase in recruitment plus equipment spending
is **1.858 Runway** rather than simply adding the entire third-Org equipment bill
to the parent. Ordinary trade, other costs, delayed Actions and score consequences
are retained in the paired complete game outcomes. Resources have no automatic
Mandate conversion, and the heuristic resource prices are not a legal exchange rate.

| Four-player diagnostic per game | Parent | Placement | Recruitment |
| --- | ---: | ---: | ---: |
| Total actual Compute production | 9.207 | 11.751 | 13.785 |
| Total actual Runway production | 7.338 | 7.600 | 11.135 |
| Compute lost to production caps | 0.269 | 0.129 | 1.474 |
| Research turns | 7.055 | 8.430 | 5.327 |
| Deploy turns | 2.079 | 2.013 | 3.798 |
| Fund turns | 1.602 | 0.332 | 0.534 |
| Era-I Research turns | 1.811 | 1.915 | 0.470 |
| Final controlled hexes | 1.045 | 1.041 | 1.723 |
| Final unspent Compute | 3.853 | 4.869 | 8.356 |
| AGI recognition rate (%) | 13.438 | 18.125 | 0.417 |

Total actual Compute production rises by 4.578 versus parent and 2.034 versus
placement. This is less than the third Org's attributed 9.890 because other Org
positions and production also change. Total Runway production rises by 3.798
versus parent, including changed Customer income. Do not attribute every income
change solely to the added piece. Candidate finishes with 8.356 unspent Compute
versus parent 3.853: some capacity is unused. Income alone does not prove payoff.

The Action pattern is consequential: Research falls from 58.793% of parent turns
to 44.392% of candidate turns; Deploy rises from 2.079 to 3.798 per game. Placement
by itself instead increases Research to 8.430 turns. The candidate sacrifices
early Capability/Customers, catches up in Customers during Era III, and finishes
with lower Capability/Reputation and much less AGI recognition. This is not a
cosmetic policy rename or a no-cost extra piece.

| Four-player final score component | Parent | Placement | Recruitment | Gain versus parent |
| --- | ---: | ---: | ---: | ---: |
| capability | 10.040 | 11.196 | 9.486 | -0.553 |
| customers | 4.548 | 4.415 | 7.931 | +3.383 |
| reputation | 1.800 | 1.788 | 0.698 | -1.102 |
| agi | 0.537 | 0.725 | 0.017 | -0.521 |
| objectives | 2.531 | 2.516 | 3.935 | +1.404 |

Customer points (+3.383) and objective points (+1.404) outweigh lower Capability
(-0.553), Reputation (-1.102) and AGI (-0.521) on average. Of the objective gain,
0.666 comes from Org-count criteria and 0.468 from Customer criteria; the remainder
includes production capacity, control, proximity and other final-state criteria.
This is not all a recruitment bonus: objective standings also depend on the other
players and changed whole-game behavior. The full paired score, including the
displaced Actions, provides positive repayment evidence against the parent. The
primary score margin beyond generic placement remains unresolved.

## Keep favorable and unfavorable complete games

At four players, recruitment finishes with a higher/equal/lower score than parent
in **599 / 42 / 319** scenarios; versus placement, **518 / 47 / 395**. It does not
win or improve every game. The local analysis retains both extreme paired-score
examples (descriptive, selected after execution), with full seeds and decisions:

- Positive: `holdout:4:0:fixed:1:2:2`, focal Kestralyn. Parent 10 / placement 14 /
  recruitment 29. Parent spends eight Actions on Fund after a poor production
  opening; placement stays on Research for all twelve turns. Recruitment equips
  the added Org at its legal one-Runway cost, then obtains five Customers and
  seven objective points. A favorable illustration, not a population estimate.
- Negative: `holdout:4:14:variable:1:1:3`, focal Mirevanta Works. Parent 31 /
  placement 24 / recruitment 16. Parent reaches four Customers, high Reputation
  and AGI; candidate finishes with three Customers, Capability 7, Reputation 0
  and unused Compute 10. Productive recruitment still does not repay its delay
  in this game. Original inputs and every unfavorable outcome remain intact.

Prefix both suffixes with `early-recruitment-128-20261011-v1:`. Exact examples,
full per-Era holdings, actual/capped yields, resolutions, final objectives and
other players are in the raw files and analysis. No branch was re-simulated.

## Integrity, validation and artifacts

**247/247 tests** passed, including untouched-parent full-outcome parity, legal
extra-Org setup, independent scenario coverage and actual cap-loss attribution.
Content/project checks and exact release verification passed. Smoke verified
all three arms at all supported counts against rich/unobserved execution,
including complete outcomes and final state. Every held-out game completes with
valid Org ownership/positions, bounded trades, nonnegative finite holdings,
reconciled score and zero policy fallback. Focal no-op rates remain below 0.03
at all counts/arms; all-player rates range 0.00411–0.00810. This is implementation
and capture integrity, not a global balance qualification.

Independent Python analysis recomputes every one of the 12 estimates, variances,
radii and interval endpoints; reconciles all Production per-source actual gains
with holding deltas; verifies counts, unique scenario seeds, equal institution/seat
exposure, release/source/protocol/input hashes, score components, winner credit
and all four Era settlements. Its exact source is retained below.

Raw JSON and analysis remain in the existing local simulation archive. Hashes:

| Artifact in `evidence/studies/simulation/` | SHA-256 |
| --- | --- |
| `2026-10-11-early-recruitment-3-raw.json` | `7372b319aff60a174df28972cfe5e2bcf0a8cee8c76b051e886e8c11518a2f76` |
| `2026-10-11-early-recruitment-3-smoke-raw.json` | `b8d8847b4aa340a3cda5122724c970b7ff9a7a9d7b7b874e229cb1a0588224a3` |
| `2026-10-11-early-recruitment-4-raw.json` | `2b1170b94ac24cbde6643b23466af67d4260aa0bec25e58bf1a471cd2e9b34d5` |
| `2026-10-11-early-recruitment-4-smoke-raw.json` | `2f6356d434838edb94006c1910dae0c03f7db6e6533226773af3cc5316a27d2c` |
| `2026-10-11-early-recruitment-5-raw.json` | `effc6ef2c03894308d14a7d609f1024756b5038768af51e7677f7913fa4bcc20` |
| `2026-10-11-early-recruitment-5-smoke-raw.json` | `488a5e1d0d61b875d871ec6cec668fa8174a6d222f32ec8340ee5ac7bd2cb6f6` |
| `2026-10-11-early-recruitment-analysis-source.json` | `9169beba3718ac26ffdff1ae61ef5ac8b575db0c3ba73bc8afbcf6e897a05f3e` |
| `2026-10-11-early-recruitment-analysis.json` | `c00275da2cba4b469dce8eeece88b83c67e66521e1ad8da8757d8834fb1fec8f` |

| Surface | Delta |
| --- | --- |
| Canonical rulebook, components and runtime data | No change. |
| Engine, default policies and policy API | No change; candidate and observer are study-owned. |
| Browser prototype and player aids | No change; no browser or human claim. |
| Tests | Five focused plan/capture/inference checks. |
| Evidence | Frozen protocol, runner, raw comparisons, independent analysis and this receipt. |
| Playtest/balance documentation | Balance guide links this result; shared playtest guide unchanged. |
| Release, deployment and historical results | No change; no promotion or deployment. |

Boundary effects: existing public decisions and runtime rules are preserved.
Only study-owned policy selection and evidence interpretation changed.
