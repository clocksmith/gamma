import assert from "node:assert/strict";
import test from "node:test";
import {
  createSimulation,
  factionRosterForRun,
} from "../lab/runtime/create-simulation.js";
import {
  normalizeSimulationReport,
  CURRENT_REPORT_SCHEMA_VERSION,
} from "../lab/contracts/report-migrations.js";
import { fixture, profiles, factions } from "./helpers/smaller-game.mjs";
import { WeightedPlayerPolicy } from "../lab/policies/weighted-policy.js";
import { validateDecisionPacket } from "../lab/contracts/decision-contract.js";
import {
  loadPlayerProfiles,
  profileForPrompt,
} from "../lab/personas/player-profile.js";
import {
  createLaunchIdentity,
  loadGameIdentity,
} from "../lab/versioning/game-identity.js";
const opts = {
  runs: 3,
  playerCount: 4,
  seed: "smaller-pipeline",
  sampleReplays: 1,
  archive: false,
};
test("reusable personas retain validated identities, resources, and action weights", async () => {
  for (const p of await loadPlayerProfiles()) {
    const v = profileForPrompt(p);
    assert.equal(v.id, p.id);
    assert.ok(v.persona.worldview);
    assert.ok(v.resourceValues.compute > 0);
    assert.equal(Object.keys(p.strategy.actionWeights).length, 6);
  }
});
test("Monte Carlo executes current game and records current report/replay identity", async () => {
  const r = await createSimulation(opts);
  assert.equal(r.schemaVersion, 8);
  assert.equal(r.reportSchemaVersion, 8);
  assert.equal(r.replaySchemaVersion, 4);
  assert.equal(r.scope.id, "shared-hex-orgs-v1");
  assert.equal(r.runs, 3);
  assert.ok(r.samples.length);
  assert.ok(r.diagnostics);
  for (const s of r.samples)
    for (const p of s.standings) assert.ok(Number.isFinite(p.score));
});
test("rich and batch runs retain identical mechanics and score summaries", async () => {
  const a = await createSimulation({ ...opts, projection: "rich" }),
    b = await createSimulation({ ...opts, projection: "batch" });
  assert.deepEqual(a.factions, b.factions);
  assert.deepEqual(a.seats, b.seats);
  assert.deepEqual(a.diagnostics, b.diagnostics);
});
test("faction rotation remains independent of equipment and has no duplicate seats", () => {
  for (let n = 0; n < 24; n++) {
    const r = factionRosterForRun(factions.factions, 4, n);
    assert.equal(new Set(r.map((f) => f.id)).size, 4);
  }
  assert.equal(
    new Set(
      Array.from({ length: 6 }, (_, n) =>
        factionRosterForRun(factions.factions, 4, n),
      )
        .flat()
        .map((f) => f.id),
    ).size,
    6,
  );
});
test("invalid player counts and metered providers fail before running", async () => {
  await assert.rejects(
    createSimulation({ ...opts, playerCount: 6 }),
    /playerCount/,
  );
  await assert.rejects(
    createSimulation({ ...opts, backends: ["claude"] }),
    /allowLlm|authorization|explicit/i,
  );
});
test("cancelled run emits no provider call", async () => {
  const c = new AbortController();
  c.abort();
  await assert.rejects(
    createSimulation({ ...opts, signal: c.signal }),
    /abort/i,
  );
});
test("frozen launch identity rejects changed numerical or strategic sources", async () => {
  const id = createLaunchIdentity(await loadGameIdentity());
  await assert.rejects(
    createSimulation({
      ...opts,
      launchIdentity: {
        ...id,
        engine: { ...id.engine, fingerprint: "changed" },
      },
    }),
    /identity|fingerprint/i,
  );
});
test("decision packets reveal public Org positions, not the hidden deck", () => {
  const m = fixture();
  m.players[1].selectedAction = "research";
  const p = m.packet(0, "select", m.legalActionSelections(0));
  validateDecisionPacket(p);
  assert.equal(p.observation.opponents[0].selectedAction, undefined);
  assert.equal(p.observation.trainingDrawPile, undefined);
  assert.equal(p.observation.self.kitId, m.players[0].kitId);
  assert.equal(p.observation.board.length, 18);
});
test("weighted decisions are deterministic on equivalent legal packets", async () => {
  const m = fixture();
  const p = m.packet(0, "select", m.legalActionSelections(0));
  const w = new WeightedPlayerPolicy(profiles[0]);
  assert.deepEqual(await w.decide(p), await w.decide(p));
});
test("historical report envelopes preserve old Trust/objectives and never rescore", async () => {
  const r = await createSimulation(opts);
  const old = {
    ...structuredClone(r),
    schemaVersion: 7,
    reportSchemaVersion: 7,
    replaySchemaVersion: 3,
    standings: [
      { seat: 0, score: 29, trust: 4, objectiveRecord: { value: 3 } },
    ],
  };
  const before = structuredClone(old);
  const display = normalizeSimulationReport(old);
  assert.equal(display.schemaVersion, CURRENT_REPORT_SCHEMA_VERSION);
  assert.equal(display.replaySchemaVersion, 3);
  assert.deepEqual(display.standings, old.standings);
  assert.deepEqual(old, before);
  assert.equal(
    display.migration.attribution,
    "historical_objectives_preserved",
  );
});
