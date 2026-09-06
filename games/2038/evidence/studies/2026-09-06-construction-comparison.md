# Construction comparison and review closure

Status: implementation and calibration complete; holdout results pending. Human
play remains pending. This receipt is completed after the preregistered holdout;
it makes no balance, teachability, or enjoyment claim.

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
