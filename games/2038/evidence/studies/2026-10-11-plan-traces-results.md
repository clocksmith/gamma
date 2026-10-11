# Where competitive plans converge — complete trace diagnosis, 2026-10-11

Component: Mandate 2038 evidence. Intent preserved. Economy, default policies, rules, thresholds and release remain unchanged. No human session occurred.

## Findings

The inspected winning plans commonly use Research, but they are not literally the same sequence. Across the selected winner-player executions, Research occupies 335/588 greedy turns (56.973%) and 301/576 weighted turns (52.257%). Greedy Capacity winners open with more equipment; Market and Balanced turn Capability into Customers; weighted Reputation Governor uses more Influence than Capability Rusher. These are observed differences in timing and finishers, not proof of several comparably strong, substantially different plans. The [held-out competence comparisons](2026-10-11-seat-diversity-results.md) remain the applicable performance evidence.

The two coarse competence pairs remain limited. Greedy Balanced and Market both spend most winning turns on Research and deployment, with similar four-Era patterns. Weighted Reputation Governor and Capability Rusher share sustained Research while differing in Influence; their prior shared path-entropy diagnostic remains below its bound. The traces neither establish broad strategic variety nor prove that other competitive plans are impossible.

An early recruitment plan remains unqualified in this policy family. Greedy winners recruit **0 times across 388 legal turn opportunities**; weighted winners recruit **2 times across 294**. Both winning weighted recruitments occur late (Eras III and IV), not as an early production plan. Across every player in the selected games, counts are 0/1,196 greedy and 9/1,123 weighted, including incidental early recruitment by non-winners. These denominators count repeated opportunities, not independent trials or players. Low use does not show that recruitment is mechanically weak.

Capped Research deserves interpretation rather than a blanket wasted-turn label. Winners resolve Research at Capability 12 on 44 greedy and 12 weighted turns. It raises Reputation on 10 and 4 of those turns respectively, lowers it on 5 and 0, and leaves it unchanged on 29 and 8. In 11 greedy winning turns it also leaves the acting Org in place and Reputation unchanged while spending Compute; no analogous weighted winning turn meets all these conditions. Shared Training-deck consumption can still affect later play. No intention or final-score benefit is inferred from these traces.

Blocked Actions are present even in wins: 4/588 greedy and 12/576 weighted winning turns. The ordinary policy selected an Action without a legal resolution, preserving the Org position. This is an observed no-op, not evidence that a person felt frustrated. Only participants can report compulsory, confusing or frustrating choices.

## Selection, identity and completeness

The [protocol](2026-10-11-plan-traces-protocol.md) fixes success-conditioned selection and the [capture runner](2026-10-11-plan-traces.mjs) records original decisions without changing them. For each of four selected profiles, all six institutions and both objective modes, select the archived winning seed with smallest SHA-256. Each backend has 48 distinct games covering all 48 requested cells, with no missing cells. **96 existing games were replayed**, not added as independent tournament observations.

The sample contains 384 player executions: 97 winner-player executions (49 greedy, including one tied game; 48 weighted) and 287 others. All players in each selected game are retained. This purposive sample cannot estimate population win rates, justify a new confidence interval or represent human play. Apparent winner/other differences below are descriptive.

Capture launched on clean commit `8ef2c9e9d48e1d14d618afa63154db96dc196f35`, executable 0.24.3 / rules 0.14.0-rc.4-test / engine 0.27.3, Linux `128`, Node 22.22.1. Both capture identities match the original league game, engine, inputs and selected profiles; source revisions differ only by study work. Every complete archived summary matches exactly: winner credits, score parts, holdings, Actions, openings, winning paths, AGI, trades, no-ops and fallbacks.

The initial `058bb7945` launch stopped at release preflight before playing any game: the new playtest-guide text changed a sealed release source. Commit `8ef2c9e9d` restored that guide byte-for-byte and moved the study-specific human procedure into the dated protocol. Neither immutable manifest nor release bundle was rewritten. Both zero-game failures are retained in the local launch-failures artifact. Release verification subsequently passed.

| Backend | Complete traces | Action selections | All decisions | Public replay events |
| --- | ---: | ---: | ---: | ---: |
| greedy | 48 | 2304 | 11101 | 14009 |
| weighted | 48 | 2304 | 11576 | 14185 |

Every game includes four Productions and four Reputation Reviews, all resolutions and Research runs, all original decision observations/legal alternatives/weights, the initial state and completed final state. Policy weights are heuristic preferences, not calibrated values of alternatives.

## Winning plans by policy

