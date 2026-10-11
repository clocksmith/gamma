# Reputation counter results — 2026-10-11

Component: Mandate 2038 policy evidence. Intent preserved. **Useful mechanism evidence; balance and human counterplay remain unqualified.** No economy, default-persona, rules, version, publication or deployment change.

## Frozen execution

The [retained diagnosis and preregistration](2026-10-11-reputation-counter-preregistration.md) identified the failing bounds and a Reputation-conversion hypothesis before new games. The [runner](2026-10-11-reputation-counter.mjs) and four contract tests were committed and pushed as `343b96e54b53c570fca0a30de85c33ce9c430c89`. Both runs bind that clean launch revision; start/end identities and protocol hashes agree. Frozen selections are byte-identical to the prior campaign. Host Linux `128`, Node 22.22.1; executable 0.24.3, rules 0.14.0-rc.4-test, engine 0.27.3.

- Ruleset: `sha256:1233df087b38b57cf593bab41b1eec39d064978771bdce234d4e6cd4458018df`.
- Engine: `sha256:c5081a6ad2bb5d0d63aebc3c4ba9da8d5a56333ef70a8484955b5e21e69b6f8c`.
- Root `reputation-counter-128-20261011-v1`; confirmation, smoke, tests and the earlier campaign use separate seeds.
- Each backend: 144 three-player, 768 four-player and 240 five-player paired blocks. Two arms per block; **4,608 full games total**, plus 24 separate smoke games. No search or added allocation after inspection.
- Both arms use the same trained Capacity, rival profiles, roster IDs, seats, institution assignments, seed and objective mode. All six focal institutions, all focal seats, fixed/variable objectives, rotating responder seats and rival identities. Homogeneous greedy and weighted are separate controls.
- Only the responder gains: **at 0/1 Reputation, take reachable Influence; otherwise use its unchanged trained parent**. Its ordinary resolution, Org choice, trading, Research and all other decisions remain unchanged.

## Failing general balance checks remain open

The canonical game was not changed or requalified. The most recent retained unified audit still fails these observed bounds. Its existing simultaneous confidence sequences yield the range intervals below; none establishes equivalence or dominance. This focused two-arm experiment does not replace the general matrix.

| Check | Observed | Limit | Excess | Conservative range interval |
| --- | ---: | ---: | ---: | --- |
| Three-player seat range | 0.107143 | 0.10 | 0.007143 | [0, 0.827905] |
| Three-player persona range | 0.291667 | 0.18 | 0.111667 | [0, 1] |
| Four-player persona range | 0.205357 | 0.18 | 0.025357 | [0, 0.676487] |
| Five-player persona range | 0.185520 | 0.18 | 0.005520 | [0, 0.514197] |

The [preregistration](2026-10-11-reputation-counter-preregistration.md) also retains both earlier audit blocks: repeated four-/five-player persona-range failures and isolated faction/path-entropy failures. Registered general precision was not reached; entropy evaluations have no retained interval. No implementation-test count clears these failures.

## Matched outcomes

Winner ties split one credit. These are point estimates, not qualified changes. The older 40.2%/29.2% rates belong to different seed populations; compare the arms within this table.

| Backend | Players | Blocks | Capacity control → candidate | Responder control → candidate | Responder score control → candidate |
| --- | ---: | ---: | --- | --- | --- |
| greedy | 3 | 144 | 45.139% → 37.500% | 35.417% → 47.222% | 19.5417 → 21.5694 |
| greedy | 4 | 768 | 30.208% → 28.646% | 29.102% → 35.286% | 19.4062 → 20.9635 |
| greedy | 5 | 240 | 22.083% → 17.500% | 25.417% → 34.583% | 19.1375 → 20.6583 |
| weighted | 3 | 144 | 47.917% → 45.486% | 31.250% → 32.986% | 16.8403 → 17.1736 |
| weighted | 4 | 768 | 39.323% → 37.500% | 26.693% → 31.510% | 17.2734 → 17.7995 |
| weighted | 5 | 240 | 25.000% → 22.500% | 27.500% → 30.000% | 17.6167 → 18.1500 |

All twelve registered effects follow. Fixed-look Hoeffding intervals, Bonferroni family alpha 0.05 / 12; winner-credit differences in proportions. The method and small-gain precision limitation were frozen before execution. Every interval includes zero. Four-player own-gain **and** Capacity-suppression lower bounds must exceed 0.04 in both backends; neither backend qualifies. Three-/five-player own-gain lower bounds must exceed -0.05; those noninferiority safeguards remain unqualified despite positive point estimates. Do not treat broad intervals as demonstrated harm or as a passed guard.

