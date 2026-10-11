# Seat fairness and diversity among trained policies — 2026-10-11

Component: Mandate 2038 evidence. Intent preserved. Canonical economy, default policies, qualification thresholds and release remain unchanged. This study separates seat fairness from bot quality and expected income mechanics; it does not establish human balance or optimal play.

## Outcome

The controlled seat comparison did not reproduce a material seat advantage. All
observed ranges are below the unchanged ten-percentage-point tolerance, and every
signed seat interval includes zero. However, none of the six controls demonstrates
equivalence: the four-player range bounds are [0, 19.607] points for greedy and
[0, 16.120] for weighted. Seat fairness remains unqualified. The allocation is
closed; the earlier failed mixed-policy seat report remains failed.

Capacity's performance depends on the opponent field and backend. In the greedy
held-out league it receives 14.271% winner credit, versus AGI's 35.938%; the adjusted
AGI-minus-Capacity interval is [9.536, 33.797] percentage points. In the weighted
league Capacity receives 34.271%, versus Market's 28.542%; their difference interval
is [-7.875, 19.334] points. These are policy-performance comparisons, not causal
tests of equipment, placement, recruitment or scoring. They establish neither an
unanswerable Capacity strategy nor a reason to change income rules.

Only one pair per backend clears the frozen coarse competence bound. Greedy
Balanced and Market have action-mix TV distance 0.044097 and similar Research /
deployment scoring, despite several winning-path labels. Weighted Reputation
Governor and Capability Rusher have distance 0.102951; Influence differs materially
(1.528 versus 0.293 actions per game), but their shared winning-path entropy is
0.554637, below the existing 0.60 diagnostic. Unqualified pairs are not declared
unequal merely because their intervals are broad.

Strategic diversity therefore remains unresolved. Whole-league greedy action
entropy is 0.611335 against 0.72, with Research occupying 65.234% of actions.
Weighted whole-league descriptive entropy and concentration checks are within
their existing bounds, but pooling all four policies cannot establish diversity
among comparably capable opponents. Path-label variety is not proof of distinct
plans, and this policy family cannot show that other competitive plans are absent.
No rule or policy promotion follows; practical human counterplay is still untested.

## Frozen identity and coverage

The [protocol](2026-10-11-seat-diversity-preregistration.md), [runner](2026-10-11-seat-diversity.mjs), four tests and diagnostic clarification were committed before execution as `3f543d3dbf1af4ca6539b3d622416b35ef9e7290`. Both full seat runs completed and were inspected before either diversity run. Clean launch identities, protocol/input hashes and final identities agree. The original general-trained profile artifacts remain byte-identical. Host: Linux `128`, Node 22.22.1. Executable 0.24.3 / rules 0.14.0-rc.4-test / engine 0.27.3.

- Ruleset: `sha256:1233df087b38b57cf593bab41b1eec39d064978771bdce234d4e6cd4458018df`.
- Engine: `sha256:c5081a6ad2bb5d0d63aebc3c4ba9da8d5a56333ef70a8484955b5e21e69b6f8c`.
- Root `seat-diversity-128-20261011-v1`; seat, screening, held-out league, smoke and tests use separate namespaces. Greedy and weighted are separate homogeneous backends.
- Seat control: 600 independent seed blocks/count/backend, with 3/4/5 common-seed cyclic institution rotations within each block: **14,400 game executions**, 3,600 independent blocks. Every institution subset and both objective modes are covered. Everyone uses the same frozen Capacity policy; initial Initiative, draw consumption and policy RNG remain ordinary.
- Screening: seven already-trained policies, 96 games each against the same three frozen Capacity opponents, all focal institutions/seats and both modes. **1,344 games**; no new mutation or training. Top four are frozen separately per backend before the league.
- Held-out four-player league: all 15 institution subsets, both modes, two repeats, and four policy rotations crossed with four institution rotations. **1,920 independent games**; disjoint seed per game. Every selected policy occupies every seat with every institution equally.
- Total **17,664 full games**, plus **108 separate smoke games** (48 seat and 60 screening/league). Fixed allocations; no extension, new candidate, or rules variant after inspection.

## Seat fairness under identical policies

Institutions rotate on a common game seed; policy is identical across seats. Average each seat over the rotations before inference. Correlated rotations do not inflate sample count. Existing seat tolerance stays 0.10. Intervals are simultaneous within the 38 registered comparisons, with alpha 0.025. Four players remains primary; adjacent counts stay separate.

