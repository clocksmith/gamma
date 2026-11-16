import { readFile, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { resolve } from "node:path";
import assert from "node:assert/strict";
import { createSimulation } from "../../../lab/runtime/create-simulation.js";
import { archiveSimulationReport } from "../../../lab/report-archive.js";
import { projectRoot } from "../../../lab/versioning/game-identity.js";

const registrationPath =
  "evidence/studies/simulation/2026-10-09-smaller-prototype-preregistration.json";
const preregistration = JSON.parse(
  await readFile(resolve(projectRoot, registrationPath), "utf8"),
);
const objectiveCards = JSON.parse(
  await readFile(resolve(projectRoot, "dist/runtime/mandates.json"), "utf8"),
).mandates;
const summaries = [];
for (const playerCount of preregistration.playerCounts) {
  const { report, outcomes } = await createSimulation({
    runs: preregistration.runsPerPlayerCount,
    playerCount,
    seed: preregistration.seed,
    projection: preregistration.projection,
    backends: Array(playerCount).fill(preregistration.backends),
    returnOutcomes: true,
    sampleReplays: 1,
    rulesVariant: preregistration.rulesVariant,
    reportType: "smaller-prototype-implementation-diagnostic",
    preRegistration: preregistration,
  });
  assert.equal(outcomes.length, preregistration.runsPerPlayerCount);
  const objectives = Object.fromEntries(
    objectiveCards.map((c) => [
      c.id,
      {
        revealed: 0,
        eligiblePlayers: 0,
        points: 0,
        tiedAwards: 0,
        noQualifiers: 0,
      },
    ]),
  );
  const scores = [];
  const negotiation = { offers: 0, accepted: 0, refused: 0, activeVentures: 0 };
  for (const { outcome: result } of outcomes) {
    for (const key of ["offers", "accepted", "refused"])
      negotiation[key] += result.matchMetrics.trades[key];
    negotiation.activeVentures += result.matchMetrics.activeVentures;
    assert.equal(result.matchMetrics.productionSnapshots.length, 4);
    assert.equal(result.matchMetrics.eraMandateScores.length, 4);
    assert.equal(result.matchMetrics.agiFunnel.length, playerCount);
    for (const player of result.standings) {
      assert.equal(
        Object.values(player.metrics.actions).reduce((n, v) => n + v, 0),
        12,
      );
      assert.ok(Number.isFinite(player.score));
      scores.push(player.score);
    }
    for (const card of result.matchMetrics.eraMandateScores) {
      const row = objectives[card.id];
      row.revealed++;
      row.eligiblePlayers += card.standings.filter((p) => p.qualified).length;
      row.points += card.standings.reduce((n, p) => n + p.points, 0);
      row.tiedAwards += Number(
        card.standings.filter((p) => p.points > 0).length > 1,
      );
      row.noQualifiers += Number(!card.standings.some((p) => p.qualified));
    }
  }
  const raw = {
    ...report,
    studyOutcomes: outcomes,
    studyObjectives: objectives,
  };
  const archive = await archiveSimulationReport(raw, {
    projectRoot,
    jobId: preregistration.id,
  });
  const bytes = await readFile(resolve(projectRoot, archive.relativePath));
  summaries.push({
    playerCount,
    runs: outcomes.length,
    configuration: report.configuration,
    source: report.provenance,
    game: report.game,
    engine: {
      id: report.engine.id,
      version: report.engine.version,
      coverageId: report.engine.coverageId,
      fingerprint: report.engine.fingerprint,
    },
    archive: archive.relativePath,
    sha256: createHash("sha256").update(bytes).digest("hex"),
    scoreRange: [Math.min(...scores), Math.max(...scores)],
    negotiation,
    diagnostics: report.diagnostics,
    agiFunnel: report.matchMetrics.agiFunnel,
    objectives,
  });
  process.stdout.write(
    `${playerCount} players: ${outcomes.length} completed games; ${archive.relativePath}\n`,
  );
}
const receipt = {
  schemaVersion: 1,
  generatedAt: new Date().toISOString(),
  preregistration: registrationPath,
  command:
    "node evidence/studies/simulation/2026-10-09-smaller-prototype-study.mjs",
  runnerSha256: createHash("sha256")
    .update(await readFile(new URL(import.meta.url)))
    .digest("hex"),
  evidenceLabel: "simulation",
  status: "completed",
  balancePromotion: false,
  summaries,
  limits: preregistration.limits,
  changesMotivatedByResults: [],
  surfaceAudit: {
    rules:
      "No change from diagnostic results; user-selected redesign implemented.",
    components:
      "No change from diagnostic results; four tracks, six areas and card supplies implemented.",
    simulator:
      "No change from diagnostic results; shared smaller-game engine implemented.",
    browser:
      "No change from diagnostic results; six-area UI and independent kits implemented.",
    referenceAids:
      "No change from diagnostic results; generated from current component records.",
    physicalAndPlaytesting:
      "No change from diagnostic results; new kit generated; blind session still required.",
  },
};
await writeFile(
  resolve(
    projectRoot,
    "evidence/studies/simulation/2026-10-09-smaller-prototype-result.json",
  ),
  JSON.stringify(receipt, null, 2) + "\n",
);