| Backend | Players | Effect | Mean | Lower | Upper |
| --- | ---: | --- | ---: | ---: | ---: |
| greedy | 3 | responderGain | 0.118056 | -0.174770 | 0.410881 |
| greedy | 3 | capacitySuppression | 0.076389 | -0.216437 | 0.369215 |
| greedy | 4 | responderGain | 0.061849 | -0.064948 | 0.188646 |
| greedy | 4 | capacitySuppression | 0.015625 | -0.111172 | 0.142422 |
| greedy | 5 | responderGain | 0.091667 | -0.135155 | 0.318489 |
| greedy | 5 | capacitySuppression | 0.045833 | -0.180989 | 0.272655 |
| weighted | 3 | responderGain | 0.017361 | -0.275465 | 0.310187 |
| weighted | 3 | capacitySuppression | 0.024306 | -0.268520 | 0.317131 |
| weighted | 4 | responderGain | 0.048177 | -0.078620 | 0.174974 |
| weighted | 4 | capacitySuppression | 0.018229 | -0.108568 | 0.145027 |
| weighted | 5 | responderGain | 0.025000 | -0.201822 | 0.251822 |
| weighted | 5 | capacitySuppression | 0.025000 | -0.201822 | 0.251822 |

## What produced the observed difference

The earlier multivariable responder search could not isolate a cause. This new intervention isolates one action-selection condition; downstream changes to placement, production and later decisions are part of its effect. The quantities below are exact retained accounting, with descriptive averages. They do not individually estimate separate causal contributions or establish a statistically qualified model of every strategy.

| Four-player responder quantity | Greedy control → candidate | Weighted control → candidate |
| --- | --- | --- |
| Capability points | 9.9076 → 9.7734 | 7.0221 → 6.7708 |
| Customer points | 4.7214 → 4.4115 | 3.9740 → 3.8490 |
| Reputation points | 1.5091 → 3.0938 | 3.2682 → 3.9831 |
| AGI points | 0.5469 → 0.8229 | 0.2031 → 0.3333 |
| Final objective points | 2.7214 → 2.8620 | 2.8060 → 2.8633 |
| Equipped Orgs | 1.1289 → 1.0573 | 1.2057 → 1.0990 |
| Total Orgs | 2.0013 → 2.0013 | 2.0560 → 2.0456 |
| Low-Reputation reviews | 1.9831 → 0.6081 | 0.8516 → 0.3255 |
| Actual direct Influence Reputation | 0.1042 → 1.9896 | 2.9492 → 3.9362 |
| Actual production Reputation | 0.0326 → 1.0872 | 0.8620 → 1.1484 |
| Actual production Compute | 9.3919 → 8.5690 | 6.3516 → 5.8737 |
| Nominal equipment Compute bonus | 3.3607 → 2.8568 | 2.3685 → 2.0234 |
| Actual review Runway loss | 3.9245 → 1.2031 | 1.6888 → 0.6445 |
| Recruit resolutions | 0.0013 → 0.0013 | 0.0560 → 0.0456 |

**Greedy: equipment and placement support Compute, but neglected Reputation is a recoverable conversion gap.** Capacity control receives 13.3086 actual production Compute per game versus the responder’s 9.3919. Its nominal equipment Compute bonus is 5.7409 versus 3.3607; base Compute yield is 7.7669 versus 6.2799. Equipment income is real enabling machinery, although these role differences are observational and do not isolate the investment’s value.

Under the single condition, the responder gains 1.5573 score: Reputation adds 1.5846 and AGI 0.2760, offset by lower Capability/customer points. It takes approximately one Influence action rather than 0.0534, and retains an Org on Influence for 1.0026 summed Org/Era observations per game instead of 0.0182. Actual Reputation production rises 0.0326 → 1.0872. This is the ordinary placement consequence of taking Influence, not a separately changed placement heuristic. It improves while equipping fewer Orgs and producing less Compute. Capacity’s score barely changes, 19.9154 → 19.8424. The tested responder gain does not require matching Capacity’s Compute income; the experiment does not separately estimate the cause of Capacity’s original advantage.

**Weighted: the remaining scoring advantage is mainly Capability.** Control Capacity has 8.9714 Capability points versus the responder’s 7.0221, while their Reputation is already similar (3.3724/3.2682). Capacity selects 5.9440 Research actions versus 3.9258, despite equipping fewer Orgs (0.9688/1.2057). Its nominal equipment Compute bonus is also slightly lower (2.3216/2.3685). The simple condition adds responder Reputation but lowers Capability; its net score gain is 0.5260, with Capacity still ahead in mean score. Do not extrapolate the greedy mechanism into an equipment-dominance claim across both backends.