| Backend | Players | Games / independent blocks | Seat credits, first to last | Observed range (points) | Range interval (points) | Within 10-point tolerance |
| --- | ---: | --- | --- | ---: | --- | --- |
| greedy | 3 | 1800 / 600 | 31.694%, 34.944%, 33.361% | 3.250 | [0.000, 19.449] | Unqualified |
| greedy | 4 | 2400 / 600 | 23.938%, 24.597%, 22.910%, 28.556% | 5.646 | [0.000, 19.607] | Unqualified |
| greedy | 5 | 3000 / 600 | 20.178%, 20.244%, 20.167%, 19.950%, 19.461% | 0.783 | [0.000, 13.274] | Unqualified |
| weighted | 3 | 1800 / 600 | 32.194%, 33.972%, 33.833% | 1.778 | [0.000, 17.669] | Unqualified |
| weighted | 4 | 2400 / 600 | 26.000%, 24.833%, 24.125%, 25.042% | 1.875 | [0.000, 16.120] | Unqualified |
| weighted | 5 | 3000 / 600 | 21.450%, 18.817%, 19.300%, 19.783%, 20.650% | 2.633 | [0.000, 15.188] | Unqualified |

Range bounds project the simultaneous signed pair intervals: maximum established absolute difference for the lower bound, maximum allowed absolute difference for the upper. Distinguish nonzero differences, material excess beyond 0.10, and failure to demonstrate equivalence. A wide interval is not a reproduced fairness defect, nor a passed fairness check. This policy-specific automated control does not qualify other policies or human Initiative fairness.

| Backend | Players | Seat pair (one-based) | Difference | Lower | Upper |
| --- | ---: | --- | ---: | ---: | ---: |
| greedy | 3 | 1 minus 2 | -0.032500 | -0.194490 | 0.129490 |
| greedy | 3 | 1 minus 3 | -0.016667 | -0.175126 | 0.141792 |
| greedy | 3 | 2 minus 3 | 0.015833 | -0.147007 | 0.178674 |
| greedy | 4 | 1 minus 2 | -0.006597 | -0.148183 | 0.134989 |
| greedy | 4 | 1 minus 3 | 0.010278 | -0.127650 | 0.148206 |
| greedy | 4 | 1 minus 4 | -0.046181 | -0.188335 | 0.095974 |
| greedy | 4 | 2 minus 3 | 0.016875 | -0.120429 | 0.154179 |
| greedy | 4 | 2 minus 4 | -0.039583 | -0.181777 | 0.102610 |
| greedy | 4 | 3 minus 4 | -0.056458 | -0.196072 | 0.083156 |
| greedy | 5 | 1 minus 2 | -0.000667 | -0.127441 | 0.126107 |
| greedy | 5 | 1 minus 3 | 0.000111 | -0.126188 | 0.126410 |
| greedy | 5 | 1 minus 4 | 0.002278 | -0.124035 | 0.128591 |
| greedy | 5 | 1 minus 5 | 0.007167 | -0.117571 | 0.131905 |
| greedy | 5 | 2 minus 3 | 0.000778 | -0.127429 | 0.128985 |
| greedy | 5 | 2 minus 4 | 0.002944 | -0.122445 | 0.128334 |
| greedy | 5 | 2 minus 5 | 0.007833 | -0.117072 | 0.132739 |
| greedy | 5 | 3 minus 4 | 0.002167 | -0.125273 | 0.129607 |
| greedy | 5 | 3 minus 5 | 0.007056 | -0.117545 | 0.131656 |
| greedy | 5 | 4 minus 5 | 0.004889 | -0.119786 | 0.129563 |
| weighted | 3 | 1 minus 2 | -0.017778 | -0.176691 | 0.141135 |
| weighted | 3 | 1 minus 3 | -0.016389 | -0.174305 | 0.141527 |
| weighted | 3 | 2 minus 3 | 0.001389 | -0.157729 | 0.160507 |
| weighted | 4 | 1 minus 2 | 0.011667 | -0.129308 | 0.152642 |
| weighted | 4 | 1 minus 3 | 0.018750 | -0.123701 | 0.161201 |
| weighted | 4 | 1 minus 4 | 0.009583 | -0.125505 | 0.144671 |
| weighted | 4 | 2 minus 3 | 0.007083 | -0.132189 | 0.146356 |
| weighted | 4 | 2 minus 4 | -0.002083 | -0.141471 | 0.137305 |
| weighted | 4 | 3 minus 4 | -0.009167 | -0.145640 | 0.127306 |
| weighted | 5 | 1 minus 2 | 0.026333 | -0.099211 | 0.151878 |
| weighted | 5 | 1 minus 3 | 0.021500 | -0.103804 | 0.146804 |
| weighted | 5 | 1 minus 4 | 0.016667 | -0.110425 | 0.143758 |
| weighted | 5 | 1 minus 5 | 0.008000 | -0.117644 | 0.133644 |
| weighted | 5 | 2 minus 3 | -0.004833 | -0.128346 | 0.118679 |
| weighted | 5 | 2 minus 4 | -0.009667 | -0.135000 | 0.115667 |
| weighted | 5 | 2 minus 5 | -0.018333 | -0.144611 | 0.107944 |
| weighted | 5 | 3 minus 4 | -0.004833 | -0.129664 | 0.119997 |
| weighted | 5 | 3 minus 5 | -0.013500 | -0.136700 | 0.109700 |
| weighted | 5 | 4 minus 5 | -0.008667 | -0.133777 | 0.116444 |