| Backend | Policy | Winning player executions | Research turns / all turns | Actual Capability gained / Research runs | Mean longest Research run | Repeated adjacent Action pairs / eligible pairs | Recruitment uses / eligible turns | Blocked turns |
| --- | --- | ---: | --- | --- | ---: | --- | --- | ---: |
| greedy | `power_broker` | 12 | 78 / 144 | 101 / 78 | 4.417 | 63 / 132 | 0 / 91 | 0 |
| greedy | `market_maximalist` | 12 | 93 / 144 | 118 / 93 | 5.083 | 64 / 132 | 0 / 86 | 4 |
| greedy | `agi_candidate` | 13 | 89 / 156 | 131 / 89 | 3.231 | 51 / 143 | 0 / 86 | 0 |
| greedy | `balanced_operator` | 12 | 75 / 144 | 117 / 75 | 3.250 | 52 / 132 | 0 / 125 | 0 |
| weighted | `trust_governor` | 12 | 83 / 144 | 122 / 78 | 4.083 | 59 / 132 | 0 / 69 | 5 |
| weighted | `market_maximalist` | 12 | 61 / 144 | 98 / 59 | 2.250 | 38 / 132 | 0 / 59 | 3 |
| weighted | `capability_rusher` | 12 | 86 / 144 | 111 / 86 | 4.000 | 58 / 132 | 2 / 85 | 0 |
| weighted | `power_broker` | 12 | 71 / 144 | 92 / 70 | 2.917 | 36 / 132 | 0 / 81 | 4 |

Research-run lengths and adjacent repetitions follow each player across all twelve turns, including Era boundaries. Selected Research turns include blocked commitments; resolved Research runs and capped-Research counts exclude them. Capability gain uses actual before/after holdings, not uncapped provisional Training metrics. A zero gain can reflect a crash, a cap or an immediately banked Human Evaluation. Repetition alone does not identify a poor or frustrating choice.

| Backend | Policy | Research in Era I | Era II | Era III | Era IV | Turns per Era |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| greedy | `power_broker` | 13 | 25 | 19 | 21 | 36 |
| greedy | `market_maximalist` | 21 | 21 | 25 | 26 | 36 |
| greedy | `agi_candidate` | 22 | 21 | 19 | 27 | 39 |
| greedy | `balanced_operator` | 20 | 16 | 20 | 19 | 36 |
| weighted | `trust_governor` | 21 | 22 | 20 | 20 | 36 |
| weighted | `market_maximalist` | 20 | 15 | 11 | 15 | 36 |
| weighted | `capability_rusher` | 22 | 22 | 21 | 21 | 36 |
| weighted | `power_broker` | 18 | 22 | 18 | 13 | 36 |

## Preserve the less successful executions

| Backend | Group | Player executions | Research turns | Capped Research | Zero actual Capability gain | Research crashes | Recruitment uses / eligible turns | Blocked / all turns |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |
| greedy | winners | 49 | 335 | 44 | 79 | 17 | 0 / 388 | 4 / 588 |
| greedy | others | 143 | 1163 | 226 | 381 | 99 | 0 / 808 | 18 / 1716 |
| weighted | winners | 48 | 301 | 12 | 50 | 21 | 2 / 294 | 12 / 576 |
| weighted | others | 144 | 894 | 95 | 222 | 73 | 7 / 829 | 37 / 1728 |

These groups share success-conditioned game selection and are not independent cohorts. Their differences cannot establish why a player lost. In particular, crashes and weak production can precede low scores, but correlated counts do not identify the causal correction.

## Concrete decisions and consequential tradeoffs

**Deferred investment versus Research.** Greedy Capacity, original league index 65, Mirevanta Works, Era I/cycle 1: before Runway 4 / Compute 2 / Capability 0 / Reputation 3 / Customers 0. Legal recruitment costs two Runway and establishes a third Org. The chosen Research spends one Compute and gains two Capability; final score is 22, with 8 Capability / 6 Customer / 5 Reputation / 0 AGI / 3 objective points. Research selection weight is 17.697, Organize 1.963. Recruitment was legal, not unaffordable or locked behind another prerequisite.

An extra Org can preserve another production position and add future yield/control, but still grants no extra turns. It begins on Organize, whose normal yield is one Runway; leaving it there through all four Productions would supply four nominal Runway, subject to holding caps and subsequent choices. The acting Org also moves to Organize. This investment consumes an Action and two Runway and delays Research; it may alter Compute production or future Customer eligibility. That is a concrete tradeoff, not a proven superior final plan.

**Late recruitment can coexist with a win.** Weighted Capability Rusher recruits in original index 697, Mirevanta Works, Era III/cycle 1, spending Runway 7 → 5 with Compute 0, Capability 6, Reputation 0 and Customers 2. It finishes with three Orgs and score 24. In index 121, Orisonix, it recruits in Era IV/cycle 1 and finishes with three Orgs and score 18. These are retained successful examples, not evidence of an early recruitment engine or the marginal value of the extra Org. The seven other recruitment resolutions in the selected weighted games belong to non-winners and remain retained.