**Recruitment is not the main engine in these tested lineups.** Direct traces distinguish recruiting from reassignment. Greedy control Capacity recruits 0.0078 Orgs/game; the responder recruits 0.0013. Weighted control rates are 0.0221 and 0.0560. This closes the prior telemetry gap for these lineups, without proving recruitment irrelevant under other policies.

Actual production applies resource caps and includes Customer income and applicable faction income; nominal equipment yield is not credited as actual income. The independent verifier reconstructs those caps and income terms for every Era. Influence gains and Deployment losses are recorded as actual capped changes, not just printed amounts.

## Human practicality and disposition

The added instruction requires one visible holding and a reachable Action; it needs no hidden-card forecast, institution-specific calculation, or policy search. At four players it changes 738 greedy and 386 weighted selections (742/500 triggers, including occasions when the parent already chose Influence). It is a candidate teaching tip, not established human counterplay. The underlying automated parent still embodies trained decision weights, and no person was observed discovering, remembering or executing the condition. Opportunity cost, learning and usability remain open.

**Keep the economy and default policies.** The isolated condition supplies a concrete counterplay hypothesis for an observed human session, but its winner-credit effects and supported-count safeguards remain unqualified. Do not add another search, change, or simulation allocation in this study. No human-playtest or balanced-release claim follows.

## Integrity, verification and artifacts

All 4,608 full games completed with finite nonnegative holdings, valid Org positions/ownership, bounded trade packets and zero policy fallbacks. Rich/batch smoke outcomes and traces agree at every supported count in both backends. Tests separately confirm that observing production, resolutions and review does not change ordinary outcomes. An independent Python check reconciles all final score components, winner credit, paired identities, counts/rotations, production caps/income, review losses, recruitment/equipment counts and all twelve interval estimates.

| Backend | Players | Control forced-no-op rate | Candidate forced-no-op rate |
| --- | ---: | ---: | ---: |
| greedy | 3 | 0.007909 | 0.008102 |
| greedy | 4 | 0.006972 | 0.004720 |
| greedy | 5 | 0.004583 | 0.004097 |
| weighted | 3 | 0.020255 | 0.019097 |
| weighted | 4 | 0.019477 | 0.019396 |
| weighted | 5 | 0.016806 | 0.016319 |

All are below 0.03. Validation: **236/236 implementation tests**, `npm run check`, focused policy/telemetry checks, release verification and `git diff --check`. These checks establish implementation/evidence integrity, not balance.

Raw JSON stays local in `evidence/studies/simulation/`. The verifier source is retained as the `python` string in `2026-10-11-reputation-counter-verifier-source.json`; extract it to a temporary file and run from this game directory. It is post-run analysis, never a game input.

| Artifact | SHA-256 |
| --- | --- |
| `2026-10-11-reputation-counter-greedy-raw.json` | `a856a88621e097e9ca2419e7ba0fc0bd013c738dffdf9e97aa6f81e5be0c0a1d` |
| `2026-10-11-reputation-counter-weighted-raw.json` | `02210987439a9d92dd800384b18bea6602d7207eca50e30ded368e2347fc6cde` |
| `2026-10-11-reputation-counter-greedy-smoke-raw.json` | `efe25ac98a1f7a0ede14e75d7d1e93dff3ad52d98890ddeb6798d33ffd6061a4` |
| `2026-10-11-reputation-counter-weighted-smoke-raw.json` | `70bb939a2e0cfae78338fd2a9407c3e3ab7e00fbe933b78307b709e6ce6f102c` |
| `2026-10-11-reputation-counter-verification.json` | `52d3ef22b23192f57f6d0226942b58954bf6e65bad9a809f55ed118325698c84` |
| `2026-10-11-reputation-counter-verifier-source.json` | `8cb24cb1f4448c042688ab8ef36350651eae019a374c21a6239c4dd3d899ae1f` |

## Affected surfaces

| Surface | Delta |
| --- | --- |
| Canonical rulebook and component data | No change. |
| Machine-readable rules, scoring and prices | No change. |
| Simulator and default personas | No change; experiment-owned wrapper and read-only observers only. |
| Browser prototype | No change; no new browser acceptance claim. |
| Reference/player aids | No change; the instruction has not been human-qualified or promoted. |
| Tests | Four focused policy, allocation, uncertainty and telemetry checks. |
| Playtest/evidence documentation | This receipt, retained diagnosis and frozen protocol. |
| Release, deployment and historical evidence | No change; executable remains 0.24.3, nothing deployed. |

Boundary effects: study code reads existing public decision packets and observes the existing match lifecycle. No runtime API, content authority or physical-kit boundary changed.