Signed differences are winner-credit proportions, with tied winners sharing one
credit. No registered seat comparison establishes a nonzero effect or material
excess beyond the 0.10 tolerance.

## Screening is selection, not proof of comparable skill

All seven policies had the same earlier general preparation budget, but fresh screening measures them against the same three opponents rather than different rival ecologies. Rank is frozen by winner credit, score, then ID. Screening uncertainty and limited policy-family coverage prevent an optimality claim; the held-out league provides the competence comparison. Keep low-scoring candidates in the evidence.

| Backend | Profile | Screening winner credit | Mean score | Selected |
| --- | --- | ---: | ---: | --- |
| greedy | The AGI Candidate (`agi_candidate`) | 0.427083 | 21.5625 | Yes |
| greedy | The Capacity Operator (`power_broker`) | 0.276042 | 20.0729 | Yes |
| greedy | The Balanced Operator (`balanced_operator`) | 0.208333 | 19.0625 | Yes |
| greedy | The Market Maximalist (`market_maximalist`) | 0.197917 | 19.3958 | Yes |
| greedy | The Infrastructure Compounder (`infrastructure_compounder`) | 0.062500 | 17.7396 | No |
| greedy | The Capability Rusher (`capability_rusher`) | 0.052083 | 14.4167 | No |
| greedy | The Reputation Governor (`trust_governor`) | 0.041667 | 17.1250 | No |
| weighted | The Capacity Operator (`power_broker`) | 0.250000 | 18.9479 | Yes |
| weighted | The Reputation Governor (`trust_governor`) | 0.166667 | 17.4271 | Yes |
| weighted | The Market Maximalist (`market_maximalist`) | 0.166667 | 16.6979 | Yes |
| weighted | The Capability Rusher (`capability_rusher`) | 0.156250 | 17.3333 | Yes |
| weighted | The AGI Candidate (`agi_candidate`) | 0.156250 | 16.1458 | No |
| weighted | The Infrastructure Compounder (`infrastructure_compounder`) | 0.119792 | 16.3333 | No |
| weighted | The Balanced Operator (`balanced_operator`) | 0.093750 | 13.8438 | No |

## Held-out competence and strategy diversity

All selected policies face each other in every league game, with independently rotated seats and institutions. Pairwise intervals cover all twelve comparisons at alpha 0.025. A pair is locally comparable only when its interval lies entirely within [-0.18, 0.18], the frozen coarse diagnostic resolution. That means neither has a demonstrated larger gap at this resolution within this league; it does not require equal wins or establish global/human equivalence. Persona win-share differences alone are not an economy defect.

| Backend | Profile | Winner credit | Mean score | Research / Build / Deploy / Influence per game |
| --- | --- | ---: | ---: | --- |
| greedy | `agi_candidate` | 0.359375 | 20.7302 | 8.630 / 0.160 / 2.199 / 0.000 |
| greedy | `power_broker` | 0.142708 | 18.2063 | 8.066 / 1.918 / 0.534 / 0.922 |
| greedy | `balanced_operator` | 0.266146 | 19.6875 | 7.088 / 1.182 / 2.115 / 0.068 |
| greedy | `market_maximalist` | 0.231771 | 18.9427 | 7.529 / 1.137 / 2.202 / 0.066 |
| weighted | `power_broker` | 0.342708 | 18.8635 | 5.820 / 1.075 / 1.755 / 2.134 |
| weighted | `trust_governor` | 0.205208 | 17.4229 | 6.884 / 0.720 / 0.754 / 1.528 |
| weighted | `market_maximalist` | 0.285417 | 17.4750 | 3.781 / 1.179 / 1.983 / 2.557 |
| weighted | `capability_rusher` | 0.166667 | 16.6812 | 7.342 / 1.209 / 0.831 / 0.293 |