**Capped Research versus a legal Customer.** Weighted Reputation Governor, index 627, Dovetalis Labs, Era IV/cycle 3: Runway 12 / Compute 2 / Capability 12 / Reputation 1 / Customers 1. Research spends one Compute, with Capability and Reputation unchanged; the Org changes position. Deploy was legal at the same Compute cost and would grant Customer 2 while losing one Reputation. That Customer has a two-Mandate contribution, while losing one Reputation removes one contribution point before final objectives, Production, Review, other players and tie-breaks. The trace establishes an available tradeoff, not that this branch would improve the final score or win. Original final score is 18. Research weight is 10.070 versus Deploy 4.847.

The contrary example is also retained: weighted Reputation Governor, index 640, Era IV/cycle 1, capped Research banks Human Evaluation and raises Reputation 3 → 4 while a Customer is legal. Thus capped Research cannot be categorically dismissed. Greedy winners had no legal Deploy alternative on their 44 capped Research turns; weighted winners had one on four of twelve. Generic advice to deploy at the cap therefore does not address the bulk of the greedy convergence.

Every example is inspectable through its original league index, complete seed in the local analysis artifact, full decision packet alternatives and replay. No branch outcome was simulated in this diagnosis.

## One focused follow-up

The clearest missing plan is **early recruitment for production**. If proceeding with another automated experiment, compare one study-local early-recruit variant of the greedy Balanced policy against its unchanged parent: on its first turn only, when Organize/recruit is legal and affordable, select Organize and the recruit resolution; otherwise use the parent. All subsequent decisions remain parent decisions. Balanced is already in the coarse competence pair with Market; no new training or weaker comparison opponent is needed.

Before execution, freeze unseen matched seeds, opponent field, rotated institutions/seats, primary competitiveness criterion and stopping allocation. Measure realized production, cap losses, delayed Capability/Customers, objective/control changes and whether the plan remains competitive while making different consequential choices. Retain three-/five-player controls before any promotion. This diagnosis does not execute or promote that intervention. Failure would reject that bounded plan, not recruitment in general; success would still require human observation.

For people, use the ordinary-rules, no-coaching procedure in the dated protocol. Record their intended plans and meaningful, compulsory or frustrating decisions in their words. Automated legal alternatives cannot establish human discoverability or enjoyment.

## Validation, artifacts and affected surfaces

Validation: **242/242 tests**, including passive-capture parity for both backends; package content checks; exact release verification after restoring the guide; archived-outcome parity for all 96 games; independent Python reconciliation of action counts, all 48 cells/backend, settlements, input/source hashes and winner/other totals; `git diff --check`. This establishes capture integrity, not balance.

Raw complete traces and analysis are local under `evidence/studies/simulation/`. Analysis source is retained in the JSON artifact below; its `python` field is independently rerunnable. Original league artifacts and thresholds remain unchanged.

| Artifact | SHA-256 |
| --- | --- |
| `2026-10-11-plan-traces-analysis-source.json` | `9d106c4a6b4afc69bab94ce52c8c373236c07899b5d13e97c30362a4f4d1ca49` |
| `2026-10-11-plan-traces-analysis.json` | `e258a0fae7a090aabdaa1a2618d8a81a136e4b344d280526649354e93e5ab3e0` |
| `2026-10-11-plan-traces-greedy-raw.json` | `4a40d3043ce1a446a4c253ba9f0a95cc11bb7961e384b42411f7f9cc4e3f5dab` |
| `2026-10-11-plan-traces-launch-failures.json` | `a5b5be91c21c0506be8cce3545fa328053086a3d4a0c495e7ade63ec66cef92f` |
| `2026-10-11-plan-traces-weighted-raw.json` | `2c193cc44c9ddb2cbd797fb32f8f655b6d95eaa30a2ab0d0a928e856d8357171` |

| Surface | Delta |
| --- | --- |
| Canonical rulebook/components/runtime data | No change. |
| Engine/default policies/policy APIs | No change; capture delegates original decisions. |
| Browser prototype | No change; no browser or human claim. |
| Reference/player aids | No change. |
| Tests | Two capture-selection/parity checks. |
| Evidence | Dated protocol, capture runner, this diagnosis and local full traces. |
| Shared playtest guide | Restored to original sealed-release bytes; ordinary-rules observation procedure lives in this study protocol. |
| Release/deployment/historical evidence | No change; exact 0.24.3 verifies, nothing deployed, failures retained. |

Boundary effects: study-owned observation only; existing execution/policy interfaces and evidence-label authority retained.
