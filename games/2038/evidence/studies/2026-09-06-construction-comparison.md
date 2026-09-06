# Construction comparison and review closure

Status: implementation, calibration, and the 216-game holdout are complete.
Human play remains pending. No balance, teachability, or enjoyment claim follows.

Protocol: [preregistration](2026-09-06-construction-preregistration.md).
Rules `0.11.0-rc.2-test`, executable `0.19.0`, engine `0.21.0`.

## Audited surfaces

- Canonical rulebook: Sections 6 and 8 now teach Agent assignment, completed
  immediate Headlines, local connections, and conditional emergency Scrutiny.
  Player range is two through five. Six faction trays remain choices.
- Machine-readable data: maximum five, playable counts `[2,3,4,5]`; six factions
  and all existing lore/content retained. No change to prices, action allowances,
  AGI requirements, scoring, Power connections, or faction abilities.
- Simulator: rejects six-player launches; two registered public-observation
  strategy treatments supplement the unchanged default policy. Actual
  Mega-Cluster production records nominal and cap-clipped Compute gains.
- Browser: game and Lab selectors stop at five. Shared runtime rejects invalid
  requests. No change to ordinary play decisions or presentation layout.
- Reference/player aids: regenerated from their authorities. Physical kit uses
  the current protocol, omits retired study prompts, and can freeze a clean local
  commit with explicit publication status. No change to component quantities.
- Tests: count rejection, funded construction policy and production telemetry;
  card inventory counts faction choices rather than maximum players. Archive
  regression covers auxiliary and malformed JSON. Document writes are atomic
  after a concurrent build exposed an incomplete HTML read.
- Playtest documentation: blind session procedure and notes capture reminders,
  first productive project Era, players' stated presence sacrifices, and separate
  explanations of the institutional winner and World Ending. No human session
  has been fabricated. Historical six-player records remain intact and readable.
- Lore, faction definitions, Headline effects, scoring and infrastructure costs:
  **no change**.

## Calibration and implementation validation

The preregistration records all six calibration results and the collector
correction. Targeted construction and engine checks passed (34 tests); the three
full-suite failures exposed and fixed inventory-test coupling, report listing of
auxiliary JSON, and non-atomic documentation writes. Those affected suites then
passed. Final validation passed: `npm test` (278/278), `npm run check`, and
`git diff --check`. Both executable and physical release bundles were verified.

Chrome desktop width 1440 started two players, and mobile width 390 started five.
Both displayed six faction choices and rejected a six-player runtime request;
Lab options were exactly 2, 3, 4, 5. No page errors were observed. This is browser
interaction evidence, not a physical-phone test or a human board-game session.

## Holdout identity and results

Command: `node lab/cli/construction-study.mjs holdout`.
Root seed: `2038-construction-holdout-20260906-v1`. All 216 games used the clean
source commit `ad22967b87f89213d945283382d804af05e6d238`. Engine fingerprint:
`sha256:342ab7f3ef1cf2e277f7c9cd786e2b25545130dc2315fcfdac2c7a2ce9a02399`.
Ruleset fingerprint: `sha256:b8f7d7ba3106d6a0c9fde2b0720dc6fa02e6d751ab373db1aedc9c8cc6106f4d`.

Raw index: `evidence/studies/simulation/2038-construction-holdout-20260906-v1.json`.
SHA-256: `00a0320309687fc2b26d1426be81239b72a83ef5f3f04282f9e58b8ea56ccbd1`.
The tracked [per-game results](2026-09-06-construction-results.csv) record each
report and outcome path and SHA-256. All 432 artifact hashes were rechecked.
The index retains exact options and identity metadata; the preregistration
specifies factions, seats, profiles, backends, canonical overlay, and limits.

Four-player results below refer only to the focal institution, with 24 games per
row. Wins are separate games against the same rival profiles, not direct matches
between the two deliberate plans.

| Backend | Focal plan | Mean Mandate | Win share total | Mega-Clusters | Fusion | First productive Era III / IV / none | AGI |
| --- | --- | ---: | ---: | ---: | ---: | --- | ---: |
| greedy | Retained baseline | 15.21 | 3/24 | 0 | 1 | 0 / 0 / 24 | 0 |
| greedy | Deliberate infrastructure | 25.96 | 19/24 | 24 | 18 | 24 / 0 / 0 | 16 |
| greedy | Research/Deploy | 23.21 | 19/24 | 0 | 0 | 0 / 0 / 24 | 0 |
| weighted | Retained baseline | 14.25 | 3/24 | 0 | 3 | 0 / 0 / 24 | 0 |
| weighted | Deliberate infrastructure | 19.21 | 12/24 | 15 | 9 | 9 / 6 / 9 | 4 |
| weighted | Research/Deploy | 19.46 | 15/24 | 0 | 0 | 0 / 0 / 24 | 0 |

Matched infrastructure-minus-Research/Deploy score differences were **+2.75**
with greedy selection (16 higher, 0 tied, 8 lower) and **−0.25** with weighted
selection (10 higher, 2 tied, 12 lower). Deliberate infrastructure received 125
actual project Compute in the greedy games and 67 in the weighted games, after
resource caps. It produced 39 Mega-Clusters across the 48 games; 33 first produced
in Era III, six in Era IV, and nine games had no productive project. Fusion was
built 27 times. The retained baseline built no Mega-Clusters and four Fusion.

All 144 four-player games reached four Production snapshots. At each of two,
three, and five players, all 24 additional games completed too (six factions ×
two backends × two deliberate plans). These guards do not balance focal seats
or every faction-omission combination. Two-player evidence remains exploratory.

## Interpretation and remaining human evidence

The earlier zero-project result did not establish that ordinary play cannot
afford advanced construction. A policy that budgets the sequence can build it
and receive production before the ending. Its score advantage was not consistent
across the two backends. Both deliberate plans were strong against the retained
rival profiles, which limits any claim about relative human strategy strength.
The Research/Deploy plan intentionally builds only one Facility, so its zero AGI
recognitions follow partly from that plan's missing second host; they do not prove
that all Research/Deploy approaches must forgo AGI.

The study changes no prices, AGI thresholds, scoring, or selection allowances.
It cannot tell whether people find the investment attractive, knowingly preserve
presence at an immediate cost, need fewer reminders, or feel the ending is earned.
Those are the registered blind-teach questions. No further cuts or incentive
changes were selected.

The current local teaching kit contains the four authoritative documents,
component masters, the world companion, and the current observer protocol.
Session creation remains pending actual participants. No completed human receipt
or measured learning/enjoyment score exists.

## Final wording-only follow-up

Executable `0.19.1`, rules `0.11.0-rc.3-test`, engine `0.21.0` print the full
two-through-five player range on the Core Rules cover beside the suggested
three-through-five range. The first kit check caught the omitted full range.
No mechanics or policy changed. The study above remains attributed to `0.19.0`;
its immutable release is preserved. The final kit uses the follow-up wording.

Final follow-up validation: `npm run check`, generated documentation/build checks, and the contract/content/engine test subset passed. Ruleset, mechanics, and engine fingerprints exactly match the studied release, so no repeated strategy run was needed. The 278-test full suite passed before this wording-only delta.