| Backend | Profile | Capability / Customers / Reputation / AGI / objectives score | Winning paths (split winner credit) |
| --- | --- | --- | --- |
| greedy | `agi_candidate` | 11.364 / 4.767 / 1.483 / 0.588 / 2.529 | research_adoption_hybrid: 57.536%, research: 23.768%, agi_declaration: 15.797%, adoption: 2.609%, research_capital_hybrid: 0.290% |
| greedy | `power_broker` | 10.483 / 1.492 / 3.117 / 0.787 / 2.327 | agi_declaration: 49.635%, research: 19.708%, research_adoption_hybrid: 10.949%, adoption: 9.489%, legitimacy: 5.109%, adoption_legitimacy_hybrid: 3.650%, research_legitimacy_hybrid: 1.460% |
| greedy | `balanced_operator` | 10.137 / 4.631 / 1.806 / 0.596 / 2.517 | research_adoption_hybrid: 37.769%, agi_declaration: 22.114%, research: 19.765%, adoption: 18.395%, capital: 0.783%, research_capital_hybrid: 0.783%, adoption_capital_hybrid: 0.391% |
| greedy | `market_maximalist` | 10.167 / 4.242 / 1.558 / 0.562 / 2.414 | research_adoption_hybrid: 35.955%, agi_declaration: 25.169%, research: 22.022%, adoption: 16.854% |
| weighted | `power_broker` | 8.761 / 3.481 / 3.544 / 0.358 / 2.719 | research: 37.082%, research_adoption_hybrid: 22.188%, agi_declaration: 17.933%, adoption: 10.030%, research_legitimacy_hybrid: 5.471%, legitimacy: 5.167%, adoption_legitimacy_hybrid: 1.824%, research_infrastructure_hybrid: 0.304% |
| weighted | `trust_governor` | 9.860 / 1.781 / 3.298 / 0.471 / 2.013 | research: 43.655%, agi_declaration: 32.487%, research_adoption_hybrid: 9.137%, legitimacy: 4.569%, research_legitimacy_hybrid: 4.061%, adoption: 3.046%, adoption_legitimacy_hybrid: 1.015%, research_capital_hybrid: 0.508%, legitimacy_capital_hybrid: 0.508%, adoption_capital_hybrid: 0.508%, legitimacy_mobility_hybrid: 0.508% |
| weighted | `market_maximalist` | 6.949 / 3.865 / 3.579 / 0.208 / 2.874 | research_adoption_hybrid: 28.102%, adoption: 17.153%, research: 16.423%, agi_declaration: 14.234%, research_legitimacy_hybrid: 10.584%, legitimacy: 7.664%, adoption_legitimacy_hybrid: 4.380%, infrastructure_legitimacy_hybrid: 0.365%, infrastructure_adoption_hybrid: 0.365%, research_mobility_hybrid: 0.365%, legitimacy_mobility_hybrid: 0.365% |
| weighted | `capability_rusher` | 10.298 / 1.969 / 2.017 / 0.379 / 2.019 | research: 45.625%, agi_declaration: 33.125%, research_adoption_hybrid: 13.750%, adoption: 5.000%, research_infrastructure_hybrid: 0.625%, adoption_legitimacy_hybrid: 0.625%, infrastructure: 0.625%, research_legitimacy_hybrid: 0.625% |

| Backend | Policy pair | Difference | Lower | Upper | Locally comparable | Action-mix TV distance |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| greedy | `agi_candidate` minus `power_broker` | 0.216667 | 0.095361 | 0.337972 | Unqualified | 0.236632 |
| greedy | `agi_candidate` minus `balanced_operator` | 0.093229 | -0.041696 | 0.228155 | Unqualified | 0.135590 |
| greedy | `agi_candidate` minus `market_maximalist` | 0.127604 | -0.004020 | 0.259229 | Unqualified | 0.091753 |
| greedy | `power_broker` minus `balanced_operator` | -0.123438 | -0.238874 | -0.008001 | Unqualified | 0.224306 |
| greedy | `power_broker` minus `market_maximalist` | -0.089063 | -0.201791 | 0.023666 | Unqualified | 0.192969 |
| greedy | `balanced_operator` minus `market_maximalist` | 0.034375 | -0.090725 | 0.159475 | Yes | 0.044097 |
| weighted | `power_broker` minus `trust_governor` | 0.137500 | 0.009384 | 0.265616 | Unqualified | 0.182378 |
| weighted | `power_broker` minus `market_maximalist` | 0.057292 | -0.078752 | 0.193336 | Unqualified | 0.169878 |
| weighted | `power_broker` minus `capability_rusher` | 0.176042 | 0.052405 | 0.299678 | Unqualified | 0.237674 |
| weighted | `trust_governor` minus `market_maximalist` | -0.080208 | -0.204370 | 0.043953 | Unqualified | 0.283333 |
| weighted | `trust_governor` minus `capability_rusher` | 0.038542 | -0.074666 | 0.151749 | Yes | 0.102951 |
| weighted | `market_maximalist` minus `capability_rusher` | 0.118750 | -0.001138 | 0.238638 | Unqualified | 0.329948 |

Publish every maximal mutually comparable set; no favorable subset is chosen after inspection. TV distances describe observed choices, not a new passing gate. Distinct names or weights are not evidence of different viable plans.

**greedy supported local sets:** `balanced_operator`, `market_maximalist`

Set balanced_operator, market_maximalist: conditional winning-path entropy **0.719519**, top share **0.369247**. Winning paths: research_adoption_hybrid: 36.925%, agi_declaration: 23.536%, research: 20.816%, adoption: 17.678%, capital: 0.418%, research_capital_hybrid: 0.418%, adoption_capital_hybrid: 0.209%. Most frequent opening: `research → research → build` (20.625%). These summarize this group's wins/choices against the complete selected league, not an isolated subset tournament.

**weighted supported local sets:** `trust_governor`, `capability_rusher`

Set trust_governor, capability_rusher: conditional winning-path entropy **0.554637**, top share **0.445378**. Winning paths: research: 44.538%, agi_declaration: 32.773%, research_adoption_hybrid: 11.204%, adoption: 3.922%, research_legitimacy_hybrid: 2.521%, legitimacy: 2.521%, adoption_legitimacy_hybrid: 0.840%, research_infrastructure_hybrid: 0.280%, research_capital_hybrid: 0.280%, legitimacy_capital_hybrid: 0.280%, adoption_capital_hybrid: 0.280%, infrastructure: 0.280%, legitimacy_mobility_hybrid: 0.280%. Most frequent opening: `research → research → research` (16.719%). These summarize this group's wins/choices against the complete selected league, not an isolated subset tournament.

| Backend | Whole-league action entropy | Opening entropy | Opening top share | Winning-path entropy | Winning-path top share |
| --- | ---: | ---: | ---: | ---: | ---: |
| greedy | 0.611335 | 0.715805 | 0.178646 | 0.608096 | 0.406250 |
| weighted | 0.822727 | 0.796422 | 0.113281 | 0.621393 | 0.339583 |

Existing descriptive thresholds remain 0.72 action entropy, 0.65 opening entropy, 0.30 maximum opening share, 0.60 winning-path entropy and 0.55 maximum winning-path share. The existing `lane-margin-v1` classifier uses actions and holdings; AGI recognition has its own category. Interpret it alongside actual action mixes and score components: an AGI label alone does not prove a different execution plan, while a shared Research foundation need not erase different finishing strategies. This limited policy family cannot establish that other competitive strategies are impossible. Three-/five-player strategic diversity and observed human play remain unqualified.

## Prior failures and limits

The [earlier receipt](2026-10-11-reputation-counter-results.md) and raw reports remain intact: mixed-policy observed three-player seat range 0.107143, persona ranges 0.291667 / 0.205357 / 0.185520, and the prior fresh-seed faction/path failures. Their original intervals and thresholds are untouched. This controlled dataset answers a narrower seat question; it neither retroactively passes those reports nor makes bot-quality gaps game-fairness failures. No general unified audit was rerun because canonical mechanics and default policies were not changed.

Equipment and placement income remain expected behavior. The previous Reputation condition is a candidate generally useful decision rule, not a demonstrated Capacity counter. There is no evidence here authorizing an economy change to equalize authored bot results. No rule or default-policy promotion follows.

## Integrity and artifacts

All full runs completed with zero policy fallbacks, finite nonnegative holdings, reconciled scores, valid Org ownership/positions and bounded immediate trade packets. Rich/batch seat smoke controls agree. Independent Python analysis verified budgets, rotations, common/disjoint seed populations, screening selection, held-out profiles, paired unit credit and all fifty registered intervals. Validation: **240/240 tests**, `npm run check`, release verification and `git diff --check`; these establish implementation/evidence integrity, not balance.

| Backend | Three-player seat no-op | Four-player seat no-op | Five-player seat no-op | Four-player league no-op |
| --- | ---: | ---: | ---: | ---: |
| greedy | 0.000170 | 0.000182 | 0.000106 | 0.006814 |
| weighted | 0.026358 | 0.025694 | 0.025328 | 0.021137 |

Raw reports and the independent verifier source remain local under `evidence/studies/simulation/`; the verifier source is the `python` field of its JSON artifact. Protocol and runner show reproduction commands. Intervals follow the preregistered [empirical Bernstein method](https://arxiv.org/pdf/0907.3740); each matched rotation block is one observation, each held-out league game one observation. The probability model assumes independent seeded inputs and does not represent a human population.

| Artifact | SHA-256 |
| --- | --- |
| `2026-10-11-seat-diversity-greedy-diversity-raw.json` | `4742a7d1ef25964cf42c3c89348722cb9701b7dd022e6f50dfb1248a6364e976` |
| `2026-10-11-seat-diversity-greedy-diversity-selection.json` | `f879402e2d46047a879a9d0a8284adce7b5c09af139a30b85cfbcb6ea3701932` |
| `2026-10-11-seat-diversity-greedy-diversity-smoke-raw.json` | `de479c992ebd4ff885cc45fa43e8bd8594d699e78e340bfb9158ffc202e093ab` |
| `2026-10-11-seat-diversity-greedy-diversity-smoke-selection.json` | `5882baa7510ea6f151a44de2999691df2e0ed6988c7aba0980d9cb88c29939e5` |
| `2026-10-11-seat-diversity-greedy-seat-raw.json` | `893fe94b1c1c2206a0bfe40fc41ccd02e6595cd933aa522940b03f8cef1ecbb8` |
| `2026-10-11-seat-diversity-greedy-seat-smoke-raw.json` | `19e0e49574807368e7081dec00296e5595075c008ff24d96779f3d5648525318` |
| `2026-10-11-seat-diversity-verification.json` | `1ecc089afaf88963f6c3cf985ce3de99a86888d30992576df641050b1c432b56` |
| `2026-10-11-seat-diversity-verifier-source.json` | `a4be104f268990dec98048c9a93da1ca251b45fba70b9068077d3aeca7cc2573` |
| `2026-10-11-seat-diversity-weighted-diversity-raw.json` | `e14f2f9a89ee219b9607c4353aed5dcce9c33e79dc9016328c13d8292acd3add` |
| `2026-10-11-seat-diversity-weighted-diversity-selection.json` | `d34e3d74adac9578d43765893830c97254107efa5d04aa2d5f9f4a8393259356` |
| `2026-10-11-seat-diversity-weighted-diversity-smoke-raw.json` | `ec89439ef2dcecfbcdd7d5a3245e30b4ef571e0f340e1ac72bab962e5d750bbb` |
| `2026-10-11-seat-diversity-weighted-diversity-smoke-selection.json` | `042ed1af93735c23b5e6f9301dab51e93a94def180712dd04942f23890f86e2b` |
| `2026-10-11-seat-diversity-weighted-seat-raw.json` | `5f5edcc58bd411529d8049d2c4cf36e2572dff008cf237313b2f5657ddd9387f` |
| `2026-10-11-seat-diversity-weighted-seat-smoke-raw.json` | `b04af60db14067884777407304542008f719d1f002aa5c1f2a4d33a7f452883e` |

## Affected surfaces

| Surface | Delta |
| --- | --- |
| Canonical rulebook, components and machine-readable rules | No change. |
| Simulator, default personas and policy APIs | No change; study-owned orchestration only. |
| Browser prototype | No change; no new browser or human-playtest claim. |
| Reference/player aids | No change. |
| Tests | Four focused rotation, inference and ordinary-execution checks. |
| Playtest/evidence documentation | Frozen protocol, this receipt and diagnostic interpretation in the existing balance guide. |
| Release, deployment and historical evidence | No change; 0.24.3, nothing deployed, prior failures retained. |

Boundary effects: existing public policy and execution interfaces are reused. No new runtime layer, registry or rule authority.
